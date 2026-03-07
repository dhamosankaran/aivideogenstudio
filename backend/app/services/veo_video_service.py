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

from app.services.gemini_image_service import _prompt_refiner


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

        logger.info(
            f"[Veo] Generating video ({aspect_ratio}, {duration_seconds}s)"
        )
        logger.debug(f"[Veo] Prompt: {prompt[:200]}...")

        try:
            result = await asyncio.to_thread(
                self._generate_sync,
                prompt,
                output_path,
                aspect_ratio,
                duration_seconds,
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
    ) -> Optional[Path]:
        """Synchronous video generation with polling (called via asyncio.to_thread)."""
        from google.genai import types

        # Start the long-running operation
        operation = self._client.models.generate_videos(
            model=self.MODEL,
            prompt=prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                duration_seconds=str(duration_seconds),
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
            videos = getattr(operation.response, "generated_videos", None) or []
            if not videos:
                logger.warning("[Veo] Operation completed but returned no videos (prompt may have been rejected)")
                return None
            generated_video = videos[0]
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

    # ── Genre → Veo Style Mapping ─────────────────────────────────────

    # Book subjects (from Open Library) that map well to whiteboard/illustration style.
    # Everything else defaults to cinematic.
    WHITEBOARD_GENRES = frozenset({
        "self-help", "personal development", "productivity", "habits",
        "business", "leadership", "management", "entrepreneurship",
        "psychology", "motivation", "success", "career", "finance",
        "personal finance", "self improvement", "mindset",
    })

    @classmethod
    def default_veo_style_for_book(cls, subjects: list) -> str:
        """
        Infer the best Veo style from book subjects.

        Returns 'whiteboard' for self-help/business genres, 'cinematic' otherwise.
        Uses rule-based mapping — fast, free, deterministic.
        """
        if not subjects:
            return "cinematic"
        subject_lower = {s.lower() for s in subjects}
        if subject_lower & cls.WHITEBOARD_GENRES:
            return "whiteboard"
        return "cinematic"

    # Scene beat → Veo style routing for "auto" mode.
    # Scene 3 (relatable story) → whiteboard (emotional, organic feel)
    # Scene 4 (famous example) → illustration (polished, authoritative)
    # Scene 6 (cheat code reveal) → illustration (diagram/framework reveal)
    _AUTO_SCENE_STYLE: dict = {
        3: "whiteboard",    # Relatable story — hand-drawn metaphor
        4: "illustration",  # Famous example — polished flat diagram
        6: "illustration",  # Cheat code — framework/system reveal
    }

    @classmethod
    def resolve_scene_style(cls, veo_style: str, scene_number: int) -> str:
        """
        Resolve the effective Veo style for a specific scene.

        Args:
            veo_style: 'cinematic' | 'whiteboard' | 'illustration' | 'auto'
            scene_number: 1-indexed scene number

        Returns one of: 'cinematic', 'whiteboard', 'illustration'
        """
        if veo_style == "auto":
            return cls._AUTO_SCENE_STYLE.get(scene_number, "cinematic")
        return veo_style if veo_style in ("cinematic", "whiteboard", "illustration") else "cinematic"

    # ── Cinematic Prompt Builder ─────────────────────────────────────

    CINEMATIC_SUFFIX = (
        "dynamic camera movement, cinematic tracking shot, highly engaging, "
        "fast-paced energy, adrenaline-pumping visuals, 24fps film look"
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
        # Determine scene role for camera/mood guidance.
        # For book reviews with 8 scenes, use beat-specific camera instructions
        # (Veo only fires on scenes 3, 4, 6 — Relatable Story, Famous Example, Cheat Code).
        # NOTE: All hints are person-free — Veo silently returns empty results
        # when prompts feature people unless account-level person_generation is approved.
        BOOK_REVIEW_CAMERA_MAP = {
            1: "Opening hook — dramatic slow zoom revealing an object or environment, counterintuitive reveal energy",
            2: "Paradox reveal — push-in on symbolic subject, tense high-contrast lighting, no people",
            3: "Relatable story — metaphor in organic motion, fluid camera through an environment",
            4: "Famous example — cinematic environment or iconic object, warm amber tracking shot, no people",
            5: "Hidden truth — light breaking through darkness, revelation moment, abstract or nature scene",
            6: "Cheat code reveal — invisible becomes visible, dramatic contrast, abstract visual metaphor",
            7: "Identity mirror — slow introspective pull-back, moody blue tones, empty reflective space",
            8: "CTA close — warm inviting push toward an object or landscape, aspirational energy",
        }
        if content_type == "book_review" and scene_number in BOOK_REVIEW_CAMERA_MAP:
            camera_hint = BOOK_REVIEW_CAMERA_MAP[scene_number]
        elif scene_number == 1:
            camera_hint = "Opening hook — dramatic reveal of an object or environment, slow zoom in, no people"
        elif scene_number == total_scenes:
            camera_hint = "Closing scene — warm pullback over landscape or environment, uplifting mood, no people"
        elif scene_number <= total_scenes // 3:
            camera_hint = "Early scene — establishing shot of environment, building intrigue, no people"
        elif scene_number <= 2 * total_scenes // 3:
            camera_hint = "Mid scene — close-up on object or texture, intense focus, key insight, no people"
        else:
            camera_hint = "Late scene — tracking shot through environment, reflective mood, no people"

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
            refined_cues = _prompt_refiner.refine(visual_cues)
            parts.append(f"VISUAL DIRECTION: {refined_cues}")

        if scene_text:
            context = scene_text[:200].rsplit(" ", 1)[0] if len(scene_text) > 200 else scene_text
            parts.append(f"NARRATION CONTEXT: {context}")

        parts.extend([
            "",
            "STYLE REQUIREMENTS:",
            "- Vertical composition (9:16 aspect ratio)",
            "- No text, watermarks, or UI overlays",
            "- NO people, faces, or human figures",
            "- Dynamic, energetic camera movement — push-ins, tracking shots, quick reveals",
            "- Rich color palette with cinematic lighting",
            "- Evoke emotion — this plays behind narration",
            "- NO dialogue or speech in audio",
        ])

        base_prompt = "\n".join(parts)
        return f"{base_prompt}\n\n{self.CINEMATIC_SUFFIX}"

    # ── Whiteboard Prompt Builder ─────────────────────────────────────

    # Scene beat → what the hand draws for book review scenes
    WHITEBOARD_SCENE_SUBJECTS = {
        1: "a closed book that slowly opens to reveal glowing pages",
        2: "a question mark that transforms into a lightbulb",
        3: "two contrasting paths — one rocky and winding, one straight and clear",
        4: "a rising staircase with a star at the top",
        5: "gears turning inside a brain outline",
        6: "a lock opening to reveal a hidden key beneath it",
        7: "an arrow breaking through a wall",
        8: "an upward arrow with stars and sparkles bursting around it",
    }

    def build_whiteboard_prompt(
        self,
        scene_number: int = 1,
        total_scenes: int = 8,
        visual_cues: str = "",
        book_title: str = "",
    ) -> str:
        """
        Build a whiteboard animation prompt for a scene.

        Generates a hand-drawing-on-white-canvas style clip.
        Best for storytelling and emotional scenes (Scene 3 — Relatable Story).
        """
        subject = self.WHITEBOARD_SCENE_SUBJECTS.get(scene_number, "an upward arrow with stars")

        # Incorporate visual cues if available
        if visual_cues:
            refined = _prompt_refiner.refine(visual_cues)
            subject = f"{subject}, incorporating: {refined[:100]}"

        return (
            f"Whiteboard animation style video. A hand holding a black marker draws on a clean pure white background. "
            f"The hand sketches {subject}, stroke by stroke. "
            f"Simple black outlines appear first, then bold color fills are added. "
            f"Fast drawing motion with satisfying reveal. "
            f"Vertical 9:16 composition. No real photography, illustrated style only. "
            f"No text overlays, no watermarks, no people."
        )

    # ── Flat Illustration Prompt Builder ─────────────────────────────

    ILLUSTRATION_SCENE_SUBJECTS = {
        1: "an open book with light rays emanating from its pages",
        2: "a split diagram: left side shows chaos, right side shows clarity and order",
        3: "a Venn diagram of two overlapping circles labeled with contrasting ideas",
        4: "a polished infographic showing an upward growth chart with milestone markers",
        5: "a flowchart with decision nodes leading to a bright outcome",
        6: "a 3-step framework diagram with icons and connecting arrows",
        7: "a before/after comparison panel with contrasting visuals",
        8: "a trophy or star with radiating lines, celebration motif",
    }

    def build_illustration_prompt(
        self,
        scene_number: int = 1,
        total_scenes: int = 8,
        visual_cues: str = "",
        book_title: str = "",
    ) -> str:
        """
        Build a 2D flat illustration / diagram animation prompt for a scene.

        Generates polished motion-graphics style clips.
        Best for framework/concept scenes (Scene 4 — Famous Example, Scene 6 — Cheat Code).
        """
        subject = self.ILLUSTRATION_SCENE_SUBJECTS.get(scene_number, "a polished upward-trending diagram")

        if visual_cues:
            refined = _prompt_refiner.refine(visual_cues)
            subject = f"{subject}, theme: {refined[:100]}"

        return (
            f"2D flat illustration animation on a clean white background. "
            f"Smooth motion graphics showing {subject}. "
            f"Clean vector art style, bold outlines, vibrant colors. "
            f"Each element appears with a draw-on animation effect. "
            f"Educational explainer video aesthetic. "
            f"Vertical 9:16 composition. No people, no photography, no text overlays, no watermarks."
        )

    # ── Unified Prompt Dispatcher ─────────────────────────────────────

    def build_prompt(
        self,
        veo_style: str,
        scene_number: int,
        scene_text: str = "",
        visual_cues: str = "",
        book_title: str = "",
        book_author: str = "",
        total_scenes: int = 8,
        content_type: str = "book_review",
    ) -> str:
        """
        Build the right Veo prompt based on style.

        Args:
            veo_style: 'cinematic' | 'whiteboard' | 'illustration'
                       (should be pre-resolved via resolve_scene_style)
        """
        if veo_style == "whiteboard":
            return self.build_whiteboard_prompt(
                scene_number=scene_number,
                total_scenes=total_scenes,
                visual_cues=visual_cues,
                book_title=book_title,
            )
        elif veo_style == "illustration":
            return self.build_illustration_prompt(
                scene_number=scene_number,
                total_scenes=total_scenes,
                visual_cues=visual_cues,
                book_title=book_title,
            )
        else:
            return self.build_scene_prompt(
                scene_text=scene_text,
                visual_cues=visual_cues,
                book_title=book_title,
                book_author=book_author,
                scene_number=scene_number,
                total_scenes=total_scenes,
                content_type=content_type,
            )
