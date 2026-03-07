"""
Gemini Image Generation Service.

Uses Google's Gemini 3.1 Flash model to generate AI images from text prompts.
Designed for book review videos where stock photos are often generic for abstract concepts.

Requires:
    pip install google-genai Pillow
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PromptRefiner:
    """Translates abstract psychological/book concepts into vivid visual metaphors.

    Heuristic keyword mapping — zero extra LLM cost.
    Unknown concepts pass through unchanged (identity fallback).
    """

    METAPHOR_MAP = {
        "loss aversion": "person staring at a broken piggy bank with intense regret, dramatic shadows",
        "compounding": "towering stack of gold coins gleaming in warm morning light, dramatic scale",
        "atomic habits": "tiny seed cracking through concrete, sprouting green shoot, macro photography",
        "identity": "person gazing at own reflection in a rain-soaked window, cinematic blue tones",
        "motivation": "lone runner sprinting toward a sunrise on an empty road, long lens compression",
        "procrastination": "person frozen at a desk surrounded by clocks, time-lapse blur effect",
        "fear": "silhouette standing at edge of cliff looking into vast misty valley, dramatic fog",
        "success": "climber reaching mountain summit, arms raised, golden hour light",
        "failure": "chess pieces scattered on floor after knocked-over board, shallow depth of field",
        "wealth": "old library with towering bookshelves, warm amber light, dust motes",
        "discipline": "athlete training alone in an empty gym before dawn, harsh fluorescent lighting",
        "mindset": "butterfly emerging from cocoon in extreme close-up, macro lens, vibrant colors",
        "decision": "fork in a misty forest road, cinematic color grade, leading lines",
        "time": "hourglass with golden sand, shallow depth of field, dark moody background",
        "power": "hand holding a glowing ember in darkness, bokeh background",
    }

    def refine(self, concept: str) -> str:
        """Return vivid visual metaphor if concept matches a known pattern, else return as-is."""
        lower = concept.lower()
        for key, metaphor in self.METAPHOR_MAP.items():
            if key in lower:
                return metaphor
        return concept


_prompt_refiner = PromptRefiner()


class GeminiImageService:
    """
    Service for generating images using Gemini's image generation API.
    
    Uses the new google-genai SDK (separate from google-generativeai).
    """
    
    MODEL = "gemini-3.1-flash-image-preview"
    DEFAULT_ASPECT_RATIO = "9:16"   # Vertical for YouTube Shorts
    DEFAULT_RESOLUTION = "1K"       # 768x1376 for 9:16
    
    def __init__(self):
        """Initialize with Google API key."""
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._client = None
        
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"✓ Gemini Image Service initialized (model={self.MODEL})")
            except ImportError:
                logger.warning("google-genai package not installed. Run: pip install google-genai")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini Image client: {e}")
    
    @property
    def is_available(self) -> bool:
        """Check if the service is ready to generate images."""
        return self._client is not None
    
    async def generate_image(
        self,
        prompt: str,
        output_path: Path,
        aspect_ratio: str = None,
        resolution: str = None
    ) -> Optional[Path]:
        """
        Generate an image from a text prompt and save it.
        
        Args:
            prompt: Text description of the image to generate
            output_path: Path to save the generated image
            aspect_ratio: Aspect ratio (default: 9:16 for vertical video)
            resolution: Image resolution (default: 1K)
            
        Returns:
            Path to saved image, or None if generation failed
        """
        if not self.is_available:
            logger.warning("[GeminiImage] Service not available")
            return None
        
        aspect_ratio = aspect_ratio or self.DEFAULT_ASPECT_RATIO
        resolution = resolution or self.DEFAULT_RESOLUTION
        
        logger.info(f"[GeminiImage] Generating image ({aspect_ratio}, {resolution})")
        logger.debug(f"[GeminiImage] Prompt: {prompt[:150]}...")
        
        try:
            # Run the sync API call in a thread to avoid blocking
            result = await asyncio.to_thread(
                self._generate_sync,
                prompt,
                output_path,
                aspect_ratio,
                resolution
            )
            return result
        except Exception as e:
            logger.error(f"[GeminiImage] Generation failed: {type(e).__name__}: {e}")
            return None
    
    def _generate_sync(
        self,
        prompt: str,
        output_path: Path,
        aspect_ratio: str,
        resolution: str
    ) -> Optional[Path]:
        """Synchronous image generation (called via asyncio.to_thread)."""
        from google.genai import types
        
        response = self._client.models.generate_content(
            model=self.MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE'],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=resolution
                ),
            )
        )
        
        # Extract and save image from response
        for part in response.parts:
            if image := part.as_image():
                output_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(str(output_path))
                
                # Log dimensions via PIL
                try:
                    from PIL import Image
                    pil_img = Image.open(str(output_path))
                    logger.info(
                        f"[GeminiImage] Saved: {output_path.name} "
                        f"({pil_img.size[0]}x{pil_img.size[1]})"
                    )
                except Exception:
                    logger.info(f"[GeminiImage] Saved: {output_path.name}")
                
                return output_path
            elif part.text:
                logger.info(f"[GeminiImage] Model text: {part.text[:100]}")
        
        logger.warning("[GeminiImage] No image in response")
        return None
    
    # ── Cinematic Quality Suffix (appended to every prompt) ──
    CINEMATIC_SUFFIX = (
        "8k resolution, cinematic lighting, shallow depth of field, "
        "high-contrast, hyper-realistic"
    )
    
    def build_scene_prompt(
        self,
        scene_text: str,
        visual_cues: str,
        book_title: str,
        book_author: str,
        scene_number: int,
        total_scenes: int
    ) -> str:
        """
        Build a rich, cinematic prompt from scene context using the
        Visual Metaphor Formula:
        
        [Relatable Subject] + [Specific Action/Emotion] + [Environment]
        + [Cinematic Lighting] + [Depth Modifiers]
        
        Args:
            scene_text: The spoken narration for this scene
            visual_cues: Description of visuals from the script
            book_title: Title of the book being reviewed
            book_author: Author of the book
            scene_number: Current scene number (1-indexed)
            total_scenes: Total number of scenes
            
        Returns:
            A detailed image generation prompt with cinematic suffix
        """
        # Determine scene role for style guidance
        if scene_number == 1:
            scene_role = "opening hook — dramatic, attention-grabbing"
        elif scene_number == total_scenes:
            scene_role = "closing scene — warm, inspiring, call-to-action"
        elif scene_number <= total_scenes // 3:
            scene_role = "early scene — setting context, building intrigue"
        elif scene_number <= 2 * total_scenes // 3:
            scene_role = "mid scene — key insight, climactic moment"
        else:
            scene_role = "late scene — reflection, transformation"
        
        # ── Visual Metaphor Formula ──
        # [Relatable Subject] + [Specific Action/Emotion] + [Environment]
        # + [Cinematic Lighting] + [Depth Modifiers]
        
        prompt_parts = [
            f"Create a cinematic, photorealistic image for a book review video.",
            f"",
            f"BOOK: \"{book_title}\" by {book_author}",
            f"SCENE: {scene_number} of {total_scenes} ({scene_role})",
            f"",
        ]
        
        # Primary visual direction — refine abstract concepts into vivid visual metaphors
        if visual_cues:
            refined_cues = _prompt_refiner.refine(visual_cues)
            prompt_parts.append(f"VISUAL METAPHOR: {refined_cues}")
        
        # Add narration context for emotional grounding
        if scene_text:
            context = scene_text[:150].rsplit(' ', 1)[0] if len(scene_text) > 150 else scene_text
            prompt_parts.append(f"NARRATION CONTEXT: {context}")
        
        # ── Tactile Book Grounding (30% Rule) ──
        # Ensure the physical book is rendered in scenes 1, 4, and 7 (or last)
        # for at least ~30% of a 7-8 scene video
        book_grounding_scenes = {1, 4, 7} if total_scenes >= 7 else {1, total_scenes}
        if scene_number in book_grounding_scenes:
            prompt_parts.extend([
                "",
                f"BOOK GROUNDING: The physical book \"{book_title}\" MUST be visible in this image.",
                "Show it held in hands, resting on a surface, or prominently placed in frame.",
            ])
        
        # ── Visual Metaphor Formula Structure ──
        prompt_parts.extend([
            "",
            "COMPOSITION FORMULA (follow this structure):",
            "- SUBJECT: A relatable human or object relevant to the narration",
            "- ACTION/EMOTION: A specific gesture, expression, or movement",
            "- ENVIRONMENT: A grounded, real-world setting (not abstract)",
            "- LIGHTING: Cinematic (golden hour, dramatic rim light, soft morning glow)",
            "- DEPTH: Shallow depth of field with foreground/background separation",
            "",
            "STYLE REQUIREMENTS:",
            "- Photorealistic with cinematic lighting",
            "- Rich color palette, high contrast, professional photography look",
            "- Vertical composition (9:16 aspect ratio for mobile viewing)",
            "- No text, no watermarks, no UI elements in the image",
            "- Evoke emotion and curiosity — this is a YouTube Shorts background",
        ])
        
        # Assemble and append the cinematic quality suffix
        base_prompt = "\n".join(prompt_parts)
        return f"{base_prompt}\n\n{self.CINEMATIC_SUFFIX}"

