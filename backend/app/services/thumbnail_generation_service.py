"""
AI Thumbnail Generation Service.

Uses Gemini 2.0 Flash (NanaBanana) for generating engaging YouTube Shorts thumbnails.
"""

import logging
import os
import base64
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ThumbnailGenerationService:
    """Service for generating AI thumbnails using Gemini's image generation."""
    
    THUMBNAIL_DIR = Path("data/thumbnails")
    
    def __init__(self):
        """Initialize with Gemini client."""
        from dotenv import load_dotenv
        load_dotenv()
        
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found")
        
        self.THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialize Gemini client
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            # Use Gemini 2.0 Flash for image generation (NanaBanana)
            self.model = genai.GenerativeModel("gemini-2.0-flash-exp-image-generation")
            logger.info("✓ Gemini 2.0 Flash Image Generation initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Gemini image generation: {e}")
            self.model = None
    
    def get_thumbnail_prompt(
        self,
        article_title: str,
        article_description: str,
        content_type: str = "daily_update",
        style: str = "vibrant"
    ) -> str:
        """
        Get the thumbnail prompt without generating.
        
        Useful for preview/editing before generation.
        """
        return self._build_thumbnail_prompt(
            article_title,
            article_description,
            content_type,
            style
        )
    
    async def generate_thumbnail(
        self,
        article_title: str,
        article_description: str,
        content_type: str = "daily_update",
        style: str = "vibrant",
        custom_prompt: str = None
    ) -> Optional[Path]:
        """
        Generate an AI thumbnail for a YouTube Short.
        
        Args:
            article_title: Title of the article/video
            article_description: Brief description for context
            content_type: Type of content for style hints
            style: Visual style (vibrant, dark, minimal, tech)
            custom_prompt: If provided, use this prompt instead of auto-generated
            
        Returns:
            Path to generated thumbnail, or None if failed
        """
        if not self.model:
            logger.error("Gemini image generation not available")
            return None
        
        # Use custom prompt or build one
        prompt = custom_prompt if custom_prompt else self._build_thumbnail_prompt(
            article_title, 
            article_description, 
            content_type, 
            style
        )
        
        try:
            logger.info(f"Generating thumbnail for: {article_title[:50]}...")
            
            # Generate image
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "response_modalities": ["image", "text"],
                    "response_mime_type": "image/png"
                }
            )
            
            # Extract image from response
            image_data = None
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_data = part.inline_data.data
                    break
            
            if not image_data:
                logger.warning("No image data in response")
                return None
            
            # Save thumbnail
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in article_title[:30] if c.isalnum() or c == " ").strip().replace(" ", "_")
            filename = f"thumb_{safe_title}_{timestamp}.png"
            output_path = self.THUMBNAIL_DIR / filename
            
            # Decode and save
            if isinstance(image_data, str):
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data
                
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            
            logger.info(f"Thumbnail saved: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            return None
    
    def _build_thumbnail_prompt(
        self,
        title: str,
        description: str,
        content_type: str,
        style: str
    ) -> str:
        """Build an optimized prompt for thumbnail generation."""
        
        # Style guides based on content type
        style_guides = {
            "daily_update": "Modern tech aesthetic with blue/purple gradients, clean typography space",
            "big_tech": "Bold corporate tech feel with company colors, dramatic lighting",
            "leader_wisdom": "Professional portrait style with warm tones, inspirational feel",
            "startup_spotlight": "Innovative startup vibe with fresh greens/oranges, dynamic composition",
            "research_recap": "Scientific and analytical with charts/graphs aesthetic, blues and whites"
        }
        
        visual_style = style_guides.get(content_type, style_guides["daily_update"])
        
        return f"""Create a stunning YouTube Shorts thumbnail (9:16 vertical aspect ratio).

**Topic**: {title}
**Context**: {description[:200]}

**Visual Requirements**:
- Vertical format (1080x1920 pixels, 9:16 ratio)
- Eye-catching, scroll-stopping design
- {visual_style}
- Bold, readable text overlay space at top or center
- High contrast for mobile viewing
- NO text in the image - leave space for text overlays
- Professional, high-quality aesthetic
- Vibrant colors that pop on mobile
- Related imagery to the topic (tech, AI, data, {title.split()[0]} themed)

**Style**: {style}, modern, engaging, suitable for YouTube Shorts

Generate a visually striking thumbnail that would make viewers want to click."""
    
    def get_thumbnail_path(self, video_id: int) -> Optional[Path]:
        """Get existing thumbnail for a video if it exists."""
        pattern = f"thumb_*_{video_id}_*.png"
        matches = list(self.THUMBNAIL_DIR.glob(pattern))
        return matches[0] if matches else None


# Convenience function for testing
async def test_thumbnail_generation():
    """Test thumbnail generation."""
    service = ThumbnailGenerationService()
    
    result = await service.generate_thumbnail(
        article_title="Why Elon Musk wants to put AI data centres in space",
        article_description="Elon Musk believes space-based AI data centres can slash power and cooling costs.",
        content_type="big_tech"
    )
    
    if result:
        print(f"✅ Thumbnail generated: {result}")
        print(f"   Size: {result.stat().st_size / 1024:.1f} KB")
    else:
        print("❌ Thumbnail generation failed")
    
    return result


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_thumbnail_generation())
