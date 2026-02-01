"""
Background music service for video composition.

Provides royalty-free music tracks organized by content type
for mixing with narration audio at 10-15% volume.
"""

import logging
from pathlib import Path
from typing import Optional, List
import random

logger = logging.getLogger(__name__)


class BackgroundMusicService:
    """Service for managing and selecting background music tracks."""
    
    MUSIC_DIR = Path("assets/music")
    
    # Music mapping by content type - using user's custom background.mp3
    MUSIC_MAP = {
        "daily_update": "background.mp3",
        "big_tech": "background.mp3",
        "leader_quote": "background.mp3",
        "arxiv_paper": "background.mp3",
    }
    
    # Fallback track for any content type
    FALLBACK_TRACK = "background.mp3"
    
    def __init__(self):
        """Initialize music service and ensure directory exists."""
        self.MUSIC_DIR.mkdir(parents=True, exist_ok=True)
        
    def get_music_for_content(self, content_type: str) -> Optional[Path]:
        """
        Get appropriate music track for content type.
        
        Args:
            content_type: Type of content (daily_update, big_tech, etc.)
            
        Returns:
            Path to music file, or None if not found
        """
        # Get mapped track or fallback
        track_name = self.MUSIC_MAP.get(content_type, self.FALLBACK_TRACK)
        track_path = self.MUSIC_DIR / track_name
        
        # Check if track exists
        if track_path.exists():
            logger.info(f"Using music track: {track_path}")
            return track_path
        
        # Try fallback
        fallback_path = self.MUSIC_DIR / self.FALLBACK_TRACK
        if fallback_path.exists():
            logger.warning(f"Track {track_name} not found, using fallback")
            return fallback_path
        
        # Check if any music exists
        available_tracks = list(self.MUSIC_DIR.glob("*.mp3"))
        if available_tracks:
            random_track = random.choice(available_tracks)
            logger.warning(f"Using random available track: {random_track}")
            return random_track
        
        logger.warning("No music tracks available in assets/music/")
        return None
    
    def list_available_tracks(self) -> List[Path]:
        """List all available music tracks."""
        return list(self.MUSIC_DIR.glob("*.mp3"))
    
    def get_recommended_volume(self, content_type: str) -> float:
        """
        Get recommended music volume for content type.
        
        Returns value between 0.0 and 1.0 (0-100%).
        Music should be subtle, not overpowering narration.
        """
        # Leader quotes need quieter music
        if content_type == "leader_quote":
            return 0.08  # 8%
        
        # arXiv papers are more technical, keep music subtle
        if content_type == "arxiv_paper":
            return 0.10  # 10%
        
        # News content can have slightly more energy
        return 0.12  # 12%


def check_music_setup():
    """Check if music assets are properly set up."""
    service = BackgroundMusicService()
    tracks = service.list_available_tracks()
    
    print(f"\n🎵 Background Music Setup Check")
    print("=" * 40)
    
    if tracks:
        print(f"✅ Found {len(tracks)} tracks:")
        for track in tracks:
            size_kb = track.stat().st_size / 1024
            print(f"   - {track.name} ({size_kb:.1f} KB)")
    else:
        print("❌ No music tracks found!")
        print(f"\n📁 Please add music files to: {service.MUSIC_DIR.absolute()}")
        print("\nRecommended tracks:")
        for content_type, track_name in service.MUSIC_MAP.items():
            print(f"   - {track_name} (for {content_type})")
        print(f"   - {service.FALLBACK_TRACK} (fallback)")
        print("\n🔗 Free sources:")
        print("   - YouTube Audio Library: https://studio.youtube.com/channel/UC/music")
        print("   - Pixabay Music: https://pixabay.com/music/")
        print("   - Mixkit: https://mixkit.co/free-stock-music/")
    
    return len(tracks) > 0


if __name__ == "__main__":
    check_music_setup()
