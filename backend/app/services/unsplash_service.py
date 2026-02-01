"""
Service for interacting with Unsplash API.
"""

import os
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class UnsplashService:
    """
    Service for Unsplash API interactions.
    Requires UNSPLASH_ACCESS_KEY in environment variables.
    """
    
    BASE_URL = "https://api.unsplash.com"
    
    def __init__(self):
        self.access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if not self.access_key:
            logger.warning("UNSPLASH_ACCESS_KEY not found in environment variables. Unsplash features will be disabled.")
            
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        if not self.access_key:
            return {}
        return {"Authorization": f"Client-ID {self.access_key}"}

    def search_photos(self, query: str, orientation: str = "landscape", per_page: int = 10) -> List[Dict]:
        """
        Search for photos on Unsplash.
        
        Args:
            query: Search term
            orientation: Photo orientation (landscape, portrait, squarish)
            per_page: Number of results
            
        Returns:
            List of photo objects
        """
        if not self.access_key:
            logger.error("Cannot search Unsplash: Missing Access Key")
            return []
            
        try:
            params = {
                "query": query,
                "orientation": orientation,
                "per_page": per_page
            }
            
            response = requests.get(
                f"{self.BASE_URL}/search/photos",
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            
            return response.json().get("results", [])
            
        except Exception as e:
            logger.error(f"Unsplash search failed for '{query}': {e}")
            return []

    def track_download(self, download_location: str):
        """
        Trigger a download event as required by Unsplash API guidelines.
        
        Args:
            download_location: The 'download_location' URL from the photo's 'links' object
        """
        if not self.access_key or not download_location:
            return
            
        try:
            # simple GET request to tracking endpoint
            requests.get(download_location, headers=self._get_headers())
        except Exception as e:
            logger.error(f"Failed to track download: {e}")

    def download_photo(self, url: str, filepath: str) -> bool:
        """
        Download a photo to disk.
        
        Args:
            url: Image URL
            filepath: Destination path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
            
        except Exception as e:
            logger.error(f"Failed to download photo from {url}: {e}")
            return False
