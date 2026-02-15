"""
Content extraction service for fetching full article content from URLs.

Uses trafilatura for efficient article extraction from news sites.
"""

import logging
from typing import Optional, Tuple
import trafilatura
from trafilatura.settings import use_config

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Service for extracting full article content from URLs."""
    
    def __init__(self):
        """Initialize content extractor with optimized settings."""
        # Configure trafilatura for article extraction
        self.config = use_config()
        self.config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")
        self.config.set("DEFAULT", "MIN_EXTRACTED_SIZE", "500")
    
    def extract_content(self, url: str, fallback_content: Optional[str] = None) -> Tuple[str, bool]:
        """
        Extract full article content from a URL.
        
        Args:
            url: Article URL to extract content from
            fallback_content: RSS content to use if extraction fails
            
        Returns:
            Tuple of (content, was_extracted) where was_extracted indicates
            if full content was successfully extracted vs using fallback
        """
        if not url:
            logger.warning("No URL provided for content extraction")
            return fallback_content or "", False
        
        try:
            logger.info(f"Extracting content from: {url}")
            
            # Fetch the URL
            downloaded = trafilatura.fetch_url(url)
            
            if not downloaded:
                logger.warning(f"Failed to download URL: {url}")
                return fallback_content or "", False
            
            # Extract article content
            content = trafilatura.extract(
                downloaded,
                config=self.config,
                include_comments=False,
                include_tables=True,
                include_links=False,
                output_format="txt"
            )
            
            if content and len(content) > 500:
                logger.info(f"Successfully extracted {len(content)} chars from {url}")
                return content, True
            else:
                logger.warning(f"Extraction too short ({len(content) if content else 0} chars) for {url}")
                return fallback_content or content or "", False
                
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return fallback_content or "", False
    
    def extract_with_metadata(self, url: str) -> dict:
        """
        Extract content along with metadata.
        
        Args:
            url: Article URL
            
        Returns:
            Dict with 'content', 'title', 'author', 'date', 'extracted' keys
        """
        if not url:
            return {"content": "", "title": None, "author": None, "date": None, "extracted": False}
        
        try:
            downloaded = trafilatura.fetch_url(url)
            
            if not downloaded:
                return {"content": "", "title": None, "author": None, "date": None, "extracted": False}
            
            # Extract content
            content = trafilatura.extract(
                downloaded,
                config=self.config,
                include_comments=False,
                output_format="txt"
            )
            
            # Extract metadata
            metadata = trafilatura.extract_metadata(downloaded)
            
            return {
                "content": content or "",
                "title": metadata.title if metadata else None,
                "author": metadata.author if metadata else None,
                "date": metadata.date if metadata else None,
                "extracted": bool(content and len(content) > 500)
            }
            
        except Exception as e:
            logger.error(f"Error extracting with metadata from {url}: {e}")
            return {"content": "", "title": None, "author": None, "date": None, "extracted": False}


# Singleton instance for reuse
_extractor: Optional[ContentExtractor] = None


def get_content_extractor() -> ContentExtractor:
    """Get or create the content extractor singleton."""
    global _extractor
    if _extractor is None:
        _extractor = ContentExtractor()
    return _extractor


def extract_article_content(url: str, fallback_content: Optional[str] = None) -> Tuple[str, bool]:
    """
    Convenience function to extract article content.
    
    Args:
        url: Article URL
        fallback_content: RSS content to use if extraction fails
        
    Returns:
        Tuple of (content, was_extracted)
    """
    extractor = get_content_extractor()
    return extractor.extract_content(url, fallback_content)
