"""
Pexels Video API integration for stock video search and caching.

Uses the Pexels Videos API endpoint to search for and download
short stock video clips to use as scene backgrounds.
"""

import logging
import requests
from pathlib import Path
from typing import List, Optional, Dict, Any
import hashlib
import os

logger = logging.getLogger(__name__)


class PexelsVideoService:
    """Service for searching and caching stock videos from Pexels."""
    
    # Pexels Videos API endpoint
    BASE_URL = "https://api.pexels.com/videos"
    CACHE_DIR = Path("data/stock_videos")
    
    # Target durations for scene videos (in seconds)
    MIN_DURATION = 5
    MAX_DURATION = 30  # Prefer shorter clips for faster downloads
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Pexels Video service.
        
        Args:
            api_key: Pexels API key (defaults to env variable)
        """
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
        logger.info("✓ Pexels Video Service initialized")
    
    def search_video(
        self,
        keywords: List[str],
        orientation: str = "portrait",
        min_duration: int = 5,
        max_duration: int = 20
    ) -> Optional[Path]:
        """
        Search for a video and download it.
        
        Args:
            keywords: List of search keywords
            orientation: Video orientation (portrait, landscape, square)
            min_duration: Minimum video duration in seconds
            max_duration: Maximum video duration in seconds
            
        Returns:
            Path to downloaded video, or None if not found
        """
        # Create cache key from keywords
        cache_key = self._get_cache_key(keywords)
        cached_path = self.CACHE_DIR / f"{cache_key}.mp4"
        
        # Check cache first
        if cached_path.exists():
            logger.info(f"Using cached video: {cached_path}")
            return cached_path
        
        # Search Pexels Videos API
        query = " ".join(keywords[:3])  # Use first 3 keywords
        logger.info(f"Searching Pexels Videos for: {query}")
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/search",
                headers=self.headers,
                params={
                    "query": query,
                    "orientation": orientation,
                    "per_page": 5,  # Get a few options
                    "size": "medium"  # Balance quality and download speed
                },
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            videos = data.get("videos", [])
            
            if not videos:
                logger.warning(f"No videos found for: {query}")
                return None
            
            # Find best video (within duration constraints)
            best_video = self._select_best_video(videos, min_duration, max_duration)
            
            if not best_video:
                logger.warning(f"No suitable video found for: {query} (duration constraints)")
                return None
            
            # Get the download URL (prefer HD quality for portrait videos)
            video_url = self._get_video_url(best_video, orientation)
            
            if not video_url:
                logger.warning("Could not get video download URL")
                return None
            
            # Download video
            logger.info(f"Downloading video from Pexels...")
            video_response = requests.get(video_url, timeout=60, stream=True)
            video_response.raise_for_status()
            
            # Save to cache
            with open(cached_path, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = cached_path.stat().st_size / (1024 * 1024)
            logger.info(f"Video cached: {cached_path} ({file_size:.1f} MB)")
            return cached_path
            
        except requests.exceptions.Timeout:
            logger.error("Pexels video search timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching Pexels videos: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def _select_best_video(
        self, 
        videos: List[Dict], 
        min_duration: int, 
        max_duration: int
    ) -> Optional[Dict]:
        """Select the best video from search results based on duration."""
        
        for video in videos:
            duration = video.get("duration", 0)
            
            # Check duration constraints
            if min_duration <= duration <= max_duration:
                logger.info(f"Selected video: {video.get('id')} ({duration}s)")
                return video
        
        # If no video in ideal range, get the shortest one
        sorted_videos = sorted(videos, key=lambda v: v.get("duration", 999))
        if sorted_videos:
            video = sorted_videos[0]
            logger.info(f"Using shortest video: {video.get('id')} ({video.get('duration')}s)")
            return video
        
        return None
    
    def _get_video_url(self, video: Dict, orientation: str = "portrait") -> Optional[str]:
        """Get the best video file URL for the orientation."""
        video_files = video.get("video_files", [])
        
        if not video_files:
            return None
        
        # For portrait orientation (Shorts), prefer:
        # 1. HD quality (720p or higher)
        # 2. Reasonable file size
        if orientation == "portrait":
            # Sort by quality (height descending) and pick 720-1080p range
            candidates = [
                f for f in video_files 
                if f.get("height", 0) >= 720 and f.get("height", 0) <= 1920
            ]
            if candidates:
                # Sort by height descending
                candidates.sort(key=lambda f: f.get("height", 0), reverse=True)
                return candidates[0].get("link")
        
        # Fallback: get the largest file
        video_files.sort(key=lambda f: f.get("height", 0), reverse=True)
        return video_files[0].get("link") if video_files else None
    
    def _get_cache_key(self, keywords: List[str]) -> str:
        """Generate cache key from keywords."""
        sorted_keywords = sorted([k.lower().strip() for k in keywords])
        key_string = "_".join(sorted_keywords)
        return "video_" + hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    def get_cached_video(self, keywords: List[str]) -> Optional[Path]:
        """Check if video is already cached."""
        cache_key = self._get_cache_key(keywords)
        cached_path = self.CACHE_DIR / f"{cache_key}.mp4"
        return cached_path if cached_path.exists() else None
    
    def clear_cache(self):
        """Clear all cached videos."""
        for video_file in self.CACHE_DIR.glob("*.mp4"):
            video_file.unlink()
        logger.info("Video cache cleared")


# Convenience function for testing
def test_pexels_video(keywords: List[str]):
    """Test Pexels video search."""
    service = PexelsVideoService()
    video_path = service.search_video(keywords, orientation="portrait")
    
    if video_path:
        size_mb = video_path.stat().st_size / (1024 * 1024)
        print(f"✅ Video downloaded: {video_path}")
        print(f"   Size: {size_mb:.1f} MB")
        return video_path
    else:
        print(f"❌ No video found for: {keywords}")
        return None


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_pexels_video(sys.argv[1:])
    else:
        # Test with AI/tech keywords
        test_pexels_video(["autonomous vehicle", "self driving car"])
