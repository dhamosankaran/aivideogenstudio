"""
RSS feed service for ingesting articles from multiple sources.

Handles feed parsing, article extraction, and deduplication.
"""

import feedparser
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import Feed, Article
import logging

logger = logging.getLogger(__name__)


class FeedService:
    """Service for managing RSS feeds and article ingestion."""
    
    def __init__(self, db: Session):
        """Initialize feed service with database session."""
        self.db = db
    
    async def fetch_feed(self, feed: Feed) -> List[Article]:
        """
        Fetch and parse a single RSS feed.
        
        Args:
            feed: Feed model instance
            
        Returns:
            List of new Article instances (not yet committed)
        """
        try:
            logger.info(f"Fetching feed: {feed.name} ({feed.url})")
            
            # Parse RSS feed
            parsed = feedparser.parse(str(feed.url))
            
            if parsed.bozo:  # Feed parsing error
                logger.warning(f"Feed parse error for {feed.name}: {parsed.bozo_exception}")
            
            new_articles = []
            
            for entry in parsed.entries:
                # Check if article already exists (by URL)
                existing = self.db.query(Article).filter(
                    Article.url == entry.link
                ).first()
                
                if existing:
                    logger.debug(f"Skipping duplicate: {entry.link}")
                    continue
                
                # Create new article
                article = self._parse_feed_entry(entry, feed)
                new_articles.append(article)
            
            logger.info(f"Found {len(new_articles)} new articles from {feed.name}")
            return new_articles
            
        except Exception as e:
            logger.error(f"Error fetching feed {feed.name}: {str(e)}")
            return []
    
    async def fetch_all_feeds(self) -> List[Article]:
        """
        Fetch all active feeds and return new articles.
        
        Returns:
            List of new Article instances (not yet committed)
        """
        # Get all active feeds
        feeds = self.db.query(Feed).filter(Feed.is_active == True).all()
        
        logger.info(f"Fetching {len(feeds)} active feeds")
        
        all_new_articles = []
        
        for feed in feeds:
            articles = await self.fetch_feed(feed)
            all_new_articles.extend(articles)
        
        return all_new_articles
    
    async def sync_feeds(self) -> int:
        """
        Sync all active feeds and save new articles to database.
        
        Returns:
            Count of new articles saved
        """
        new_articles = await self.fetch_all_feeds()
        
        # Save to database
        for article in new_articles:
            self.db.add(article)
        
        self.db.commit()
        
        logger.info(f"Synced {len(new_articles)} new articles")
        return len(new_articles)

    async def sync_single_feed(self, feed_id: int) -> int:
        """
        Sync a single feed and save new articles to database.
        
        Args:
            feed_id: ID of the feed to sync
            
        Returns:
            Count of new articles saved
        """
        # Get the specific feed
        feed = self.db.query(Feed).filter(Feed.id == feed_id).first()
        if not feed:
            return 0
        
        # Fetch articles from this feed only
        new_articles = await self.fetch_feed(feed)
        
        # Save to database
        for article in new_articles:
            self.db.add(article)
        
        self.db.commit()
        
        logger.info(f"Synced {len(new_articles)} new articles from feed {feed_id}")
        return len(new_articles)
    
    def _parse_feed_entry(self, entry, feed: Feed) -> Article:
        """
        Parse a single feed entry into an Article model.
        
        Args:
            entry: feedparser entry object
            feed: Feed model instance
            
        Returns:
            Article instance
        """
        # Extract published date
        published_at = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6])
            except:
                pass
        
        # Extract content (try different fields)
        content = None
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value
        elif hasattr(entry, 'summary'):
            content = entry.summary
        elif hasattr(entry, 'description'):
            content = entry.description
        
        # Extract description
        description = None
        if hasattr(entry, 'summary'):
            description = entry.summary
        elif hasattr(entry, 'description'):
            description = entry.description
        
        # Extract author
        author = None
        if hasattr(entry, 'author'):
            author = entry.author
        elif hasattr(entry, 'authors') and entry.authors:
            author = entry.authors[0].get('name')
        
        return Article(
            feed_id=feed.id,
            title=entry.title,
            url=entry.link,
            author=author,
            published_at=published_at,
            description=description,
            content=content,
            is_processed=False,
            is_selected=False
        )
    
    def add_feed(self, name: str, url: str, category: Optional[str] = None) -> Feed:
        """
        Add a new RSS feed.
        
        Args:
            name: Feed display name
            url: Feed URL
            category: Optional category tag
            
        Returns:
            Created Feed instance
        """
        feed = Feed(
            name=name,
            url=url,
            category=category,
            is_active=True
        )
        
        self.db.add(feed)
        self.db.commit()
        self.db.refresh(feed)
        
        logger.info(f"Added new feed: {name}")
        return feed
    
    def get_feeds(self, active_only: bool = False) -> List[Feed]:
        """Get all feeds, optionally filtered by active status."""
        query = self.db.query(Feed)
        if active_only:
            query = query.filter(Feed.is_active == True)
        return query.all()
    
    def update_feed(self, feed_id: int, **kwargs) -> Optional[Feed]:
        """Update a feed's properties."""
        feed = self.db.query(Feed).filter(Feed.id == feed_id).first()
        if not feed:
            return None
        
        for key, value in kwargs.items():
            if hasattr(feed, key):
                setattr(feed, key, value)
        
        self.db.commit()
        self.db.refresh(feed)
        
        logger.info(f"Updated feed: {feed.name}")
        return feed
    
    def delete_feed(self, feed_id: int) -> bool:
        """Delete a feed and all its articles."""
        feed = self.db.query(Feed).filter(Feed.id == feed_id).first()
        if not feed:
            return False
        
        self.db.delete(feed)
        self.db.commit()
        
        logger.info(f"Deleted feed: {feed.name}")
        return True
