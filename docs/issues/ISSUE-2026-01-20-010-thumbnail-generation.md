# ISSUE-2026-01-20-010: Thumbnail Generation

**Created**: 2026-01-20  
**Priority**: High  
**Effort**: 2-3 hours  
**Status**: Open

---

## Problem

Videos need eye-catching thumbnails for YouTube/social media. Currently, no thumbnail is generated.

**Requirements**:
1. Visually appealing design
2. Includes video title (or catchy variant)
3. Consistent branding
4. 1280x720 resolution (YouTube standard)

---

## Proposed Solution

### Option A: Static Template with Text Overlay
Use Pillow to create thumbnail from template:

```python
# app/services/thumbnail_service.py

from PIL import Image, ImageDraw, ImageFont

def generate_thumbnail(
    title: str,
    background_image: Path,
    output_path: Path
) -> Path:
    """Generate YouTube thumbnail."""
    
    # Load background (first scene image or template)
    img = Image.open(background_image)
    img = img.resize((1280, 720))
    
    # Add dark overlay for text readability
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 128))
    img = Image.alpha_composite(img.convert('RGBA'), overlay)
    
    # Add title text
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("Arial-Bold.ttf", 72)
    
    # Word wrap title
    wrapped_title = wrap_text(title, font, 1200)
    
    # Draw text with outline
    draw.text((640, 360), wrapped_title, 
              font=font, fill='white', 
              stroke_width=4, stroke_fill='black',
              anchor='mm')
    
    # Save
    img.convert('RGB').save(output_path, 'JPEG', quality=95)
    return output_path
```

### Option B: Use First Scene Frame
Extract frame from video at 2-3 seconds and add title overlay.

**Recommendation**: Option A (more control, better quality)

---

## Implementation Plan

1. Create `ThumbnailService`
2. Add to video generation pipeline
3. Store thumbnail path in Video model
4. Add download endpoint: `/api/video/{id}/thumbnail`

---

## Database Changes

```python
# Add to Video model
thumbnail_path: Optional[str] = Column(String, nullable=True)
```

---

## Acceptance Criteria

- [ ] Thumbnail generated for each video
- [ ] 1280x720 resolution
- [ ] Title overlaid with good readability
- [ ] Stored in `data/thumbnails/`
- [ ] Downloadable via API

---

## Estimated Impact

- **Time**: 2-3 hours
- **Risk**: Low
- **Value**: High (essential for YouTube publishing)
