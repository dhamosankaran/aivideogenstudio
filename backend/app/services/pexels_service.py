"""
Pexels API integration for stock photo search and caching.
"""

import logging
import requests
from pathlib import Path
from typing import List, Optional
import hashlib
import os

logger = logging.getLogger(__name__)


class PexelsService:
    """Service for searching and caching stock photos from Pexels."""
    
    BASE_URL = "https://api.pexels.com/v1"
    CACHE_DIR = Path("data/images")
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Pexels service.
        
        Args:
            api_key: Pexels API key (defaults to env variable)
        """
        # Load .env file if not already loaded
        from dotenv import load_dotenv
        load_dotenv()
        
        self.api_key = api_key or os.getenv("PEXELS_API_KEY")
        if not self.api_key:
            raise ValueError("PEXELS_API_KEY not found in environment")
        
        self.headers = {
            "Authorization": self.api_key
        }
        
        # Ensure cache directory exists
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def search_image(
        self,
        keywords: List[str],
        orientation: str = "portrait",
        size: str = "large"
    ) -> Optional[Path]:
        """
        Search for an image and download it.
        
        Args:
            keywords: List of search keywords
            orientation: Image orientation (portrait, landscape, square)
            size: Image size (large, medium, small)
            
        Returns:
            Path to downloaded image, or None if not found
        """
        # Create cache key from keywords
        cache_key = self._get_cache_key(keywords)
        cached_path = self.CACHE_DIR / f"{cache_key}.jpg"
        
        # Check cache first
        if cached_path.exists():
            logger.info(f"Using cached image: {cached_path}")
            return cached_path
        
        # Search Pexels
        query = " ".join(keywords)
        logger.info(f"Searching Pexels for: {query}")
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/search",
                headers=self.headers,
                params={
                    "query": query,
                    "orientation": orientation,
                    "per_page": 1  # We only need one image
                },
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            photos = data.get("photos", [])
            
            if not photos:
                logger.warning(f"No images found for: {query}")
                return None
            
            # Get the first photo
            photo = photos[0]
            image_url = photo["src"][size]
            
            # Download image
            logger.info(f"Downloading image from: {image_url}")
            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()
            
            # Save to cache
            with open(cached_path, 'wb') as f:
                f.write(img_response.content)
            
            logger.info(f"Image cached: {cached_path}")
            return cached_path
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching Pexels: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def _get_cache_key(self, keywords: List[str]) -> str:
        """Generate cache key from keywords."""
        # Sort keywords for consistency
        sorted_keywords = sorted([k.lower().strip() for k in keywords])
        key_string = "_".join(sorted_keywords)
        # Hash to keep filename reasonable
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    def get_cached_image(self, keywords: List[str]) -> Optional[Path]:
        """Check if image is already cached."""
        cache_key = self._get_cache_key(keywords)
        cached_path = self.CACHE_DIR / f"{cache_key}.jpg"
        return cached_path if cached_path.exists() else None
    
    def clear_cache(self):
        """Clear all cached images."""
        for img_file in self.CACHE_DIR.glob("*.jpg"):
            img_file.unlink()
        logger.info("Image cache cleared")


# Convenience function for testing
def test_pexels(keywords: List[str]):
    """Test Pexels image search."""
    service = PexelsService()
    image_path = service.search_image(keywords)
    
    if image_path:
        print(f"✅ Image downloaded: {image_path}")
        print(f"   Size: {image_path.stat().st_size / 1024:.1f} KB")
        return image_path
    else:
        print(f"❌ No image found for: {keywords}")
        return None


if __name__ == "__main__":
    # Test with AI-related keywords
    test_pexels(["artificial intelligence", "technology"])
