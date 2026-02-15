"""
Content analyzer service using LLM for article scoring and ranking.

Analyzes articles on multiple dimensions and ranks them for video generation.
"""

import json
import logging
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import Article
from app.schemas import ArticleScores
from app.services.base_provider import BaseLLMProvider
from app.services.provider_factory import ProviderFactory, LLMProvider
from app.utils.llm_helpers import parse_llm_json
from app.prompts import build_article_analysis_prompt

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """LLM-powered content analyzer for article scoring and ranking."""
    
    # Weighting for final score calculation
    RELEVANCE_WEIGHT = 0.3
    ENGAGEMENT_WEIGHT = 0.4  # Highest weight - engagement is key for Shorts
    RECENCY_WEIGHT = 0.2
    UNIQUENESS_WEIGHT = 0.1
    
    def __init__(
        self,
        db: Session,
        llm_provider: Optional[BaseLLMProvider] = None
    ):
        """
        Initialize content analyzer.
        
        Args:
            db: Database session
            llm_provider: Optional LLM provider (defaults to Gemini)
        """
        self.db = db
        self.llm = llm_provider or ProviderFactory.create_llm_provider(
            provider=LLMProvider.GEMINI
        )
    
    async def analyze_article(self, article: Article) -> Optional[ArticleScores]:
        """
        Analyze a single article using LLM.
        
        Args:
            article: Article model instance
            
        Returns:
            ArticleScores with LLM analysis, or None if analysis failed
        """
        try:
            logger.info(f"Analyzing article: {article.title}")
            
            # Build prompt
            content_preview = (article.content or article.description or "")[:500]
            published_str = article.published_at.isoformat() if article.published_at else "Unknown"
            source_name = article.feed.name if article.feed else "Unknown"
            
            prompt = build_article_analysis_prompt(
                title=article.title,
                description=article.description or "",
                content_preview=content_preview,
                published_at=published_str,
                source=source_name
            )
            
            # Get LLM response - use JSON mode without response_schema to avoid malformed output
            response_text = await self.llm.generate_text(
                prompt=prompt,
                temperature=0.3,
                max_tokens=8192,
                response_mime_type="application/json"
            )
            
            # Validate and create ArticleScores
            # First try to clean the response (handles markdown code blocks from Gemini)
            parsed_data = parse_llm_json(response_text)
            
            if parsed_data:
                try:
                    scores = ArticleScores.model_validate(parsed_data)
                except Exception as e:
                    logger.warning(f"Pydantic validation failed after parsing: {e}")
                    # Fallback: try direct JSON validation
                    try:
                        scores = ArticleScores.model_validate_json(response_text)
                    except Exception as e2:
                        logger.error(f"Failed to parse LLM response for article {article.id}: {e2}")
                        logger.debug(f"Raw response (first 500 chars): {response_text[:500]}...")
                        return None
            else:
                # Direct JSON validation as fallback
                try:
                    scores = ArticleScores.model_validate_json(response_text)
                except Exception as e:
                    logger.error(f"Failed to parse LLM response for article {article.id}: {e}")
                    logger.debug(f"Raw response (first 500 chars): {response_text[:500]}...")
                    return None
            
            logger.info(f"Article analyzed - Final score: {self._calculate_final_score(scores):.2f}")
            return scores
            
        except Exception as e:
            logger.error(f"Error analyzing article {article.id}: {str(e)}")
            return None
    
    async def batch_analyze(
        self,
        articles: List[Article],
        batch_size: int = 10
    ) -> List[Article]:
        """
        Analyze multiple articles in batches.
        
        Args:
            articles: List of Article instances
            batch_size: Number of articles to process in parallel
            
        Returns:
            List of articles with scores updated
        """
        logger.info(f"Batch analyzing {len(articles)} articles")
        
        analyzed_articles = []
        
        # Process in batches
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            
            for article in batch:
                scores = await self.analyze_article(article)
                
                if scores:
                    # Update article with scores
                    article.relevance_score = scores.relevance_score
                    article.engagement_score = scores.engagement_score
                    article.recency_score = scores.recency_score
                    article.uniqueness_score = scores.uniqueness_score
                    article.category = scores.category
                    article.key_topics = scores.key_topics
                    article.why_interesting = scores.why_interesting
                    article.final_score = self._calculate_final_score(scores)
                    article.analyzed_at = datetime.now(timezone.utc)
                    
                    analyzed_articles.append(article)
            
            # Commit batch
            self.db.commit()
            logger.info(f"Committed batch {i // batch_size + 1}")
        
        logger.info(f"Successfully analyzed {len(analyzed_articles)} articles")
        return analyzed_articles
    
    def rank_articles(
        self,
        articles: Optional[List[Article]] = None,
        limit: Optional[int] = None,
        min_score: Optional[float] = None
    ) -> List[Article]:
        """
        Get ranked articles by final score.
        
        Args:
            articles: Optional list to rank (defaults to all analyzed articles)
            limit: Optional limit on number of results
            min_score: Optional minimum score filter
            
        Returns:
            List of articles sorted by final_score descending
        """
        if articles is None:
            # Query all analyzed articles
            query = self.db.query(Article).filter(
                Article.final_score.isnot(None)
            )
            
            if min_score is not None:
                query = query.filter(Article.final_score >= min_score)
            
            articles = query.order_by(Article.final_score.desc()).all()
        else:
            # Sort provided list
            articles = sorted(
                [a for a in articles if a.final_score is not None],
                key=lambda x: x.final_score,
                reverse=True
            )
        
        if limit:
            articles = articles[:limit]
        
        return articles
    
    def get_top_articles(
        self,
        limit: int = 5,
        days: int = 7,
        min_score: Optional[float] = None
    ) -> List[Article]:
        """
        Get top-ranked articles from recent days.
        
        Args:
            limit: Number of articles to return
            days: Look back this many days
            min_score: Optional minimum score threshold
            
        Returns:
            Top articles sorted by final_score
        """
        from datetime import timedelta
        
        since = datetime.now(timezone.utc) - timedelta(days=days)
        
        query = self.db.query(Article).filter(
            Article.final_score.isnot(None),
            Article.created_at >= since
        )
        
        if min_score is not None:
            query = query.filter(Article.final_score >= min_score)
        
        articles = query.order_by(Article.final_score.desc()).limit(limit).all()
        
        return articles
    
    def _calculate_final_score(self, scores: ArticleScores) -> float:
        """
        Calculate weighted final score from individual scores.
        
        Args:
            scores: ArticleScores instance
            
        Returns:
            Weighted final score (0-10)
        """
        final = (
            scores.relevance_score * self.RELEVANCE_WEIGHT +
            scores.engagement_score * self.ENGAGEMENT_WEIGHT +
            scores.recency_score * self.RECENCY_WEIGHT +
            scores.uniqueness_score * self.UNIQUENESS_WEIGHT
        )
        return round(final, 2)
    
    # _parse_llm_response removed — now using shared parse_llm_json from app.utils
