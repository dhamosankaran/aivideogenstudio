# End Screen Configuration Guide

**Last Updated**: 2026-02-10  
**Status**: ✅ Configured for Book Reviews

---

## Overview

The video composition service automatically selects the appropriate end screen based on the content type. This ensures that each video category has branded CTAs and messaging that match the content.

---

## How It Works

### 1. Content Type Detection
When a script is generated, the system detects the content type from the article:

**File**: `/backend/app/services/script_service.py`
```python
content_type = getattr(article, 'suggested_content_type', '') or ''
is_book_review = content_type == 'book_review'
```

### 2. Content Type Storage
The content type is stored in the Script model during creation:
```python
script = Script(
    ...
    content_type=content_type,  # e.g., "book_review"
    ...
)
```

### 3. End Screen Selection
During video rendering, the content type determines which end screen to use:

**File**: `/backend/app/services/enhanced_video_service.py` (line 371)
```python
content_type = getattr(script, 'content_type', 'daily_update') or 'daily_update'
end_screen_path = self.end_screen_service.generate_end_screen(content_type)
```

---

## Available End Screens

| Content Type | File | Channel | CTA Message |
|--------------|------|---------|-------------|
| `daily_update` | `end_daily_update.png` | @AINewsDaily | "Subscribe for Daily AI News!" |
| `big_tech` | `end_big_tech.png` | @AINewsDaily | "Follow for In-Depth Analysis!" |
| `leader_quote` | `end_leader_quote.png` | @AINewsDaily | "Get Inspired Daily!" |
| `arxiv_paper` | `end_arxiv_paper.png` | @AINewsDaily | "Learn Cutting-Edge AI!" |
| **`book_review`** | **`end_book_review.png`** | **@60SecondBooks** | **"Subscribe for Book Reviews!"** |

---

## Book Review Configuration

### Asset Location
```
/backend/assets/end_screens/end_book_review.png
```

### Design Specifications
- **Resolution**: 1080x1920 (Portrait/Vertical)
- **Background**: Dark blue gradient (#1e2a46 → #2a3a5a)
- **Layout**:
  - "Thanks for Watching!" (large white text, 600px from top)
  - "Subscribe for Book Reviews!" (light gray, 750px from top)
  - Red SUBSCRIBE button (900px from top)
  - Blue SHARE button (1100px from top)
  - "@60SecondBooks" channel name (gray, 1400px from top)
  - "📚 More Book Summaries Weekly!" (dark gray, 1550px from top)

### Automatic Selection
✅ All videos generated from articles with `suggested_content_type="book_review"` will automatically use `end_book_review.png`

---

## How Book Reviews Are Identified

The system identifies book reviews during article analysis:

1. **Book Source Detection**: Articles imported from the Books API have `source_type="book"`
2. **Content Analysis**: The LLM analyzer sets `suggested_content_type="book_review"` 
3. **Script Generation**: Uses specialized book review prompt (60s format, 6 scenes)
4. **Video Rendering**: Automatically selects `end_book_review.png`

---

## Testing the Configuration

### Generate a New Book Review Video
1. Import a book from the Books interface
2. Generate script (will use book review prompt)
3. Generate audio
4. Generate video
5. ✅ Video should end with `end_book_review.png` showing "@60SecondBooks"

### Verify Content Type
```bash
# Check script content type
sqlite3 backend/data/app.db "SELECT id, catchy_title, content_type FROM scripts WHERE id = X;"
```

Expected output for book reviews:
```
7|How to Change Your Life 1% at a Time 📈|book_review
```

---

## Troubleshooting

### Video Uses Wrong End Screen

**Problem**: Book review video shows @AINewsDaily instead of @60SecondBooks

**Solutions**:
1. Check script content_type:
   ```sql
   SELECT content_type FROM scripts WHERE id = X;
   ```
2. If NULL or incorrect, update manually:
   ```sql
   UPDATE scripts SET content_type = 'book_review' WHERE id = X;
   ```
3. Regenerate the video

### End Screen Not Found

**Problem**: Error: `FileNotFoundError: end_book_review.png`

**Solution**: Regenerate the end screen:
```bash
cd backend && source venv/bin/activate
cd ..
python3 -c "
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
# (full script from generate_book_endscreen.py)
"
```

---

## Adding New End Screens

To add a new content type with custom end screen:

1. **Create the end screen image**:
   ```bash
   # Add to: /backend/assets/end_screens/end_YOUR_TYPE.png
   ```

2. **Update EndScreenService**:
   ```python
   # File: /backend/app/services/end_screen_service.py
   CTA_MESSAGES = {
       ...
       "your_type": "Your Custom CTA Message!"
   }
   ```

3. **Set content type in articles**:
   ```python
   article.suggested_content_type = "your_type"
   ```

4. Done! Videos will automatically use the new end screen.

---

## Related Files

- `/backend/app/services/end_screen_service.py` - End screen generation service
- `/backend/app/services/enhanced_video_service.py` - Video composition (uses end screens)
- `/backend/app/services/script_service.py` - Sets content_type during script generation
- `/backend/assets/end_screens/` - End screen image assets
- `/backend/app/prompts/__init__.py` - Content type specific prompts

---

## Summary

✅ **Book review videos will automatically use the @60SecondBooks end screen**

The system flow is:
```
Book Article → Script (content_type="book_review") → Video → end_book_review.png
```

No manual configuration needed for each video. It's fully automatic!
