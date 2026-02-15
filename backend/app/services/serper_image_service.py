"""
Serper.dev Image Search Service

Uses Serper.dev API to search for topic-relevant images from Google Images.
This provides better image matching than generic stock photos because:
1. Searches are based on article title/topic
2. Returns real-world images related to the content
3. Better for news/tech topics than abstract stock photos

API: https://serper.dev
Fallback: Pexels/Unsplash stock photos
"""

import os
import logging
import asyncio
import aiohttp
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SerperImage:
    """Represents an image result from Serper."""
    url: str
    title: str
    source: str
    width: int
    height: int
    thumbnail_url: Optional[str] = None


class SerperImageService:
    """Service for searching images via Serper.dev API."""
    
    BASE_URL = "https://google.serper.dev/images"
    CACHE_DIR = Path("data/images/serper_cache")
    
    # Minimum dimensions for video backgrounds (portrait mode 1080x1920)
    MIN_WIDTH = 800
    MIN_HEIGHT = 600
    
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            logger.warning("SERPER_API_KEY not set - Serper image search disabled")
        
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_available(self) -> bool:
        """Check if Serper API is available."""
        return bool(self.api_key)
    
    async def search_images(
        self,
        query: str,
        num_results: int = 5,
        safe_search: bool = True
    ) -> List[SerperImage]:
        """
        Search for images using Serper.dev API.
        
        Args:
            query: Search query (article title, topic, etc.)
            num_results: Number of results to return (max 10)
            safe_search: Enable safe search filter
            
        Returns:
            List of SerperImage objects
        """
        if not self.is_available:
            logger.warning("Serper API not available")
            return []
        
        try:
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "num": min(num_results, 10),  # API limit
            }
            
            if safe_search:
                payload["safe"] = "active"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.BASE_URL,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Serper API error {response.status}: {error_text}")
                        return []
                    
                    data = await response.json()
            
            images = []
            for img_data in data.get("images", []):
                try:
                    image = SerperImage(
                        url=img_data.get("imageUrl", ""),
                        title=img_data.get("title", ""),
                        source=img_data.get("source", ""),
                        width=img_data.get("imageWidth", 0),
                        height=img_data.get("imageHeight", 0),
                        thumbnail_url=img_data.get("thumbnailUrl")
                    )
                    
                    # Filter by minimum dimensions for video use
                    if image.width >= self.MIN_WIDTH and image.height >= self.MIN_HEIGHT:
                        images.append(image)
                        
                except Exception as e:
                    logger.warning(f"Error parsing image result: {e}")
                    continue
            
            logger.info(f"Serper search '{query[:50]}...': found {len(images)} suitable images")
            return images
            
        except asyncio.TimeoutError:
            logger.error("Serper API timeout")
            return []
        except Exception as e:
            logger.error(f"Serper search error: {e}")
            return []
    
    async def download_image(
        self,
        image: SerperImage,
        output_dir: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Download an image and save it locally.
        
        Args:
            image: SerperImage object
            output_dir: Directory to save image (default: cache dir)
            
        Returns:
            Path to downloaded image, or None if failed
        """
        output_dir = output_dir or self.CACHE_DIR
        
        # Generate cache filename from URL hash
        url_hash = hashlib.md5(image.url.encode()).hexdigest()[:12]
        extension = self._get_extension(image.url)
        filename = f"serper_{url_hash}{extension}"
        output_path = output_dir / filename
        
        # Return cached version if exists
        if output_path.exists():
            logger.debug(f"Using cached image: {output_path}")
            return output_path
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    image.url,
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={"User-Agent": "Mozilla/5.0 (compatible; AIVideoGen/1.0)"}
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to download image: {response.status}")
                        return None
                    
                    content = await response.read()
                    
                    # Validate it's actually an image
                    content_type = response.headers.get("Content-Type", "")
                    if not content_type.startswith("image/"):
                        logger.warning(f"Not an image: {content_type}")
                        return None
                    
                    # Save the file
                    with open(output_path, "wb") as f:
                        f.write(content)
                    
                    logger.info(f"Downloaded image: {output_path.name} ({len(content) / 1024:.1f}KB)")
                    return output_path
                    
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None
    
    async def search_and_download(
        self,
        query: str,
        num_results: int = 3,
        output_dir: Optional[Path] = None
    ) -> List[Path]:
        """
        Search for images and download them.
        
        Args:
            query: Search query
            num_results: Number of images to download
            output_dir: Directory to save images
            
        Returns:
            List of paths to downloaded images
        """
        images = await self.search_images(query, num_results=num_results + 2)  # Extra for failures
        
        downloaded = []
        for image in images[:num_results + 2]:
            path = await self.download_image(image, output_dir)
            if path:
                downloaded.append(path)
            if len(downloaded) >= num_results:
                break
        
        return downloaded
    
    def _get_extension(self, url: str) -> str:
        """Extract file extension from URL."""
        # Common image extensions
        for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
            if ext in url.lower():
                return ext
        return ".jpg"  # Default


# Convenience function for testing
async def test_serper_search(query: str):
    """Test Serper image search."""
    service = SerperImageService()
    if not service.is_available:
        print("Serper API not available (check SERPERDEV_KEY)")
        return
    
    print(f"Searching for: {query}")
    images = await service.search_images(query, num_results=5)
    
    for i, img in enumerate(images, 1):
        print(f"\n{i}. {img.title[:60]}...")
        print(f"   Size: {img.width}x{img.height}")
        print(f"   URL: {img.url[:80]}...")
    
    if images:
        print("\nDownloading first image...")
        path = await service.download_image(images[0])
        if path:
            print(f"Saved to: {path}")


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "artificial intelligence technology"
    asyncio.run(test_serper_search(query))
