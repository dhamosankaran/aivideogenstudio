"""
Video Editor Service for Phase 3.

Non-destructive video editing operations using ffmpeg:
- Trim clips
- Strip audio
- Overlay background music
- Concatenate clips
- Extract preview frames
"""

import os
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Working directory for edited clips
EDITOR_DIR = Path("data/editor")
EDITOR_DIR.mkdir(parents=True, exist_ok=True)


class VideoEditorService:
    """Non-destructive video editor using ffmpeg."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or EDITOR_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── Trim ────────────────────────────────────────────────────

    def trim_clip(
        self,
        video_path: Path,
        start_time: float,
        end_time: float,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Trim a video to the specified time range.

        Uses ffmpeg fast-seek (-ss before -i) for speed.

        Args:
            video_path: Input video path
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Optional output path (auto-generated if None)

        Returns:
            Path to trimmed clip
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        duration = end_time - start_time
        if duration <= 0:
            raise ValueError(f"Invalid trim range: {start_time}s - {end_time}s")

        if output_path is None:
            stem = video_path.stem
            output_path = self.output_dir / f"{stem}_trim_{int(start_time)}_{int(end_time)}.mp4"

        if output_path.exists() and output_path.stat().st_size > 0:
            logger.info(f"Using cached trimmed clip: {output_path}")
            return output_path

        cmd = [
            "ffmpeg",
            "-ss", str(start_time),
            "-i", str(video_path),
            "-t", str(duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "veryfast",
            "-avoid_negative_ts", "make_zero",
            "-y",
            "-loglevel", "error",
            str(output_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                logger.error(f"Trim failed: {result.stderr[:300]}")
                raise ValueError(f"Trim failed: {result.stderr[:200]}")

            logger.info(f"Trimmed {video_path.name} → {output_path.name} ({duration:.1f}s)")
            return output_path

        except subprocess.TimeoutExpired:
            raise ValueError("Trim operation timed out")

    # ── Strip audio ─────────────────────────────────────────────

    def strip_audio(
        self,
        video_path: Path,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Remove all audio tracks from a video.

        Uses stream copy (no re-encode) for speed.

        Args:
            video_path: Input video path
            output_path: Optional output path

        Returns:
            Path to video without audio
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        if output_path is None:
            output_path = self.output_dir / f"{video_path.stem}_noaudio.mp4"

        if output_path.exists() and output_path.stat().st_size > 0:
            logger.info(f"Using cached no-audio video: {output_path}")
            return output_path

        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-an",
            "-c:v", "copy",
            "-y",
            "-loglevel", "error",
            str(output_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                logger.warning(f"Strip audio failed: {result.stderr[:200]}")
                return video_path  # Return original on failure

            logger.info(f"Audio stripped: {output_path}")
            return output_path

        except Exception as e:
            logger.warning(f"Strip audio error: {e}")
            return video_path

    # ── Overlay music ───────────────────────────────────────────

    def overlay_music(
        self,
        video_path: Path,
        music_path: Path,
        volume: float = 0.12,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Add background music to a video.

        If the video has no audio, the music becomes the only audio track.
        If the video has audio, the music is mixed at the specified volume.

        Args:
            video_path: Input video path
            music_path: Path to music file
            volume: Music volume (0.0-1.0)
            output_path: Optional output path

        Returns:
            Path to video with music
        """
        video_path = Path(video_path)
        music_path = Path(music_path)

        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        if not music_path.exists():
            raise FileNotFoundError(f"Music not found: {music_path}")

        if output_path is None:
            output_path = self.output_dir / f"{video_path.stem}_music.mp4"

        if output_path.exists() and output_path.stat().st_size > 0:
            logger.info(f"Using cached music overlay: {output_path}")
            return output_path

        # Check if video has audio
        has_audio = self._has_audio_stream(video_path)

        if has_audio:
            # Mix music with existing audio
            filter_complex = (
                f"[1:a]volume={volume}[music];"
                f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=3[aout]"
            )
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-i", str(music_path),
                "-filter_complex", filter_complex,
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                "-y",
                "-loglevel", "error",
                str(output_path),
            ]
        else:
            # No existing audio — music becomes the audio track
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-i", str(music_path),
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "copy",
                "-c:a", "aac",
                "-filter:a", f"volume={volume}",
                "-shortest",
                "-y",
                "-loglevel", "error",
                str(output_path),
            ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                logger.warning(f"Music overlay failed: {result.stderr[:300]}")
                return video_path

            logger.info(f"Music overlaid: {output_path} (volume={volume})")
            return output_path

        except Exception as e:
            logger.warning(f"Music overlay error: {e}")
            return video_path

    # ── Concatenate clips ───────────────────────────────────────

    def concat_clips(
        self,
        clip_paths: List[Path],
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Concatenate multiple clips into a single video.

        Args:
            clip_paths: List of video file paths
            output_path: Optional output path

        Returns:
            Path to concatenated video
        """
        if not clip_paths:
            raise ValueError("No clips to concatenate")

        if len(clip_paths) == 1:
            return clip_paths[0]

        if output_path is None:
            output_path = self.output_dir / f"concat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

        # Create concat file list
        list_path = self.output_dir / "concat_list.txt"
        with open(list_path, "w") as f:
            for path in clip_paths:
                f.write(f"file '{path}'\n")

        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_path),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "veryfast",
            "-y",
            "-loglevel", "error",
            str(output_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if result.returncode != 0:
                raise ValueError(f"Concat failed: {result.stderr[:200]}")

            logger.info(f"Concatenated {len(clip_paths)} clips → {output_path}")
            return output_path

        except subprocess.TimeoutExpired:
            raise ValueError("Concat operation timed out")
        finally:
            if list_path.exists():
                list_path.unlink()

    # ── Preview / metadata ──────────────────────────────────────

    def get_clip_preview(
        self,
        video_path: Path,
        num_frames: int = 5,
    ) -> Dict[str, Any]:
        """
        Get preview data for a video: duration, dimensions, and frame thumbnails.

        Args:
            video_path: Input video path
            num_frames: Number of preview frames to extract

        Returns:
            Dict with duration, width, height, has_audio, and frame_paths
        """
        video_path = Path(video_path)
        if not video_path.exists():
            return {"error": "Video not found"}

        metadata = self._get_metadata(video_path)

        # Extract keyframes for visual preview
        duration = metadata.get("duration", 0)
        if duration <= 0:
            return metadata

        frame_paths = []
        interval = duration / (num_frames + 1)

        for i in range(num_frames):
            timestamp = interval * (i + 1)
            frame_path = self.output_dir / f"preview_{video_path.stem}_{i}.jpg"

            if not frame_path.exists():
                cmd = [
                    "ffmpeg",
                    "-ss", str(timestamp),
                    "-i", str(video_path),
                    "-vframes", "1",
                    "-q:v", "5",
                    "-y",
                    "-loglevel", "error",
                    str(frame_path),
                ]
                try:
                    subprocess.run(cmd, capture_output=True, timeout=10)
                except Exception:
                    continue

            if frame_path.exists():
                frame_paths.append(str(frame_path))

        metadata["frame_paths"] = frame_paths
        return metadata

    # ── Internals ───────────────────────────────────────────────

    def _has_audio_stream(self, video_path: Path) -> bool:
        """Check if a video file has an audio stream."""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "a",
                "-show_entries", "stream=codec_type",
                "-of", "json",
                str(video_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return len(data.get("streams", [])) > 0
        except Exception:
            pass
        return False

    def _get_metadata(self, video_path: Path) -> Dict[str, Any]:
        """Get video file metadata using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration,size:stream=width,height,codec_name,codec_type",
                "-of", "json",
                str(video_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                fmt = data.get("format", {})
                streams = data.get("streams", [])
                video_stream = next(
                    (s for s in streams if s.get("codec_type") == "video"), {}
                )
                has_audio = any(
                    s.get("codec_type") == "audio" for s in streams
                )
                return {
                    "duration": float(fmt.get("duration", 0)),
                    "file_size": int(fmt.get("size", 0)),
                    "width": int(video_stream.get("width", 0)),
                    "height": int(video_stream.get("height", 0)),
                    "has_audio": has_audio,
                    "path": str(video_path),
                }
        except Exception as e:
            logger.warning(f"Metadata extraction failed: {e}")

        return {
            "duration": 0,
            "file_size": video_path.stat().st_size if video_path.exists() else 0,
            "width": 0,
            "height": 0,
            "has_audio": False,
            "path": str(video_path),
        }

    def cleanup(self, max_age_hours: int = 24) -> int:
        """Remove editor temp files older than max_age_hours."""
        removed = 0
        now = datetime.now()
        for f in self.output_dir.iterdir():
            if f.is_file():
                try:
                    age_hours = (now - datetime.fromtimestamp(f.stat().st_mtime)).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        f.unlink()
                        removed += 1
                except Exception:
                    pass
        if removed:
            logger.info(f"Cleaned up {removed} editor temp files")
        return removed
