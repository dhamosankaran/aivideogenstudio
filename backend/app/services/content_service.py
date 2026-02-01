"""
Content curation service for AIVideoGen.

Handles article listing, filtering, selection, and script generation triggering.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime, timedelta
import logging
from app.models import Article, Script, Feed
from app.services.script_service import ScriptService

logger = logging.getLogger(__name__)


class ContentService:
    """Service for content curation operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.script_service = ScriptService(db)
    
    def list_articles(
        self,
        source: Optional[str] = None,
        date_range: Optional[str] = "last_7_days",
        content_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        List articles with filters and pagination.
        
        Args:
            source: Filter by feed name
            date_range: last_7_days, last_30_days, all
            content_type: Filter by suggested_content_type
            status: unprocessed, has_script, has_video
            search: Search in title and description
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            Dict with items, total, page, page_size, total_pages
        """
        query = self.db.query(Article)
        
        # Filter by source (feed name)
        if source:
            query = query.join(Feed).filter(Feed.name == source)
        
        # Filter by date range
        if date_range and date_range != "all":
            cutoff = self._parse_date_range(date_range)
            if cutoff:
                query = query.filter(Article.published_at >= cutoff)
        
        # Filter by content type
        if content_type:
            query = query.filter(Article.suggested_content_type == content_type)
        
        # Filter by status
        if status:
            if status == "unprocessed":
                query = query.filter(Article.is_processed == False)
            elif status == "has_script":
                query = query.filter(Article.is_processed == True)
            elif status == "has_video":
                # Has script with completed video
                query = query.join(Script).filter(
                    Script.status == "approved"
                )
        
        # Search in title and description
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Article.title.ilike(search_term),
                    Article.description.ilike(search_term)
                )
            )
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination and ordering
        items = query.order_by(Article.published_at.desc()) \
                    .offset((page - 1) * page_size) \
                    .limit(page_size) \
                    .all()
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    def get_article(self, article_id: int) -> Optional[Article]:
        """Get article by ID with full details."""
        return self.db.query(Article).filter(Article.id == article_id).first()
    
    def select_articles(self, article_ids: List[int]) -> Dict[str, Any]:
        """
        Mark articles as selected for script generation.
        
        Args:
            article_ids: List of article IDs to select
            
        Returns:
            Dict with selected count
        """
        articles = self.db.query(Article).filter(Article.id.in_(article_ids)).all()
        
        for article in articles:
            article.is_selected = True
            article.selected_at = datetime.utcnow()
        
        self.db.commit()
        
        return {"selected": len(articles), "article_ids": article_ids}

    def delete_articles(self, article_ids: List[int]) -> Dict[str, int]:
        """
        Delete specific articles by ID.
        
        Args:
            article_ids: List of article IDs to delete
            
        Returns:
            Dict with delete count
        """
        # Delete related scripts first (if cascade is not configured)
        # But assuming cascade is handled or we just want to delete the articles
        # Ideally, we should check for relationships. 
        # For MVP, we will attempt delete.
        
        # Using synchronize_session=False for performance on bulk delete
        deleted_count = self.db.query(Article).filter(Article.id.in_(article_ids)).delete(synchronize_session=False)
        
        self.db.commit()
        
        return {"deleted": deleted_count}
    
    async def generate_scripts(
        self,
        article_ids: List[int],
        content_type: Optional[str] = "daily_update"
    ) -> Dict[str, Any]:
        """
        Generate scripts from selected articles with auto-analysis.
        
        Args:
            article_ids: List of article IDs to generate scripts from
            content_type: Content type for script generation
            
        Returns:
            Dict with created script IDs and count
        """
        from app.services.content_analyzer import ContentAnalyzer
        
        articles = self.db.query(Article).filter(Article.id.in_(article_ids)).all()
        script_ids = []
        errors = []
        analyzed_count = 0
        
        # Initialize content analyzer for auto-analysis
        analyzer = ContentAnalyzer(self.db)
        
        for article in articles:
            try:
                # Check if article is from YouTube (has youtube_source_id)
                # YouTube articles already have scores from insight, skip LLM analysis
                is_youtube_article = article.youtube_source_id is not None
                
                # Check if article needs analysis (has key_topics and why_interesting)
                needs_analysis = not article.key_topics or not article.why_interesting
                
                if is_youtube_article and needs_analysis:
                    # For YouTube articles, populate from description/summary instead of LLM analysis
                    logger.info(f"Auto-populating YouTube article {article.id} fields from insight data")
                    article.key_topics = article.key_points if article.key_points else ["YouTube Insight"]
                    article.why_interesting = article.summary or article.description or "Key insight from YouTube video"
                    article.category = "youtube_insight"
                    article.analyzed_at = datetime.utcnow()
                    analyzed_count += 1
                    logger.info(f"YouTube article {article.id} populated from insight data")
                elif needs_analysis:
                    logger.info(f"Auto-analyzing article {article.id}: {article.title}")
                    try:
                        # Analyze article first
                        scores = await analyzer.analyze_article(article)
                        if scores:
                            # Update article with analysis
                            article.relevance_score = scores.relevance_score
                            article.engagement_score = scores.engagement_score
                            article.recency_score = scores.recency_score
                            article.uniqueness_score = scores.uniqueness_score
                            article.category = scores.category
                            article.key_topics = scores.key_topics
                            article.why_interesting = scores.why_interesting
                            article.final_score = analyzer._calculate_final_score(scores)
                            article.analyzed_at = datetime.utcnow()
                            analyzed_count += 1
                            logger.info(f"Article {article.id} analyzed successfully")
                        else:
                            raise ValueError("Analysis failed - no scores returned")
                    except Exception as analysis_error:
                        error_msg = f"Failed to analyze article '{article.title[:50]}...': {str(analysis_error)}"
                        logger.error(error_msg)
                        errors.append({
                            "article_id": article.id,
                            "article_title": article.title[:100],
                            "error": error_msg,
                            "error_type": "analysis_failed"
                        })
                        continue
                
                # Generate script using script service
                script = await self.script_service.generate_script(
                    article=article,
                    style="engaging"
                )
                
                # Update article status
                article.is_processed = True
                article.is_selected = True
                article.selected_at = datetime.utcnow()
                
                # Update script with content type
                script.content_type = content_type
                
                script_ids.append(script.id)
                logger.info(f"Script generated for article {article.id}")
                
            except ValueError as e:
                # Specific validation errors
                error_msg = str(e)
                errors.append({
                    "article_id": article.id,
                    "article_title": article.title[:100],
                    "error": error_msg,
                    "error_type": "validation_error"
                })
                logger.error(f"Validation error for article {article.id}: {error_msg}")
            except Exception as e:
                # Generic errors with more context
                error_msg = f"Failed to generate script for '{article.title[:50]}...': {str(e)}"
                errors.append({
                    "article_id": article.id,
                    "article_title": article.title[:100],
                    "error": error_msg,
                    "error_type": "generation_failed"
                })
                logger.error(f"Script generation error for article {article.id}: {str(e)}")
        
        self.db.commit()
        
        return {
            "scripts_created": len(script_ids),
            "script_ids": script_ids,
            "analyzed_count": analyzed_count,
            "errors": errors
        }
    
    def analyze_article(self, article_id: int) -> Dict[str, Any]:
        """
        Analyze article and generate AI insights.
        
        Uses LLM to:
        - Calculate relevance score (0-10)
        - Suggest content type
        - Extract key points
        - Generate tags
        
        Args:
            article_id: Article ID to analyze
            
        Returns:
            Dict with analysis results
        """
        article = self.get_article(article_id)
        if not article:
            raise ValueError(f"Article {article_id} not found")
        
        # Use LLM to analyze (simplified for now)
        # In production, this would call the LLM service
        analysis = {
            "score": article.final_score or 7.0,  # Use existing score or default
            "content_type": article.suggested_content_type or "daily_update",
            "key_points": article.key_points or [],
            "tags": article.key_topics or []
        }
        
        # Update article with analysis
        article.relevance_score = analysis["score"]
        article.suggested_content_type = analysis["content_type"]
        article.analyzed_at = datetime.utcnow()
        
        self.db.commit()
        
        return analysis
    
    def get_sources(self) -> List[str]:
        """Get list of all feed sources."""
        feeds = self.db.query(Feed.name).distinct().all()
        return [feed[0] for feed in feeds]
    
    def get_content_types(self) -> List[str]:
        """Get list of available content types."""
        return [
            "daily_update",
            "big_tech",
            "leader_quote",
            "arxiv_paper"
        ]
    
    def _parse_date_range(self, date_range: str) -> Optional[datetime]:
        """Parse date range string to datetime."""
        from datetime import timedelta
        
        now = datetime.utcnow()
        
        if date_range == "yesterday":
            return now - timedelta(days=1)
        elif date_range == "today":
            return now - timedelta(hours=24)
        elif date_range == "last_7_days":
            return now - timedelta(days=7)
        elif date_range == "last_30_days":
            return now - timedelta(days=30)
        elif date_range == "last_90_days":
            return now - timedelta(days=90)
        else:  # "all" or unknown
            return None
