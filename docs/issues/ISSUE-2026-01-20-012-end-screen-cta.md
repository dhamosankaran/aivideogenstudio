# ISSUE-2026-01-20-012: End Screen with CTA

**Created**: 2026-01-20  
**Priority**: High  
**Effort**: 2-3 hours  
**Status**: ✅ Complete

---

## Problem

Videos need a professional end screen asking viewers to subscribe and share. Currently, videos just end abruptly.

**Requirements**:
1. 3-5 second end screen
2. "Subscribe" button/text
3. "Share" button/text  
4. Channel branding (logo/name)
5. Smooth transition from content

---

## Proposed Solution

### Design Options

**Option A: Static Image End Screen**
- Create template image (1080x1920)
- Add as final clip in video composition
- Simple, fast, consistent

**Option B: Animated End Screen**
- Fade in subscribe/share buttons
- Pulse animation on buttons
- More engaging but complex

**Recommendation**: Start with Option A, upgrade to B later

---

## Implementation

```python
# In enhanced_video_service.py

def _create_end_screen(self, duration: float = 4.0) -> ImageClip:
    """Create end screen with subscribe/share CTA."""
    
    # Load or generate end screen template
    end_screen_path = Path("assets/end_screen_template.png")
    
    if not end_screen_path.exists():
        # Generate programmatically with Pillow
        end_screen_path = self._generate_end_screen_template()
    
    # Create clip
    end_clip = ImageClip(str(end_screen_path))
    end_clip = end_clip.set_duration(duration)
    end_clip = end_clip.fadein(0.5)
    
    return end_clip

def _generate_end_screen_template(self) -> Path:
    """Generate end screen template with Pillow."""
    from PIL import Image, ImageDraw, ImageFont
    
    # Create canvas
    img = Image.new('RGB', (1080, 1920), color=(20, 30, 50))
    draw = ImageDraw.Draw(img)
    
    # Add gradient background
    # ... (gradient code)
    
    # Add "Thanks for Watching!" text
    font_large = ImageFont.truetype("Arial-Bold.ttf", 80)
    draw.text((540, 600), "Thanks for Watching!", 
              font=font_large, fill='white', anchor='mm')
    
    # Add subscribe button
    draw.rounded_rectangle(
        [(340, 900), (740, 1000)], 
        radius=20, 
        fill=(255, 0, 0)  # YouTube red
    )
    draw.text((540, 950), "SUBSCRIBE", 
              font=font_large, fill='white', anchor='mm')
    
    # Add share button
    draw.rounded_rectangle(
        [(340, 1100), (740, 1200)], 
        radius=20, 
        fill=(0, 120, 255)  # Blue
    )
    draw.text((540, 1150), "SHARE", 
              font=font_large, fill='white', anchor='mm')
    
    # Add channel name/logo
    font_small = ImageFont.truetype("Arial.ttf", 40)
    draw.text((540, 1400), "@YourChannelName", 
              font=font_small, fill='gray', anchor='mm')
    
    # Save template
    output_path = Path("assets/end_screen_template.png")
    output_path.parent.mkdir(exist_ok=True)
    img.save(output_path)
    
    return output_path
```

### Integration into Video Pipeline

```python
# In _compose_scene_based_video()

# After all scene clips
end_screen = self._create_end_screen(duration=4.0)
end_screen = end_screen.set_start(duration)  # After main content

# Add to final composite
final_video = CompositeVideoClip(
    scene_clips + all_subtitle_clips + [end_screen], 
    size=(w, h)
)
```

---

## Customization Options

Store in database/config:
```python
end_screen_config = {
    "duration": 4.0,
    "channel_name": "@AINewsDaily",
    "background_color": (20, 30, 50),
    "subscribe_color": (255, 0, 0),
    "share_color": (0, 120, 255),
    "show_logo": True,
    "logo_path": "assets/channel_logo.png"
}
```

---

## Database Changes

```python
# Add to Video model
has_end_screen: bool = Column(Boolean, default=True)
end_screen_duration: float = Column(Float, default=4.0)
```

---

## Acceptance Criteria

- [ ] End screen generated for each video
- [ ] 3-5 second duration
- [ ] Subscribe and Share CTAs visible
- [ ] Smooth fade-in transition
- [ ] Channel branding included
- [ ] Customizable via config

---

## Future Enhancements

- [ ] Animated buttons (pulse effect)
- [ ] Click-through tracking (YouTube analytics)
- [ ] A/B test different designs
- [ ] Personalized end screens per topic

---

## Estimated Impact

- **Time**: 2-3 hours
- **Risk**: Low
- **Value**: High (increases subscriber conversion)
- **Industry Standard**: 2-5% conversion rate on end screens
