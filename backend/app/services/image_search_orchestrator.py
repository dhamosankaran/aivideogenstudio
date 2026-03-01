"""
Image Search Orchestrator - Multi-source image search with fallback chain.

Priority order (optimized for topic-relevant images):
0. Gemini AI (AI-generated images - best for book reviews / abstract concepts)
1. Serper (Google Images - best for news/tech topics)
2. Unsplash (high quality stock photos)
3. Pexels (fallback stock photos)
4. Gradient background (final fallback)
"""

import logging
import asyncio
from pathlib import Path
from typing import List, Optional
import hashlib

logger = logging.getLogger(__name__)


class ImageSearchOrchestrator:
    """
    Orchestrates image search across multiple providers with fallback chain.
    
    Usage:
        orchestrator = ImageSearchOrchestrator()
        image_path = orchestrator.search_image(["Waymo", "self-driving car"])
        
        # Async version (preferred):
        image_path = await orchestrator.search_image_async(["Waymo", "self-driving"])
    """
    
    # Ephemeral cache for raw Serper/Pexels downloads (purgeable)
    CACHE_DIR = Path("data/images/_cache")
    
    # Legacy fallback when no project dir is specified
    FALLBACK_DIR = Path("data/images")
    
    def __init__(self):
        """Initialize with available image providers."""
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialize providers (gracefully handle missing API keys)
        self.gemini_image = None
        self.serper = None
        self.unsplash = None
        self.pexels = None
        
        # Gemini AI image generation (best for book reviews / abstract concepts)
        try:
            from app.services.gemini_image_service import GeminiImageService
            gemini = GeminiImageService()
            if gemini.is_available:
                self.gemini_image = gemini
                logger.info("✓ Gemini Image service initialized (AI generation)")
            else:
                logger.info("Gemini Image API key not configured (optional)")
        except Exception as e:
            logger.warning(f"Could not initialize Gemini Image: {e}")
        
        # Try Serper first (best for topic-relevant images)
        try:
            from app.services.serper_image_service import SerperImageService
            serper = SerperImageService()
            if serper.is_available:
                self.serper = serper
                logger.info("✓ Serper service initialized (primary)")
            else:
                logger.warning("Serper API key not configured (SERPER_API_KEY)")
        except Exception as e:
            logger.warning(f"Could not initialize Serper: {e}")
        
        # Unsplash for high-quality stock photos
        try:
            from app.services.unsplash_service import UnsplashService
            unsplash = UnsplashService()
            if unsplash.access_key:
                self.unsplash = unsplash
                logger.info("✓ Unsplash service initialized (fallback 1)")
            else:
                logger.warning("Unsplash API key not configured")
        except Exception as e:
            logger.warning(f"Could not initialize Unsplash: {e}")
            
        # Pexels as final stock photo fallback
        try:
            from app.services.pexels_service import PexelsService
            self.pexels = PexelsService()
            logger.info("✓ Pexels service initialized (fallback 2)")
        except ValueError as e:
            logger.warning(f"Could not initialize Pexels: {e}")
        except Exception as e:
            logger.warning(f"Could not initialize Pexels: {e}")
    
    async def search_image_async(
        self,
        keywords: List[str],
        topic_query: Optional[str] = None,
        orientation: str = "portrait",
        size: str = "regular",
        content_type: str = "",
        output_dir: Optional[Path] = None,
        human_presence_boost: bool = False,
        ai_prompt: Optional[str] = None
    ) -> Optional[Path]:
        """
        Async search for an image across all providers.
        
        Args:
            keywords: List of search keywords (for stock photos)
            topic_query: Specific topic query (for Serper - uses article title if set)
            orientation: Image orientation (portrait, landscape)
            size: Image size
            content_type: Content type (for legacy fallback path)
            output_dir: Project directory to save image (preferred over content_type)
            human_presence_boost: If True, append 'person' to stock queries to
                                  bias results toward human-centric imagery
            
        Returns:
            Path to downloaded image, or None if not found
        """
        if not keywords and not topic_query:
            return None
        
        # Use topic_query for Serper, keywords for stock photos
        serper_query = topic_query or " ".join(keywords[:4])
        stock_query = " ".join(keywords[:3])
        
        # Human presence boost: append "person" to stock queries for people-centric results
        if human_presence_boost and "person" not in stock_query.lower():
            stock_query = f"{stock_query} person"
            logger.info(f"[HumanBoost] Boosted stock query: {stock_query}")
        
        # Create cache key
        cache_key = self._get_cache_key(keywords + ([topic_query] if topic_query else []))
        
        # Determine output directory:
        # 1. Explicit output_dir (project folder) — preferred
        # 2. Fallback dir for legacy callers
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            target_dir = output_dir
        else:
            self.FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
            target_dir = self.FALLBACK_DIR
        
        cached_path = target_dir / f"{cache_key}.jpg"
        
        # Check cache first (in target directory)
        if cached_path.exists():
            logger.info(f"Using cached image: {cached_path}")
            return cached_path
        
        # Try Gemini AI generation first (if prompt provided)
        if ai_prompt and self.gemini_image:
            logger.info(f"[GeminiAI] Generating image for: {ai_prompt[:80]}...")
            # Use .png for AI-generated images (lossless quality)
            ai_path = cached_path.with_suffix('.png')
            result = await self._generate_gemini_image_async(ai_prompt, ai_path)
            if result:
                return result
        
        # Try Serper (best for topic-specific images)
        if self.serper:
            logger.info(f"[Serper] Searching: {serper_query[:50]}...")
            result = await self._search_serper_async(serper_query, cached_path)
            if result:
                return result
        
        # Try Unsplash
        if self.unsplash:
            logger.info(f"[Unsplash] Fallback: {stock_query}")
            result = self._search_unsplash(stock_query, orientation, size, cached_path)
            if result:
                return result
        
        # Try Pexels as final fallback
        if self.pexels:
            logger.info(f"[Pexels] Fallback: {stock_query}")
            result = self._search_pexels(keywords, orientation, cached_path)
            if result:
                return result
        
        logger.warning(f"No images found for: {serper_query}")
        return None
    
    def search_image(
        self,
        keywords: List[str],
        topic_query: Optional[str] = None,
        orientation: str = "portrait",
        size: str = "regular",
        content_type: str = "",
        output_dir: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Sync wrapper for search_image_async.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                future = asyncio.ensure_future(
                    self.search_image_async(keywords, topic_query, orientation, size, content_type, output_dir)
                )
                return asyncio.get_event_loop().run_until_complete(future)
            else:
                return loop.run_until_complete(
                    self.search_image_async(keywords, topic_query, orientation, size, content_type, output_dir)
                )
        except RuntimeError:
            return asyncio.run(
                self.search_image_async(keywords, topic_query, orientation, size, content_type, output_dir)
            )
    
    async def _search_serper_async(
        self, 
        query: str, 
        output_path: Path
    ) -> Optional[Path]:
        """Search Serper and download image with title-aware relevance filtering."""
        try:
            # Append negative keywords for book-related searches to filter noise
            search_query = query
            query_lower = query.lower()
            is_book_query = any(term in query_lower for term in ["book", "author", "reading", "habit", "review"])
            
            if is_book_query:
                search_query = f"{query} -amazon -kindle -ebay -audible -religious -flipkart -goodreads"
                logger.info(f"[Serper] Book-aware query with negative keywords")
            
            images = await self.serper.search_images(search_query, num_results=8)
            
            if not images:
                logger.info(f"[Serper] No results for: {query[:50]}")
                return None
            
            # ==== TITLE-AWARE RELEVANCE FILTERING ====
            # For book queries, prefer images whose title/source contains book title words.
            # This prevents "How to Win Friends" from appearing in "7 Habits" videos.
            if is_book_query:
                # Extract likely book title words from query (first part, usually the title)
                # Ignore very short words and common terms
                stop_words = {'the', 'a', 'an', 'of', 'and', 'in', 'to', 'for', 'by', 'on', 'is',
                              'book', 'cover', 'front', 'author', 'portrait', 'photo', 'speaking',
                              'event', 'review', 'recommendation', 'subscribe', 'bestselling',
                              'infographic', 'sales', 'accolades', 'award', 'target', 'audience',
                              'person', 'reading', 'concept', 'visual', 'diagram'}
                title_words = [w.lower() for w in query.split() if len(w) > 2 and w.lower() not in stop_words]
                
                if title_words:
                    def relevance_score(img):
                        """Score an image result by how many query title words appear in its title/source."""
                        img_text = f"{img.title} {img.source}".lower()
                        return sum(1 for w in title_words if w in img_text)
                    
                    # Sort by relevance (highest first)
                    images.sort(key=relevance_score, reverse=True)
                    
                    best_score = relevance_score(images[0])
                    logger.info(f"[Serper] Relevance filtering: top result score={best_score} "
                               f"title='{images[0].title[:60]}' (query_words={title_words[:5]})")
            
            # Try to download the best available image
            for image in images:
                path = await self.serper.download_image(image, self.CACHE_DIR)
                if path and path.exists():
                    # Copy to our cache location with consistent naming
                    import shutil
                    shutil.copy(path, output_path)
                    logger.info(f"[Serper] Downloaded: {output_path} (title='{image.title[:50]}')")
                    return output_path
            
            return None
            
        except Exception as e:
            logger.error(f"[Serper] Error: {e}")
            return None
    
    def _search_unsplash(
        self, 
        query: str, 
        orientation: str, 
        size: str,
        output_path: Path
    ) -> Optional[Path]:
        """Search Unsplash and download image."""
        try:
            # Map orientation for Unsplash
            unsplash_orientation = "portrait" if orientation == "portrait" else "landscape"
            
            photos = self.unsplash.search_photos(
                query, 
                orientation=unsplash_orientation, 
                per_page=1
            )
            
            if not photos:
                logger.info(f"[Unsplash] No results for: {query}")
                return None
            
            photo = photos[0]
            image_url = photo["urls"].get(size, photo["urls"]["regular"])
            download_location = photo["links"]["download_location"]
            
            # Download the image
            if self.unsplash.download_photo(image_url, str(output_path)):
                # Track download per Unsplash API guidelines
                self.unsplash.track_download(download_location)
                logger.info(f"[Unsplash] Downloaded: {output_path}")
                return output_path
            
            return None
            
        except Exception as e:
            logger.error(f"[Unsplash] Error: {e}")
            return None
    
    def _search_pexels(
        self, 
        keywords: List[str], 
        orientation: str,
        output_path: Path
    ) -> Optional[Path]:
        """Search Pexels and download image."""
        try:
            # Pexels service has different interface
            result = self.pexels.search_image(
                keywords, 
                orientation=orientation,
                size="large"
            )
            
            if result and result.exists():
                # Copy to our cache location (Pexels uses its own cache)
                import shutil
                shutil.copy(result, output_path)
                logger.info(f"[Pexels] Downloaded: {output_path}")
                return output_path
            
            return None
            
        except Exception as e:
            logger.error(f"[Pexels] Error: {e}")
            return None
    
    def _get_cache_key(self, keywords: List[str]) -> str:
        """Generate cache key from keywords."""
        sorted_keywords = sorted([k.lower().strip() for k in keywords])
        key_string = "_".join(sorted_keywords)
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    async def _generate_gemini_image_async(
        self,
        prompt: str,
        output_path: Path
    ) -> Optional[Path]:
        """Generate an image using Gemini AI."""
        try:
            result = await self.gemini_image.generate_image(
                prompt=prompt,
                output_path=output_path
            )
            if result and result.exists():
                logger.info(f"[GeminiAI] Generated: {output_path.name}")
                return result
            return None
        except Exception as e:
            logger.error(f"[GeminiAI] Error: {e}")
            return None
    
    def get_provider_status(self) -> dict:
        """Get status of all providers."""
        return {
            "gemini_image": bool(self.gemini_image),
            "serper": bool(self.serper),
            "unsplash": bool(self.unsplash),
            "pexels": bool(self.pexels),
            "fallback": "gradient"
        }


# Convenience test function
def test_orchestrator(keywords: List[str]):
    """Test the image search orchestrator."""
    orchestrator = ImageSearchOrchestrator()
    print(f"Provider status: {orchestrator.get_provider_status()}")
    
    image_path = orchestrator.search_image(keywords)
    
    if image_path:
        print(f"✅ Image downloaded: {image_path}")
        print(f"   Size: {image_path.stat().st_size / 1024:.1f} KB")
    else:
        print(f"❌ No image found for: {keywords}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_orchestrator(sys.argv[1:])
    else:
        test_orchestrator(["artificial intelligence", "technology"])
