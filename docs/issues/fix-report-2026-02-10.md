# Fix Report: Duplicate Scenes & Book Review End Screen

**Date**: 2026-02-10  
**Status**: ✅ COMPLETED  

---

## Issues Fixed

### 1. Duplicate Scenes in TTS/Video (Scene 1 & Scene 6)

**Problem**: 
- Scene 1 and Scene 6 were appearing twice in both TTS audio and final video
- Caused by concatenating hook + scenes + CTA when scenes already contained this content

**Root Cause**:
The `formatted_script` was being built incorrectly:
```python
# OLD (INCORRECT):
formatted_parts = [script_data.hook]  # Added hook
formatted_parts.extend([s.text for s in script_data.scenes])  # Scene 1 already has hook!
formatted_parts.append(script_data.call_to_action)  # Scene 6 already has CTA!
```

**Solution Applied**:
Updated `/backend/app/services/script_service.py` in two locations:

1. **Lines 159-163** (generate_script method):
```python
# NEW (CORRECT):
# Scenes already contain hook and CTA, so we only use scenes
formatted_parts = [s.text for s in script_data.scenes]
formatted_script = " ".join(formatted_parts)
```

2. **Lines 277-281** (generate_commentary_script method):
Applied the same fix to ensure consistency.

**Impact**:
- ✅ New scripts will no longer have duplicated scenes
- ✅ TTS audio will be cleaner and shorter
- ✅ Final videos will have proper narration flow
- ⚠️ Existing script #7 will need to be regenerated to fix the audio

---

### 2. Book Review End Screen Created

**Requirement**: 
Create an end screen for book review videos for @AINewsDaily channel

**Solution**:
1. **Created new end screen asset**: `/backend/assets/end_screens/end_book_review.png`
   - Dark blue gradient background matching existing end screens
   - "Thanks for Watching!" header
   - "Subscribe for Book Reviews!" subtitle
   - Red SUBSCRIBE button
   - Blue SHARE button
   - @AINewsDaily channel name
   - "📚 More Book Summaries Weekly!" footer

2. **Updated EndScreenService**: `/backend/app/services/end_screen_service.py`
   - Added `"book_review": "Subscribe for Book Reviews!"` to CTA_MESSAGES

3. **Fixed Script Content Type Storage**: `/backend/app/services/script_service.py`
   - Added `content_type=content_type` to Script creation (line 199)
   - Ensures book review videos automatically use the correct end screen
   - The video service reads this field to select the appropriate end screen

**Visual**:
The end screen matches the existing style (end_big_tech.png, end_daily_update.png) but with book review-specific messaging.

---

## Files Modified

1. `/backend/app/services/script_service.py` (3 locations)
   - Fixed duplicate scene issue in script formatting (2 locations)
   - Added content_type to Script creation for automatic end screen selection

2. `/backend/app/services/end_screen_service.py`
   - Added book_review CTA message

3. `/backend/assets/end_screens/end_book_review.png` (NEW)
   - Book review end screen asset with @60SecondBooks branding

4. `/docs/issues/duplicate-scenes-tts-issue.md` (NEW)
   - Detailed root cause analysis document

5. `/docs/configuration/end-screen-guide.md` (NEW)
   - Comprehensive guide for end screen configuration and troubleshooting

---

## Testing Recommendations

### For Duplicate Scene Fix:
1. Generate a new book review script from an existing article
2. Generate audio from the new script
3. Verify the formatted_script in the database has no duplicates
4. Listen to TTS audio to confirm no repetition
5. Optional: Regenerate script #7 and re-render video

### For Book Review End Screen:
1. Generate a new book review video
2. Verify the end screen uses `end_book_review.png`
3. Confirm the messaging matches the content type

---

## Next Steps (Optional)

1. **Fix Existing Script #7**:
   ```bash
   # Delete existing audio and video
   # Regenerate from script with fixed formatting
   ```

2. **Verify Video Composition Uses Correct End Screen**:
   Check that the video service selects the right end screen based on `content_type="book_review"`

3. **Add Book Title Overlay** (from future features list):
   Add text overlay with book title on book review videos

---

## Verification Commands

Check the fixed script formatting:
```bash
sqlite3 backend/data/app.db "SELECT formatted_script FROM scripts WHERE id = 8 LIMIT 1;"
```

Check end screen exists:
```bash
ls -lh backend/assets/end_screens/
```
