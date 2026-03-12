"""
Universal Video Downloader Service.

Downloads videos from YouTube, X (Twitter), and LinkedIn using yt-dlp.
Supports full download, audio stripping, and metadata extraction.
"""

import os
import re
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Output directory for downloaded videos
DOWNLOADS_DIR = Path("data/downloads")
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)


class VideoDownloaderService:
    """Platform-agnostic video downloader using yt-dlp."""

    # Supported platform patterns
    PLATFORM_PATTERNS = {
        "youtube": [
            r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=",
            r"(?:https?://)?(?:www\.)?youtube\.com/shorts/",
            r"(?:https?://)?youtu\.be/",
            r"(?:https?://)?(?:www\.)?youtube\.com/embed/",
            r"(?:https?://)?(?:www\.)?youtube\.com/v/",
        ],
        "twitter": [
            r"(?:https?://)?(?:www\.)?(?:twitter|x)\.com/.+/status/",
            r"(?:https?://)?(?:www\.)?x\.com/.+/status/",
        ],
        "linkedin": [
            r"(?:https?://)?(?:www\.)?linkedin\.com/posts/",
            r"(?:https?://)?(?:www\.)?linkedin\.com/feed/update/",
            r"(?:https?://)?(?:www\.)?linkedin\.com/video/",
        ],
    }

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the downloader service.

        Args:
            output_dir: Directory to store downloaded videos
        """
        self.output_dir = output_dir or DOWNLOADS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── Platform detection ──────────────────────────────────────

    def detect_platform(self, url: str) -> str:
        """
        Detect the source platform from a URL.

        Returns:
            One of: youtube, twitter, linkedin, unknown
        """
        for platform, patterns in self.PLATFORM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return platform
        return "unknown"

    def extract_video_id(self, url: str, platform: str = None) -> Optional[str]:
        """
        Extract the video/post ID from a URL.

        Args:
            url: Video URL
            platform: Platform name (auto-detected if not provided)

        Returns:
            Video ID string, or None if extraction fails
        """
        if platform is None:
            platform = self.detect_platform(url)

        if platform == "youtube":
            # Standard watch URL
            match = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url)
            if match:
                return match.group(1)
            # Short URL
            match = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
            if match:
                return match.group(1)
            # Shorts/embed/v
            match = re.search(r"(?:shorts|embed|v)/([a-zA-Z0-9_-]{11})", url)
            if match:
                return match.group(1)

        elif platform == "twitter":
            match = re.search(r"/status/(\d+)", url)
            if match:
                return match.group(1)

        elif platform == "linkedin":
            # LinkedIn URN-based IDs
            match = re.search(r"urn:li:activity:(\d+)", url)
            if match:
                return match.group(1)
            # Fallback: use hash of URL
            import hashlib
            return hashlib.md5(url.encode()).hexdigest()[:12]

        return None

    # ── Metadata extraction ─────────────────────────────────────

    async def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        Get video metadata without downloading.

        Args:
            url: Video URL

        Returns:
            Dict with title, duration, thumbnail_url, platform, etc.
        """
        platform = self.detect_platform(url)

        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-download",
            "--no-playlist",
            "--no-check-certificate",
        ]

        # Add platform-specific options
        if platform == "youtube":
            pass

        cmd.append(url)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                logger.warning(f"yt-dlp metadata failed: {result.stderr[:200]}")
                return {
                    "platform": platform,
                    "url": url,
                    "error": result.stderr[:200],
                }

            info = json.loads(result.stdout)
            return {
                "platform": platform,
                "url": url,
                "video_id": info.get("id"),
                "title": info.get("title"),
                "duration": info.get("duration"),
                "thumbnail_url": info.get("thumbnail"),
                "channel_name": info.get("uploader") or info.get("channel"),
                "channel_url": info.get("uploader_url") or info.get("channel_url"),
                "view_count": info.get("view_count"),
                "upload_date": info.get("upload_date"),
                "description": info.get("description", "")[:500],
            }
        except subprocess.TimeoutExpired:
            return {"platform": platform, "url": url, "error": "Metadata fetch timed out"}
        except json.JSONDecodeError:
            return {"platform": platform, "url": url, "error": "Failed to parse metadata"}
        except Exception as e:
            return {"platform": platform, "url": url, "error": str(e)}

    # ── Full video download ─────────────────────────────────────

    async def download_video(
        self,
        url: str,
        strip_audio: bool = False,
        max_height: int = 1080,
    ) -> Tuple[Path, Dict[str, Any]]:
        """
        Download a full video from any supported platform.

        Args:
            url: Video URL (YouTube, X, LinkedIn)
            strip_audio: If True, remove audio track from output
            max_height: Maximum video height (default 1080p)

        Returns:
            Tuple of (output_path, metadata_dict)

        Raises:
            ValueError: If download fails
        """
        platform = self.detect_platform(url)
        video_id = self.extract_video_id(url, platform) or datetime.now().strftime("%Y%m%d_%H%M%S")

        # Generate output filename
        output_filename = f"dl_{platform}_{video_id}.mp4"
        output_path = self.output_dir / output_filename

        # Check cache
        if output_path.exists() and output_path.stat().st_size > 0:
            logger.info(f"Using cached download: {output_path}")
            metadata = self._get_video_metadata(output_path)
            if strip_audio:
                output_path = await self._strip_audio(output_path)
                metadata = self._get_video_metadata(output_path)
            return output_path, metadata

        logger.info(f"Downloading video from {platform}: {url}")

        # Build yt-dlp command
        cmd = [
            "yt-dlp",
            "--format", f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]",
            "--merge-output-format", "mp4",
            "--output", str(output_path),
            "--no-playlist",
            "--no-check-certificate",
            "--quiet",
            "--progress",
        ]

        # Platform-specific options
        if platform == "youtube":
            pass
        elif platform == "twitter":
            # Twitter/X may need cookies; yt-dlp handles most cases
            pass
        elif platform == "linkedin":
            # LinkedIn often requires auth; best-effort
            logger.warning("LinkedIn download: may require authentication for private videos")

        cmd.append(url)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600  # 10min timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr[:300] if result.stderr else "Unknown error"
                logger.error(f"Download failed: {error_msg}")
                raise ValueError(f"Download failed for {platform}: {error_msg}")

            if not output_path.exists():
                # yt-dlp sometimes adds format suffixes; check for them
                possible = list(self.output_dir.glob(f"dl_{platform}_{video_id}.*"))
                if possible:
                    actual = possible[0]
                    if actual.suffix != ".mp4":
                        # Convert to mp4
                        mp4_path = actual.with_suffix(".mp4")
                        self._convert_to_mp4(actual, mp4_path)
                        actual.unlink()
                        output_path = mp4_path
                    else:
                        output_path = actual
                else:
                    raise ValueError("Download completed but output file not found")

            metadata = self._get_video_metadata(output_path)
            logger.info(
                f"Download complete: {output_path} "
                f"({metadata.get('duration', 0):.1f}s, {metadata.get('file_size', 0) / 1024 / 1024:.1f}MB)"
            )

            # Strip audio if requested
            if strip_audio:
                output_path = await self._strip_audio(output_path)
                metadata = self._get_video_metadata(output_path)

            return output_path, metadata

        except subprocess.TimeoutExpired:
            raise ValueError("Download timed out after 10 minutes")
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Download failed: {str(e)}")

    # ── Audio stripping ─────────────────────────────────────────

    async def _strip_audio(self, video_path: Path) -> Path:
        """
        Strip all audio tracks from a video file.

        Args:
            video_path: Path to input video

        Returns:
            Path to output video (no audio)
        """
        output_path = video_path.with_stem(f"{video_path.stem}_noaudio")

        if output_path.exists() and output_path.stat().st_size > 0:
            logger.info(f"Using cached no-audio video: {output_path}")
            return output_path

        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-an",  # Remove audio
            "-c:v", "copy",  # Copy video stream (fast, no re-encode)
            "-y",
            "-loglevel", "error",
            str(output_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                logger.warning(f"Audio stripping failed: {result.stderr[:200]}")
                return video_path  # Return original on failure

            logger.info(f"Audio stripped: {output_path}")
            return output_path

        except Exception as e:
            logger.warning(f"Audio stripping failed: {e}")
            return video_path

    # ── Helpers ──────────────────────────────────────────────────

    def _get_video_metadata(self, video_path: Path) -> Dict[str, Any]:
        """Get metadata for a video file using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration,size:stream=width,height,codec_name",
                "-of", "json",
                str(video_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                fmt = data.get("format", {})
                streams = data.get("streams", [])
                video_stream = next((s for s in streams if s.get("width")), {})
                return {
                    "duration": float(fmt.get("duration", 0)),
                    "file_size": int(fmt.get("size", 0)),
                    "width": int(video_stream.get("width", 0)),
                    "height": int(video_stream.get("height", 0)),
                    "codec": video_stream.get("codec_name", ""),
                    "path": str(video_path),
                    "has_audio": any(
                        s.get("codec_name") and "video" not in s.get("codec_type", "")
                        for s in streams
                    ),
                }
        except Exception as e:
            logger.warning(f"Failed to get video metadata: {e}")

        return {
            "duration": 0,
            "file_size": video_path.stat().st_size if video_path.exists() else 0,
            "width": 0,
            "height": 0,
            "path": str(video_path),
            "has_audio": True,
        }

    def _convert_to_mp4(self, input_path: Path, output_path: Path):
        """Convert a video file to MP4 format."""
        cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "veryfast",
            "-y",
            "-loglevel", "error",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    def cleanup_old_downloads(self, max_age_days: int = 7) -> int:
        """
        Remove downloads older than max_age_days.

        Returns:
            Number of files removed
        """
        removed = 0
        now = datetime.now()

        for video_file in self.output_dir.glob("dl_*"):
            try:
                file_time = datetime.fromtimestamp(video_file.stat().st_mtime)
                age_days = (now - file_time).days
                if age_days > max_age_days:
                    video_file.unlink()
                    removed += 1
                    logger.debug(f"Removed old download: {video_file}")
            except Exception as e:
                logger.warning(f"Failed to remove {video_file}: {e}")

        if removed > 0:
            logger.info(f"Cleaned up {removed} old downloads")
        return removed
