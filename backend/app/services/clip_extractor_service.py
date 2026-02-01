"""
Clip Extractor Service for Phase 2.5 Enhancement.

Handles downloading and extracting clips from YouTube videos using yt-dlp.
Clips are used for Mode A (React/Commentary) videos.
"""

import os
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Output directory for clips
CLIPS_DIR = Path("data/clips")
CLIPS_DIR.mkdir(parents=True, exist_ok=True)


class ClipExtractorService:
    """Service for extracting clips from YouTube videos."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the clip extractor service.
        
        Args:
            output_dir: Directory to store downloaded clips
        """
        self.output_dir = output_dir or CLIPS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_clip_filename(
        self,
        video_id: str,
        start_time: float,
        end_time: float
    ) -> str:
        """Generate a unique filename for the clip."""
        start_str = f"{int(start_time):05d}"
        end_str = f"{int(end_time):05d}"
        return f"clip_{video_id}_{start_str}_{end_str}.mp4"
    
    def get_clip_path(
        self,
        video_id: str,
        start_time: float,
        end_time: float
    ) -> Path:
        """Get the path where a clip would be stored."""
        filename = self.get_clip_filename(video_id, start_time, end_time)
        return self.output_dir / filename
    
    def clip_exists(
        self,
        video_id: str,
        start_time: float,
        end_time: float
    ) -> bool:
        """Check if a clip has already been downloaded."""
        clip_path = self.get_clip_path(video_id, start_time, end_time)
        return clip_path.exists() and clip_path.stat().st_size > 0
    
    async def download_clip(
        self,
        youtube_url: str,
        video_id: str,
        start_time: float,
        end_time: float,
        max_duration: float = 60.0
    ) -> Tuple[Path, dict]:
        """
        Download a clip from a YouTube video.
        
        Uses yt-dlp with ffmpeg to download and trim the video.
        
        Args:
            youtube_url: Full YouTube URL
            video_id: YouTube video ID
            start_time: Start time in seconds
            end_time: End time in seconds
            max_duration: Maximum clip duration (default 60s for Shorts)
            
        Returns:
            Tuple of (clip_path, metadata_dict)
            
        Raises:
            ValueError: If download fails or clip is too long
        """
        # Validate duration
        duration = end_time - start_time
        if duration > max_duration:
            logger.warning(f"Clip duration {duration}s exceeds max {max_duration}s, trimming")
            end_time = start_time + max_duration
            duration = max_duration
        
        if duration <= 0:
            raise ValueError(f"Invalid clip duration: {duration}s")
        
        # Check cache
        clip_path = self.get_clip_path(video_id, start_time, end_time)
        if self.clip_exists(video_id, start_time, end_time):
            logger.info(f"Using cached clip: {clip_path}")
            return clip_path, self._get_clip_metadata(clip_path)
        
        logger.info(f"Downloading clip from {youtube_url} [{start_time}s - {end_time}s]")
        
        # Build yt-dlp command with section download
        # Format: download best quality up to 1080p, trim to section
        cmd = [
            "yt-dlp",
            "--format", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "--merge-output-format", "mp4",
            "--download-sections", f"*{start_time}-{end_time}",
            "--force-keyframes-at-cuts",
            "--output", str(clip_path),
            "--no-playlist",
            "--quiet",
            "--progress",
            youtube_url
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                # Try fallback without section download (for older yt-dlp versions)
                logger.warning(f"Section download failed, trying full download + trim: {result.stderr}")
                clip_path = await self._download_and_trim_fallback(
                    youtube_url, video_id, start_time, end_time
                )
            
            if not clip_path.exists():
                raise ValueError(f"Clip download failed: output file not created")
            
            metadata = self._get_clip_metadata(clip_path)
            logger.info(f"Clip downloaded successfully: {clip_path} ({metadata.get('duration', 0):.1f}s)")
            
            return clip_path, metadata
            
        except subprocess.TimeoutExpired:
            raise ValueError("Clip download timed out after 5 minutes")
        except Exception as e:
            logger.error(f"Failed to download clip: {str(e)}")
            raise ValueError(f"Clip download failed: {str(e)}")
    
    async def _download_and_trim_fallback(
        self,
        youtube_url: str,
        video_id: str,
        start_time: float,
        end_time: float
    ) -> Path:
        """
        Fallback method: Download full video and trim with ffmpeg.
        
        Used when yt-dlp's --download-sections is not available.
        """
        temp_path = self.output_dir / f"temp_{video_id}.mp4"
        clip_path = self.get_clip_path(video_id, start_time, end_time)
        
        try:
            # Download full video (or use existing temp)
            if not temp_path.exists():
                cmd_download = [
                    "yt-dlp",
                    "--format", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                    "--merge-output-format", "mp4",
                    "--output", str(temp_path),
                    "--no-playlist",
                    "--quiet",
                    youtube_url
                ]
                
                result = subprocess.run(cmd_download, capture_output=True, text=True, timeout=600)
                if result.returncode != 0:
                    raise ValueError(f"Download failed: {result.stderr}")
            
            # Trim with ffmpeg
            duration = end_time - start_time
            cmd_trim = [
                "ffmpeg",
                "-i", str(temp_path),
                "-ss", str(start_time),
                "-t", str(duration),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-y",
                "-loglevel", "error",
                str(clip_path)
            ]
            
            result = subprocess.run(cmd_trim, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise ValueError(f"Trim failed: {result.stderr}")
            
            return clip_path
            
        finally:
            # Clean up temp file
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass
    
    def _get_clip_metadata(self, clip_path: Path) -> dict:
        """Get metadata for a clip using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=duration,width,height",
                "-of", "json",
                str(clip_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                streams = data.get("streams", [{}])
                if streams:
                    stream = streams[0]
                    return {
                        "duration": float(stream.get("duration", 0)),
                        "width": int(stream.get("width", 0)),
                        "height": int(stream.get("height", 0)),
                        "file_size": clip_path.stat().st_size,
                        "path": str(clip_path)
                    }
        except Exception as e:
            logger.warning(f"Failed to get clip metadata: {e}")
        
        return {
            "duration": 0,
            "width": 0,
            "height": 0,
            "file_size": clip_path.stat().st_size if clip_path.exists() else 0,
            "path": str(clip_path)
        }
    
    def add_watermark(
        self,
        clip_path: Path,
        watermark_text: str = "REACTING TO:",
        position: str = "top"
    ) -> Path:
        """
        Add a watermark to the clip for copyright-safe commentary.
        
        Args:
            clip_path: Path to the input clip
            watermark_text: Text to overlay
            position: Position of watermark (top, bottom)
            
        Returns:
            Path to watermarked clip
        """
        output_path = clip_path.with_stem(f"{clip_path.stem}_watermarked")
        
        # Position mapping
        y_position = "10" if position == "top" else "h-th-10"
        
        cmd = [
            "ffmpeg",
            "-i", str(clip_path),
            "-vf", f"drawtext=text='{watermark_text}':fontsize=24:fontcolor=white:x=10:y={y_position}:box=1:boxcolor=black@0.5",
            "-c:a", "copy",
            "-y",
            "-loglevel", "error",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and output_path.exists():
                logger.info(f"Watermark added: {output_path}")
                return output_path
        except Exception as e:
            logger.warning(f"Failed to add watermark: {e}")
        
        # Return original if watermark fails
        return clip_path
    
    def cleanup_old_clips(self, max_age_days: int = 7) -> int:
        """
        Remove clips older than max_age_days.
        
        Returns:
            Number of clips removed
        """
        removed = 0
        now = datetime.now()
        
        for clip_file in self.output_dir.glob("clip_*.mp4"):
            try:
                file_time = datetime.fromtimestamp(clip_file.stat().st_mtime)
                age_days = (now - file_time).days
                if age_days > max_age_days:
                    clip_file.unlink()
                    removed += 1
                    logger.debug(f"Removed old clip: {clip_file}")
            except Exception as e:
                logger.warning(f"Failed to remove clip {clip_file}: {e}")
        
        if removed > 0:
            logger.info(f"Cleaned up {removed} old clips")
        return removed
