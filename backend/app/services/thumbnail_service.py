"""
Thumbnail generation service for YouTube videos.

Creates professional 1280x720 thumbnails with:
- Title text overlay
- Content type badges
- Background images or gradients
- High readability
"""

import logging
from pathlib import Path
from typing import Optional
from uuid import uuid4
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap

logger = logging.getLogger(__name__)


class ThumbnailService:
    """Service for generating YouTube thumbnails."""
    
    THUMBNAIL_SIZE = (1280, 720)
    OUTPUT_DIR = Path("data/thumbnails")
    
    # Color schemes per content type
    COLOR_SCHEMES = {
        "daily_update": {
            "gradient_start": (255, 107, 53),  # Orange
            "gradient_end": (53, 107, 255),    # Blue
            "badge_color": (255, 193, 7),      # Yellow
            "badge_text": "TODAY"
        },
        "big_tech": {
            "gradient_start": (30, 60, 114),   # Dark blue
            "gradient_end": (42, 82, 152),     # Medium blue
            "badge_color": (0, 150, 136),      # Teal
            "badge_text": "DEEP DIVE"
        },
        "leader_quote": {
            "gradient_start": (156, 39, 176),  # Purple
            "gradient_end": (255, 152, 0),     # Orange
            "badge_color": (255, 193, 7),      # Gold
            "badge_text": "WISDOM"
        },
        "arxiv_paper": {
            "gradient_start": (25, 118, 210),  # Blue
            "gradient_end": (255, 255, 255),   # White
            "badge_color": (76, 175, 80),      # Green
            "badge_text": "RESEARCH"
        }
    }
    
    def __init__(self):
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    def generate_thumbnail(
        self,
        title: str,
        content_type: str = "daily_update",
        background_image: Optional[Path] = None
    ) -> Path:
        """
        Generate YouTube thumbnail.
        
        Args:
            title: Video title (will be word-wrapped)
            content_type: Type of content (daily_update, big_tech, etc.)
            background_image: Optional background image path
            
        Returns:
            Path to generated thumbnail
        """
        logger.info(f"Generating thumbnail for: {title[:50]}...")
        
        # Create base image
        if background_image and background_image.exists():
            img = self._load_background_image(background_image)
        else:
            img = self._create_gradient_background(content_type)
        
        # Add dark overlay for text readability
        img = self._add_overlay(img)
        
        # Add content type badge
        img = self._add_badge(img, content_type)
        
        # Add title text
        img = self._add_title_text(img, title)
        
        # Save
        output_path = self.OUTPUT_DIR / f"thumb_{uuid4().hex[:12]}.jpg"
        img.convert('RGB').save(output_path, 'JPEG', quality=95)
        
        logger.info(f"Thumbnail saved: {output_path}")
        return output_path
    
    def _load_background_image(self, image_path: Path) -> Image.Image:
        """Load and resize background image."""
        img = Image.open(image_path)
        img = img.resize(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        return img.convert('RGBA')
    
    def _create_gradient_background(self, content_type: str) -> Image.Image:
        """Create gradient background based on content type."""
        scheme = self.COLOR_SCHEMES.get(content_type, self.COLOR_SCHEMES["daily_update"])
        
        img = Image.new('RGB', self.THUMBNAIL_SIZE, scheme["gradient_start"])
        draw = ImageDraw.Draw(img)
        
        # Create vertical gradient
        for y in range(self.THUMBNAIL_SIZE[1]):
            ratio = y / self.THUMBNAIL_SIZE[1]
            r = int(scheme["gradient_start"][0] * (1 - ratio) + scheme["gradient_end"][0] * ratio)
            g = int(scheme["gradient_start"][1] * (1 - ratio) + scheme["gradient_end"][1] * ratio)
            b = int(scheme["gradient_start"][2] * (1 - ratio) + scheme["gradient_end"][2] * ratio)
            draw.line([(0, y), (self.THUMBNAIL_SIZE[0], y)], fill=(r, g, b))
        
        return img.convert('RGBA')
    
    def _add_overlay(self, img: Image.Image) -> Image.Image:
        """Add semi-transparent dark overlay for text readability."""
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 140))  # 55% opacity
        return Image.alpha_composite(img, overlay)
    
    def _add_badge(self, img: Image.Image, content_type: str) -> Image.Image:
        """Add content type badge in top-right corner."""
        scheme = self.COLOR_SCHEMES.get(content_type, self.COLOR_SCHEMES["daily_update"])
        draw = ImageDraw.Draw(img)
        
        # Badge dimensions
        badge_text = scheme["badge_text"]
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        except:
            font = ImageFont.load_default()
        
        # Calculate badge size
        bbox = draw.textbbox((0, 0), badge_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        padding = 20
        badge_width = text_width + padding * 2
        badge_height = text_height + padding * 2
        
        # Position in top-right
        x = self.THUMBNAIL_SIZE[0] - badge_width - 40
        y = 40
        
        # Draw rounded rectangle
        draw.rounded_rectangle(
            [(x, y), (x + badge_width, y + badge_height)],
            radius=15,
            fill=scheme["badge_color"]
        )
        
        # Draw text
        text_x = x + padding
        text_y = y + padding
        draw.text((text_x, text_y), badge_text, font=font, fill='white')
        
        return img
    
    def _add_title_text(self, img: Image.Image, title: str) -> Image.Image:
        """Add title text with word wrapping."""
        draw = ImageDraw.Draw(img)
        
        # Load font
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 90)
        except:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 90)
            except:
                font = ImageFont.load_default()
        
        # Word wrap title
        max_width = self.THUMBNAIL_SIZE[0] - 100  # 50px margin each side
        wrapped_lines = self._wrap_text(title, font, max_width, draw)
        
        # Calculate total height
        line_height = 110
        total_height = len(wrapped_lines) * line_height
        
        # Center vertically
        y = (self.THUMBNAIL_SIZE[1] - total_height) // 2
        
        # Draw each line
        for line in wrapped_lines:
            # Get text size for centering
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (self.THUMBNAIL_SIZE[0] - text_width) // 2
            
            # Draw text with outline
            self._draw_text_with_outline(draw, (x, y), line, font)
            y += line_height
        
        return img
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw) -> list:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Limit to 3 lines max
        if len(lines) > 3:
            lines = lines[:3]
            lines[2] = lines[2][:30] + "..."
        
        return lines
    
    def _draw_text_with_outline(self, draw: ImageDraw.Draw, position: tuple, text: str, font: ImageFont.FreeTypeFont):
        """Draw text with black outline for better readability."""
        x, y = position
        
        # Draw outline (black)
        outline_width = 4
        for adj_x in range(-outline_width, outline_width + 1):
            for adj_y in range(-outline_width, outline_width + 1):
                draw.text((x + adj_x, y + adj_y), text, font=font, fill='black')
        
        # Draw main text (white)
        draw.text((x, y), text, font=font, fill='white')


# Test function
def test_thumbnail():
    """Test thumbnail generation."""
    service = ThumbnailService()
    
    test_cases = [
        ("AI Revolutionizes Video Creation! 🤯", "daily_update"),
        ("Google's Gemini 2.0: Deep Dive Analysis", "big_tech"),
        ("Sam Altman on the Future of AGI 💡", "leader_quote"),
        ("New Transformer Architecture Explained 📚", "arxiv_paper"),
    ]
    
    for title, content_type in test_cases:
        path = service.generate_thumbnail(title, content_type)
        print(f"✅ Generated {content_type}: {path}")


if __name__ == "__main__":
    test_thumbnail()
