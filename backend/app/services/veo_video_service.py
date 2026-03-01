"""
Veo Video Generation Service.

Uses Google's Veo 3.1 API via the google-genai SDK to generate AI video clips
from text prompts.  Designed for YouTube Shorts scene backgrounds where stock
video is either unavailable or too generic.

Requires:
    pip install google-genai
"""

import os
import time
import logging
import asyncio
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class VeoVideoService:
    """
    Service for generating short video clips using Veo 3.1.

    Each call produces an 8-second 720p clip (portrait 9:16 by default).
    Generation is async with polling – latency is typically 30-90 seconds.
    """

    MODEL = "veo-3.1-generate-preview"
    DEFAULT_ASPECT_RATIO = "9:16"       # Portrait for YouTube Shorts
    DEFAULT_DURATION = 8                # 8-second clips (max for Veo 3.1)
    DEFAULT_RESOLUTION = "720p"         # 720p is fastest; 1080p also available
    POLL_INTERVAL = 10                  # seconds between status polls
    MAX_POLL_TIME = 300                 # 5-minute hard timeout

    def __init__(self):
        """Initialize with Google API key."""
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._client = None

        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"✓ Veo Video Service initialized (model={self.MODEL})")
            except ImportError:
                logger.warning("google-genai package not installed. Run: pip install google-genai")
            except Exception as e:
                logger.warning(f"Failed to initialize Veo client: {e}")

    @property
    def is_available(self) -> bool:
        """Check if the service is ready to generate videos."""
        return self._client is not None

    async def generate_video(
        self,
        prompt: str,
        output_path: Path,
        aspect_ratio: str = None,
        duration_seconds: int = None,
        resolution: str = None,
    ) -> Optional[Path]:
        """
        Generate a video clip from a text prompt and save it.

        Args:
            prompt: Text description of the video to generate
            output_path: Path to save the generated MP4
            aspect_ratio: Aspect ratio (default: 9:16 for vertical)
            duration_seconds: Clip duration in seconds (default: 8)
            resolution: Video resolution (default: 720p)

        Returns:
            Path to saved video, or None if generation failed
        """
        if not self.is_available:
            logger.warning("[Veo] Service not available")
            return None

        aspect_ratio = aspect_ratio or self.DEFAULT_ASPECT_RATIO
        duration_seconds = duration_seconds or self.DEFAULT_DURATION
        resolution = resolution or self.DEFAULT_RESOLUTION

        logger.info(
            f"[Veo] Generating video ({aspect_ratio}, {resolution}, {duration_seconds}s)"
        )
        logger.debug(f"[Veo] Prompt: {prompt[:200]}...")

        try:
            result = await asyncio.to_thread(
                self._generate_sync,
                prompt,
                output_path,
                aspect_ratio,
                duration_seconds,
                resolution,
            )
            return result
        except Exception as e:
            logger.error(f"[Veo] Generation failed: {type(e).__name__}: {e}")
            return None

    def _generate_sync(
        self,
        prompt: str,
        output_path: Path,
        aspect_ratio: str,
        duration_seconds: int,
        resolution: str,
    ) -> Optional[Path]:
        """Synchronous video generation with polling (called via asyncio.to_thread)."""
        from google.genai import types

        # Start the long-running operation
        operation = self._client.models.generate_videos(
            model=self.MODEL,
            prompt=prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                duration_seconds=str(duration_seconds),
                person_generation="allow_adult",
            ),
        )

        # Poll until done or timeout
        elapsed = 0
        while not operation.done:
            if elapsed >= self.MAX_POLL_TIME:
                logger.error(f"[Veo] Timed out after {self.MAX_POLL_TIME}s")
                return None
            logger.info(f"[Veo] Waiting for video... ({elapsed}s elapsed)")
            time.sleep(self.POLL_INTERVAL)
            elapsed += self.POLL_INTERVAL
            operation = self._client.operations.get(operation)

        # Download the generated video
        try:
            generated_video = operation.response.generated_videos[0]
            output_path.parent.mkdir(parents=True, exist_ok=True)

            self._client.files.download(file=generated_video.video)
            generated_video.video.save(str(output_path))

            file_size = output_path.stat().st_size if output_path.exists() else 0
            logger.info(
                f"[Veo] Saved: {output_path.name} "
                f"({file_size / 1024:.1f} KB, {elapsed}s generation time)"
            )
            return output_path
        except Exception as e:
            logger.error(f"[Veo] Failed to download/save video: {e}")
            return None

    # ── Cinematic Prompt Builder ─────────────────────────────────────

    CINEMATIC_SUFFIX = (
        "Cinematic quality, shallow depth of field, professional color grading, "
        "smooth camera movement, 24fps film look"
    )

    def build_scene_prompt(
        self,
        scene_text: str,
        visual_cues: str,
        book_title: str = "",
        book_author: str = "",
        scene_number: int = 1,
        total_scenes: int = 8,
        content_type: str = "book_review",
    ) -> str:
        """
        Build a cinematic video generation prompt from scene context.

        Returns a rich prompt optimized for Veo 3.1 video output.
        """
        # Determine scene role for camera/mood guidance
        if scene_number == 1:
            camera_hint = "Opening hook — dramatic reveal, slow zoom in"
        elif scene_number == total_scenes:
            camera_hint = "Closing scene — warm pullback, uplifting mood"
        elif scene_number <= total_scenes // 3:
            camera_hint = "Early scene — establishing shot, building intrigue"
        elif scene_number <= 2 * total_scenes // 3:
            camera_hint = "Mid scene — close-up, intense focus, key insight"
        else:
            camera_hint = "Late scene — tracking shot, reflective mood"

        parts = [
            "Create a cinematic 8-second video clip for a YouTube Shorts background.",
            "",
        ]

        if content_type == "book_review" and book_title:
            parts.append(f'BOOK: "{book_title}" by {book_author}')

        parts.extend([
            f"SCENE: {scene_number} of {total_scenes} ({camera_hint})",
            "",
        ])

        if visual_cues:
            parts.append(f"VISUAL DIRECTION: {visual_cues}")

        if scene_text:
            context = scene_text[:200].rsplit(" ", 1)[0] if len(scene_text) > 200 else scene_text
            parts.append(f"NARRATION CONTEXT: {context}")

        parts.extend([
            "",
            "STYLE REQUIREMENTS:",
            "- Vertical composition (9:16 aspect ratio)",
            "- No text, watermarks, or UI overlays",
            "- Smooth, slow camera movement",
            "- Rich color palette with cinematic lighting",
            "- Evoke emotion — this plays behind narration",
            "- NO dialogue or speech in audio",
        ])

        base_prompt = "\n".join(parts)
        return f"{base_prompt}\n\n{self.CINEMATIC_SUFFIX}"
