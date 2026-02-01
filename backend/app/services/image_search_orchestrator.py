"""
Image Search Orchestrator - Multi-source image search with fallback chain.

Priority order:
1. Unsplash (free, high quality)
2. Pexels (fallback)
3. Gradient background (final fallback)
"""

import logging
from pathlib import Path
from typing import List, Optional
import hashlib

logger = logging.getLogger(__name__)


class ImageSearchOrchestrator:
    """
    Orchestrates image search across multiple providers with fallback chain.
    
    Usage:
        orchestrator = ImageSearchOrchestrator()
        image_path = orchestrator.search_image(["Elon Musk", "SpaceX"])
    """
    
    CACHE_DIR = Path("data/images")
    
    def __init__(self):
        """Initialize with available image providers."""
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialize providers (gracefully handle missing API keys)
        self.unsplash = None
        self.pexels = None
        
        try:
            from app.services.unsplash_service import UnsplashService
            unsplash = UnsplashService()
            if unsplash.access_key:
                self.unsplash = unsplash
                logger.info("✓ Unsplash service initialized")
            else:
                logger.warning("Unsplash API key not configured")
        except Exception as e:
            logger.warning(f"Could not initialize Unsplash: {e}")
            
        try:
            from app.services.pexels_service import PexelsService
            self.pexels = PexelsService()
            logger.info("✓ Pexels service initialized (fallback)")
        except ValueError as e:
            logger.warning(f"Could not initialize Pexels: {e}")
        except Exception as e:
            logger.warning(f"Could not initialize Pexels: {e}")
    
    def search_image(
        self,
        keywords: List[str],
        orientation: str = "portrait",
        size: str = "regular"
    ) -> Optional[Path]:
        """
        Search for an image across all providers.
        
        Args:
            keywords: List of search keywords
            orientation: Image orientation (portrait, landscape)
            size: Image size (for Unsplash: raw, full, regular, small, thumb)
            
        Returns:
            Path to downloaded image, or None if not found
        """
        if not keywords:
            return None
            
        # Create cache key from keywords
        cache_key = self._get_cache_key(keywords)
        cached_path = self.CACHE_DIR / f"{cache_key}.jpg"
        
        # Check cache first
        if cached_path.exists():
            logger.info(f"Using cached image: {cached_path}")
            return cached_path
        
        query = " ".join(keywords[:3])  # Use first 3 keywords
        
        # Try Unsplash first (primary)
        if self.unsplash:
            logger.info(f"[Unsplash] Searching: {query}")
            result = self._search_unsplash(query, orientation, size, cached_path)
            if result:
                return result
        
        # Try Pexels as fallback
        if self.pexels:
            logger.info(f"[Pexels] Fallback searching: {query}")
            result = self._search_pexels(keywords, orientation, cached_path)
            if result:
                return result
        
        logger.warning(f"No images found for: {query}")
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
    
    def get_provider_status(self) -> dict:
        """Get status of all providers."""
        return {
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
