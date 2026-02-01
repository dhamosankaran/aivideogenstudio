# NotebookLM-Style Video Generation - Exploration

**Date**: 2026-01-19  
**Status**: Planning  
**Goal**: Build video generation similar to NotebookLM's "Audio Overview" feature

---

## 🎯 What is NotebookLM Video Style?

NotebookLM's "Audio Overview" creates engaging videos with:
1. **Natural conversational audio** (podcast-style, often 2 speakers)
2. **Synchronized visuals** - Images/graphics that match the audio content
3. **Smooth transitions** - Fade, zoom, pan effects
4. **Captions/subtitles** - Word-level or phrase-level sync
5. **Professional pacing** - Not too fast, not too slow

---

## 🔍 Current System vs. Target

### Current (MVP)
```
Audio: ✅ Google TTS (single voice)
Video: ⚠️ Simple text overlays
       - Even word distribution
       - Gradient background
       - No images
       - Basic timing
```

### Target (NotebookLM-Style)
```
Audio: ✅ Google TTS (can add multi-voice later)
Video: 🎯 Enhanced composition
       - Relevant images per segment
       - Smooth transitions
       - Word-level subtitle sync
       - Scene-based structure
```

---

## 🏗️ Architecture Changes Needed

### 1. Script Generation Enhancement
**Current**: Single text block  
**Target**: Structured scenes with metadata

```json
{
  "script_id": 123,
  "scenes": [
    {
      "scene_number": 1,
      "duration": 15.0,
      "text": "AI is revolutionizing video generation...",
      "image_keywords": ["artificial intelligence", "video editing", "technology"],
      "visual_style": "tech_modern",
      "transition": "fade"
    },
    {
      "scene_number": 2,
      "duration": 12.0,
      "text": "Companies like OpenAI and Google...",
      "image_keywords": ["openai logo", "google ai", "tech companies"],
      "visual_style": "corporate",
      "transition": "zoom"
    }
  ]
}
```

### 2. Image Integration
**Options**:
- **Pexels API** (free, 200 req/hour)
- **Unsplash API** (free, 50 req/hour)
- **Google Custom Search** (100 free/day)

**Recommendation**: Start with Pexels (best free tier)

### 3. Audio-Visual Sync
**Options**:

| Method | Accuracy | Cost | Complexity |
|--------|----------|------|------------|
| **Whisper Forced Alignment** | High | Free | Medium |
| **Google TTS Timing** | Medium | Free | Low |
| **WPM Estimation** | Low | Free | Very Low |

**Recommendation**: Start with WPM estimation, upgrade to Whisper later

### 4. Video Composition
**New Components**:
- Scene manager
- Image downloader/cache
- Transition effects library
- Subtitle synchronizer

---

## 📊 Implementation Strategy

### Option A: Full Rebuild (2-3 days)
- Rewrite script generation with scene structure
- Integrate Pexels API
- Implement Whisper alignment
- Build new video compositor

**Pros**: Best quality, future-proof  
**Cons**: Longer timeline, more complexity

### Option B: Incremental Enhancement (1 day)
- Keep current script generation
- Add simple image search (Pexels)
- Use WPM-based timing
- Enhance video compositor with images

**Pros**: Faster, lower risk  
**Cons**: Less sophisticated, may need refactor later

### Option C: Hybrid (1.5 days)
- Enhance script generation with image keywords
- Integrate Pexels API
- Use WPM-based timing initially
- Build extensible video compositor

**Pros**: Balanced approach, room to grow  
**Cons**: Medium complexity

---

## 💡 Recommended Approach: Option C (Hybrid)

### Phase 1: Script Enhancement (3 hours)
1. Update script generation prompt to include:
   - Scene breakdown (3-5 scenes per video)
   - Image keywords per scene
   - Estimated timing per scene
2. Add `scenes` JSON field to Script model
3. Test with 1 article

### Phase 2: Image Integration (2 hours)
1. Add Pexels API integration
2. Create image search service
3. Download and cache images
4. Map images to scenes

### Phase 3: Video Composition (4 hours)
1. Refactor `_compose_video()` to be scene-based
2. Add image clips with transitions
3. Improve subtitle timing (WPM-based)
4. Add fade/zoom effects

### Phase 4: Testing (1 hour)
1. Generate 1 test video
2. Review quality
3. Iterate

**Total Time**: ~10 hours (1.5 days)

---

## 🎬 Example Video Structure

```
Scene 1 (0-15s):
  Image: AI brain visualization
  Text: "Artificial intelligence is transforming..."
  Transition: Fade in

Scene 2 (15-28s):
  Image: OpenAI office
  Text: "Companies like OpenAI are leading..."
  Transition: Zoom

Scene 3 (28-45s):
  Image: Video editing software
  Text: "These tools can now generate..."
  Transition: Pan

Scene 4 (45-60s):
  Image: Future tech concept
  Text: "The future of content creation..."
  Transition: Fade out
```

---

## 🔑 Key Technical Decisions

### 1. Image Search Strategy
**Decision**: Use Pexels API
- Free tier: 200 requests/hour
- High-quality stock photos
- Good search relevance
- Simple API

### 2. Timing Synchronization
**Decision**: Start with WPM estimation, upgrade later
- Average speaking rate: 150-160 WPM
- Calculate scene duration from word count
- Upgrade to Whisper if quality issues

### 3. Transition Effects
**Decision**: Use MoviePy built-in effects
- `fadein()`, `fadeout()`
- `resize()` for zoom
- `set_position()` for pan
- Keep it simple initially

### 4. Subtitle Style
**Decision**: Word-level captions (like TikTok/Shorts)
- Highlight current word
- 2-3 words visible at once
- Bottom third of screen
- High contrast (white text, black outline)

---

## 📝 Next Steps

1. **User Decision**: Approve Option C (Hybrid approach)?
2. **Create Implementation Plan**: Detailed technical plan
3. **Set up Pexels API**: Get API key
4. **Start Phase 1**: Enhanced script generation

---

## ❓ Questions for User

1. **Image style preference**: Stock photos, illustrations, or mixed?
2. **Transition style**: Subtle (fade) or dynamic (zoom/pan)?
3. **Subtitle style**: Word-by-word or phrase-by-phrase?
4. **Background music**: Yes/no? (adds complexity)
5. **Timeline**: Need this ASAP or can take 1.5 days?
