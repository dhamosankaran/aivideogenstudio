"""
NewsAPI service for fetching real-time news articles.

Provides comprehensive news coverage from 80,000+ sources worldwide.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Article, Feed
from app.database import get_db

logger = logging.getLogger(__name__)


class NewsAPIService:
    """Service for fetching articles from NewsAPI.org"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize NewsAPI service.
        
        Args:
            api_key: NewsAPI key (defaults to settings)
        """
        self.api_key = api_key or settings.newsapi_key
        if not self.api_key:
            raise ValueError("NewsAPI key not configured")
        
        self.client = NewsApiClient(api_key=self.api_key)
    
    def search_articles(
        self,
        query: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        language: str = "en",
        sort_by: str = "publishedAt",
        page_size: int = 20,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Search for articles using NewsAPI.
        
        Args:
            query: Search query (e.g., "Davos", "AI AND regulation")
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            language: Language code (default: en)
            sort_by: Sort by (publishedAt, relevancy, popularity)
            page_size: Results per page (max 100)
            page: Page number
            
        Returns:
            Dict with articles, total results, status
        """
        try:
            # Default to last 7 days if no date specified
            if not from_date:
                from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
            
            logger.info(f"Searching NewsAPI: query='{query}', from={from_date}, to={to_date}")
            
            response = self.client.get_everything(
                q=query,
                from_param=from_date,
                to=to_date,
                language=language,
                sort_by=sort_by,
                page_size=page_size,
                page=page
            )
            
            logger.info(f"NewsAPI returned {response.get('totalResults', 0)} results")
            
            return {
                "status": response.get("status"),
                "total_results": response.get("totalResults", 0),
                "articles": response.get("articles", []),
                "page": page,
                "page_size": page_size
            }
            
        except Exception as e:
            logger.error(f"NewsAPI search error: {str(e)}")
            raise
    
    def get_top_headlines(
        self,
        category: Optional[str] = None,
        country: str = "us",
        page_size: int = 20,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Get top headlines from NewsAPI.
        
        Args:
            category: Category (business, technology, etc.)
            country: Country code (us, gb, etc.)
            page_size: Results per page
            page: Page number
            
        Returns:
            Dict with articles and metadata
        """
        try:
            logger.info(f"Fetching top headlines: category={category}, country={country}")
            
            response = self.client.get_top_headlines(
                category=category,
                country=country,
                page_size=page_size,
                page=page
            )
            
            return {
                "status": response.get("status"),
                "total_results": response.get("totalResults", 0),
                "articles": response.get("articles", []),
                "page": page,
                "page_size": page_size
            }
            
        except Exception as e:
            logger.error(f"NewsAPI top headlines error: {str(e)}")
            raise
    
    def import_articles_to_db(
        self,
        articles: List[Dict[str, Any]],
        db: Session,
        source_name: str = "NewsAPI"
    ) -> Dict[str, Any]:
        """
        Import NewsAPI articles to database.
        
        Args:
            articles: List of article dicts from NewsAPI
            db: Database session
            source_name: Name for the feed source
            
        Returns:
            Dict with import statistics
        """
        try:
            # Get or create NewsAPI feed
            feed = db.query(Feed).filter(Feed.name == source_name).first()
            if not feed:
                feed = Feed(
                    name=source_name,
                    url="https://newsapi.org",
                    category="news_api",
                    is_active=True
                )
                db.add(feed)
                db.commit()
                db.refresh(feed)
            
            imported = 0
            duplicates = 0
            errors = 0
            
            for article_data in articles:
                try:
                    # Check for duplicates by URL
                    url = article_data.get("url")
                    if not url:
                        errors += 1
                        continue
                    
                    existing = db.query(Article).filter(Article.url == url).first()
                    if existing:
                        duplicates += 1
                        continue
                    
                    # Parse published date
                    published_at = None
                    if article_data.get("publishedAt"):
                        try:
                            published_at = datetime.fromisoformat(
                                article_data["publishedAt"].replace("Z", "+00:00")
                            )
                        except:
                            published_at = datetime.utcnow()
                    
                    # Create article
                    article = Article(
                        feed_id=feed.id,
                        title=article_data.get("title", "")[:500],
                        description=article_data.get("description", "")[:1000],
                        url=url,
                        content=article_data.get("content", ""),
                        author=article_data.get("author", ""),
                        published_at=published_at or datetime.utcnow(),
                        is_processed=False
                    )
                    
                    db.add(article)
                    imported += 1
                    
                except Exception as e:
                    logger.error(f"Error importing article: {str(e)}")
                    errors += 1
                    continue
            
            db.commit()
            
            logger.info(f"Import complete: {imported} imported, {duplicates} duplicates, {errors} errors")
            
            return {
                "imported": imported,
                "duplicates": duplicates,
                "errors": errors,
                "total_processed": len(articles)
            }
            
        except Exception as e:
            logger.error(f"Import error: {str(e)}")
            db.rollback()
            raise
    
    def get_sources(self, category: Optional[str] = None, language: str = "en") -> List[Dict[str, Any]]:
        """
        Get available news sources from NewsAPI.
        
        Args:
            category: Filter by category
            language: Filter by language
            
        Returns:
            List of source dicts
        """
        try:
            response = self.client.get_sources(
                category=category,
                language=language
            )
            
            return response.get("sources", [])
            
        except Exception as e:
            logger.error(f"Error fetching sources: {str(e)}")
            raise
