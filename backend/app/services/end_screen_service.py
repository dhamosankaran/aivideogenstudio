"""
End screen generation service for YouTube videos.

Creates 4-second end screens with:
- Subscribe/Share CTAs
- Content-type specific messaging
- Channel branding
- Professional design
"""

import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class EndScreenService:
    """Service for generating video end screens."""
    
    SCREEN_SIZE = (1080, 1920)  # Vertical video format
    OUTPUT_DIR = Path("assets/end_screens")
    
    # Content-type specific CTAs
    CTA_MESSAGES = {
        "daily_update": "Subscribe for Daily AI News!",
        "big_tech": "Follow for In-Depth Analysis!",
        "leader_quote": "Get Inspired Daily!",
        "arxiv_paper": "Learn Cutting-Edge AI!",
        "book_review": "Subscribe for Book Reviews!",
        "youtube_import": "Subscribe for More Insights!"
    }
    
    # Content-type to channel name mapping
    CHANNEL_NAMES = {
        "daily_update": "@AINewsDaily",
        "big_tech": "@AINewsDaily",
        "leader_quote": "@AINewsDaily",
        "arxiv_paper": "@AINewsDaily",
        "book_review": "@60SecondBooks",
        "youtube_import": "@AINewsDaily",
    }
    
    # Content-type specific footer messages
    FOOTER_MESSAGES = {
        "daily_update": "🔔 Turn on notifications!",
        "big_tech": "🔔 Turn on notifications!",
        "leader_quote": "💡 Daily Wisdom Awaits!",
        "arxiv_paper": "🧠 Stay Ahead of AI Research!",
        "book_review": "📚 More Book Summaries Weekly!",
        "youtube_import": "🔔 Turn on notifications!",
    }
    
    def __init__(self):
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    def generate_end_screen(
        self,
        content_type: str = "daily_update",
        channel_name: str = None,
        force_regenerate: bool = False
    ) -> Path:
        """
        Generate end screen template.
        
        Args:
            content_type: Type of content for customized CTA
            channel_name: Channel name to display
            force_regenerate: If True, regenerate even if cached file exists
            
        Returns:
            Path to generated end screen
        """
        # Auto-select channel name based on content type if not explicitly provided
        if channel_name is None:
            channel_name = self.CHANNEL_NAMES.get(content_type, "@AINewsDaily")
        
        logger.info(f"Generating end screen for {content_type} (channel: {channel_name})")
        
        # Check if already exists (reuse templates)
        output_path = self.OUTPUT_DIR / f"end_{content_type}.png"
        if output_path.exists() and not force_regenerate:
            logger.info(f"Using existing end screen: {output_path}")
            return output_path
        elif output_path.exists() and force_regenerate:
            output_path.unlink()
            logger.info(f"Force regenerating end screen: {output_path}")
        
        # Create canvas with gradient background
        img = self._create_background()
        draw = ImageDraw.Draw(img)
        
        # Load fonts
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        except:
            try:
                font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
                font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
                font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
            except:
                font_large = font_medium = font_small = ImageFont.load_default()
        
        # Add "Thanks for Watching!"
        self._draw_centered_text(draw, 600, "Thanks for Watching!", font_large, 'white')
        
        # Add content-specific CTA
        cta_text = self.CTA_MESSAGES.get(content_type, self.CTA_MESSAGES["daily_update"])
        self._draw_centered_text(draw, 750, cta_text, font_small, 'lightgray')
        
        # Add Subscribe button
        self._draw_button(draw, 900, "SUBSCRIBE", (255, 0, 0), font_medium)
        
        # Add Share button
        self._draw_button(draw, 1100, "SHARE", (0, 120, 255), font_medium)
        
        # Add channel name
        self._draw_centered_text(draw, 1400, channel_name, font_small, 'gray')
        
        # Add content-type-specific footer text
        footer_text = self.FOOTER_MESSAGES.get(content_type, "🔔 Turn on notifications!")
        self._draw_centered_text(draw, 1550, footer_text, font_small, 'darkgray')
        
        # Save
        img.save(output_path)
        logger.info(f"End screen saved: {output_path}")
        
        return output_path
    
    def _create_background(self) -> Image.Image:
        """Create gradient background."""
        img = Image.new('RGB', self.SCREEN_SIZE, (20, 30, 50))
        draw = ImageDraw.Draw(img)
        
        # Create subtle vertical gradient
        for y in range(self.SCREEN_SIZE[1]):
            ratio = y / self.SCREEN_SIZE[1]
            r = int(20 * (1 - ratio) + 30 * ratio)
            g = int(30 * (1 - ratio) + 40 * ratio)
            b = int(50 * (1 - ratio) + 70 * ratio)
            draw.line([(0, y), (self.SCREEN_SIZE[0], y)], fill=(r, g, b))
        
        return img
    
    def _draw_centered_text(self, draw: ImageDraw.Draw, y: int, text: str, font: ImageFont.FreeTypeFont, color: str):
        """Draw centered text at given y position."""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.SCREEN_SIZE[0] - text_width) // 2
        draw.text((x, y), text, font=font, fill=color)
    
    def _draw_button(self, draw: ImageDraw.Draw, y: int, text: str, color: tuple, font: ImageFont.FreeTypeFont):
        """Draw rounded button with text."""
        # Button dimensions
        button_width = 400
        button_height = 100
        x = (self.SCREEN_SIZE[0] - button_width) // 2
        
        # Draw rounded rectangle
        draw.rounded_rectangle(
            [(x, y), (x + button_width, y + button_height)],
            radius=20,
            fill=color
        )
        
        # Draw text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = x + (button_width - text_width) // 2
        text_y = y + (button_height - text_height) // 2
        draw.text((text_x, text_y), text, font=font, fill='white')


# Test function
def test_end_screen():
    """Test end screen generation."""
    service = EndScreenService()
    
    for content_type in ["daily_update", "big_tech", "leader_quote", "arxiv_paper"]:
        path = service.generate_end_screen(content_type)
        print(f"✅ Generated {content_type}: {path}")


if __name__ == "__main__":
    test_end_screen()
