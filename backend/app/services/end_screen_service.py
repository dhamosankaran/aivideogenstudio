"""
End screen generation service for YouTube videos.

Creates 4-second end screens with:
- Subscribe/Share CTAs
- Content-type specific messaging
- Channel branding
- Professional design

CTA / channel / footer configuration is driven by the central
content_types registry.
"""

import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from app.content_types import CONTENT_TYPES, get_registry

logger = logging.getLogger(__name__)


class EndScreenService:
    """Service for generating video end screens."""

    # Supported aspect ratios → (width, height)
    ASPECT_SIZES = {
        "9:16": (1080, 1920),   # Shorts / Reels (default)
        "16:9": (1920, 1080),   # YouTube landscape
        "1:1":  (1080, 1080),   # Instagram square
    }
    OUTPUT_DIR = Path("assets/end_screens")

    def __init__(self):
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def generate_end_screen(
        self,
        content_type: str = "daily_update",
        channel_name: str = None,
        aspect_ratio: str = "9:16",
        force_regenerate: bool = False,
    ) -> Path:
        """
        Generate (or return cached) end screen for the given content type and aspect ratio.

        Cache key: end_{content_type}_{ar_tag}.png  e.g. end_daily_update_9x16.png
        Each (content_type, aspect_ratio) pair is generated once and reused.

        Args:
            content_type: Content type for customised CTA/channel branding
            channel_name: Override channel name (defaults to registry value)
            aspect_ratio: "9:16" | "16:9" | "1:1"
            force_regenerate: Bypass cache and rebuild

        Returns:
            Path to the generated PNG
        """
        if channel_name is None:
            channel_name = get_registry(content_type)["channel"]

        # Normalise aspect_ratio and resolve dimensions
        ar = aspect_ratio if aspect_ratio in self.ASPECT_SIZES else "9:16"
        screen_size = self.ASPECT_SIZES[ar]
        ar_tag = ar.replace(":", "x")  # "9:16" → "9x16"

        logger.info(f"Generating end screen for {content_type} @ {ar} (channel: {channel_name})")

        # Check cache — one file per (content_type, aspect_ratio)
        output_path = self.OUTPUT_DIR / f"end_{content_type}_{ar_tag}.png"
        if output_path.exists() and not force_regenerate:
            logger.info(f"Using cached end screen: {output_path}")
            return output_path
        if output_path.exists() and force_regenerate:
            output_path.unlink()
            logger.info(f"Force-regenerating end screen: {output_path}")

        # Create canvas with gradient background
        w, h = screen_size
        img = self._create_background(screen_size)
        draw = ImageDraw.Draw(img)

        # All sizing off min(w,h) so nothing overflows on landscape or square
        base = min(w, h)
        sz_large  = max(32, int(base * 0.065))   # ~70px at 1080
        sz_medium = max(24, int(base * 0.046))   # ~50px at 1080
        sz_small  = max(18, int(base * 0.030))   # ~32px at 1080

        try:
            font_large  = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", sz_large)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", sz_medium)
            font_small  = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", sz_small)
        except Exception:
            font_large = font_medium = font_small = ImageFont.load_default()

        # Fixed element sizes (relative to base, so they never overflow)
        btn_w  = int(base * 0.37)     # ~400px at 1080
        btn_h  = int(base * 0.08)     # ~86px  at 1080
        gap_sm = int(base * 0.025)    # ~27px  — between title and CTA
        gap_md = int(base * 0.04)     # ~43px  — between CTA and buttons
        gap_btn= int(base * 0.03)     # ~32px  — between the two buttons
        gap_lg = int(base * 0.05)     # ~54px  — between buttons and channel

        # Measure actual text heights
        def text_h(font):
            bb = draw.textbbox((0, 0), "Ag", font=font)
            return bb[3] - bb[1]

        th_large = text_h(font_large)
        th_small = text_h(font_small)

        # Total block height → center it vertically
        total_block = (
            th_large           # "Thanks for Watching!"
            + gap_sm
            + th_small         # CTA line
            + gap_md
            + btn_h            # SUBSCRIBE button
            + gap_btn
            + btn_h            # SHARE button
            + gap_lg
            + th_small         # channel name
            + gap_sm
            + th_small         # footer
        )
        y = (h - total_block) // 2   # top of the vertically-centred block

        cta_text    = get_registry(content_type)["cta"]
        footer_text = get_registry(content_type)["footer"]

        self._draw_centered_text(draw, y, "Thanks for Watching!", font_large, 'white', w)
        y += th_large + gap_sm

        self._draw_centered_text(draw, y, cta_text, font_small, 'lightgray', w)
        y += th_small + gap_md

        self._draw_button(draw, y, "SUBSCRIBE", (220, 30, 30), font_medium, w, btn_w, btn_h)
        y += btn_h + gap_btn

        self._draw_button(draw, y, "SHARE", (30, 100, 230), font_medium, w, btn_w, btn_h)
        y += btn_h + gap_lg

        self._draw_centered_text(draw, y, channel_name, font_small, (170, 190, 220), w)
        y += th_small + gap_sm

        self._draw_centered_text(draw, y, footer_text, font_small, (110, 130, 160), w)

        img.save(output_path)
        logger.info(f"End screen saved: {output_path}")
        return output_path

    def prebuild_all(self, force: bool = False) -> dict:
        """
        Pre-generate end screens for every registered content type × aspect ratio.
        Call once at startup or via admin endpoint.

        Returns a summary dict: {content_type: {aspect_ratio: path_str | error_str}}
        """
        results = {}
        for ct in CONTENT_TYPES:
            results[ct] = {}
            for ar in self.ASPECT_SIZES:
                try:
                    path = self.generate_end_screen(ct, aspect_ratio=ar, force_regenerate=force)
                    results[ct][ar] = str(path)
                    logger.info(f"[prebuild] {ct} @ {ar} → {path}")
                except Exception as e:
                    results[ct][ar] = f"ERROR: {e}"
                    logger.error(f"[prebuild] {ct} @ {ar} failed: {e}")
        return results

    def get_cached_path(self, content_type: str, aspect_ratio: str = "9:16") -> Path | None:
        """
        Return the cached end screen path if it exists, None otherwise.
        Use this for zero-cost lookups in hot paths.
        """
        ar = aspect_ratio if aspect_ratio in self.ASPECT_SIZES else "9:16"
        ar_tag = ar.replace(":", "x")
        path = self.OUTPUT_DIR / f"end_{content_type}_{ar_tag}.png"
        return path if path.exists() else None

    def _create_background(self, screen_size: tuple) -> Image.Image:
        """Create gradient background for the given dimensions."""
        w, h = screen_size
        img = Image.new('RGB', screen_size, (20, 30, 50))
        draw = ImageDraw.Draw(img)
        for y in range(h):
            ratio = y / h
            r = int(20 * (1 - ratio) + 30 * ratio)
            g = int(30 * (1 - ratio) + 40 * ratio)
            b = int(50 * (1 - ratio) + 70 * ratio)
            draw.line([(0, y), (w, y)], fill=(r, g, b))
        return img

    def _draw_centered_text(self, draw: ImageDraw.Draw, y: int, text: str, font, color: str, canvas_width: int):
        """Draw horizontally centred text at the given y position."""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (canvas_width - text_width) // 2
        draw.text((x, y), text, font=font, fill=color)

    def _draw_button(self, draw: ImageDraw.Draw, y: int, text: str, color: tuple, font,
                     canvas_width: int, button_width: int = None, button_height: int = None):
        """Draw a rounded rectangle button centred horizontally."""
        if button_width is None:
            button_width = int(canvas_width * 0.37)
        if button_height is None:
            button_height = int(canvas_width * 0.08)
        x = (canvas_width - button_width) // 2

        draw.rounded_rectangle(
            [(x, y), (x + button_width, y + button_height)],
            radius=int(button_height * 0.25),
            fill=color,
        )

        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text(
            (x + (button_width - text_w) // 2, y + (button_height - text_h) // 2),
            text, font=font, fill='white',
        )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pre-build all end screen images")
    parser.add_argument("--force", action="store_true", help="Regenerate even if files already exist")
    args = parser.parse_args()

    service = EndScreenService()
    results = service.prebuild_all(force=args.force)

    print(f"\n{'─'*60}")
    print(f"  End Screen Pre-build {'(forced)' if args.force else '(skip existing)'}")
    print(f"{'─'*60}")
    for ct, ar_map in results.items():
        for ar, result in ar_map.items():
            status = "✅" if not result.startswith("ERROR") else "❌"
            print(f"  {status}  {ct:20s}  {ar}  →  {result}")
    print(f"{'─'*60}\n")
