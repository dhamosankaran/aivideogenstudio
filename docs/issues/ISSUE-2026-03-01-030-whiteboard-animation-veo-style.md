# ISSUE-030: Whiteboard Animation Style for Veo Video Clips

**Created**: 2026-03-01
**Priority**: 🔵 P3 - Future Enhancement
**Phase**: Phase 5 - AI Innovation
**Status**: 📋 Idea Captured

---

## 🎯 Problem Statement

Currently, Veo generates cinematic real-world video clips (nature, objects, environments).
For book reviews specifically, a **whiteboard animation style** could be significantly more
engaging — matching the classic "explainer video" aesthetic that performs well on YouTube.

The user wants a third Video Background option alongside the existing two:

| Option | Current | Style |
|--------|---------|-------|
| Stock Videos | ✅ Live | Real stock footage from Pexels |
| Gemini Veo (Cinematic) | ✅ Live | AI-generated cinematic real-world clips |
| **Whiteboard Animation** | ❌ Future | Hand-drawing animation on white background |

---

## 💡 Feature Description

Add a **"Whiteboard Animation"** Veo generation mode for book review videos.

### Visual Style Reference
- White background canvas
- A hand (holding a pen/marker) appears to draw illustrations in real time
- Simple cartoon-style characters and diagrams emerge stroke by stroke
- Colored thought bubbles, atomic diagrams, book covers drawn live
- Brand watermark in corner (e.g. "LITTLE BIT BETTER" style)
- Fast-paced drawing motion — engaging for short-form content

### How It Differs from Cinematic Mode

| Attribute | Cinematic Veo | Whiteboard Animation |
|-----------|--------------|----------------------|
| Background | Real environments | Pure white canvas |
| Motion | Camera tracking shots | Hand drawing motion |
| Subject | Objects, nature, abstract | Illustrated diagrams, characters |
| Mood | Atmospheric, emotional | Educational, explainer-style |
| Best for | Emotional/inspirational scenes | Concept-explanation scenes |

---

## 🏗️ Implementation Approach

### Option A — Pure Veo Prompt Engineering (Try First)
Craft Veo prompts that describe the whiteboard animation style directly:

```
"Whiteboard animation style: a hand holding a marker draws [concept]
on a clean white background. Simple black outlines, colorful fills,
fast drawing motion. Explainer video aesthetic. Vertical 9:16 composition."
```

**Pros**: No new services, uses existing Veo pipeline
**Cons**: Veo may not reliably produce this style — needs testing

### Option B — Dedicated Veo Prompt Template
Add a new `build_whiteboard_prompt()` method to `VeoVideoService` alongside the existing
`build_scene_prompt()`. Use scene-specific drawing subjects:

```python
WHITEBOARD_SCENE_MAP = {
    1: "draws a closed book that slowly opens, revealing glowing pages",
    2: "draws a question mark that transforms into a lightbulb",
    3: "draws two contrasting paths — one rocky, one smooth",
    4: "draws a famous quote in stylized lettering with decorative borders",
    5: "draws gears turning inside a brain outline",
    6: "draws a lock opening to reveal a hidden key",
    7: "draws a mirror reflecting a better version of the same object",
    8: "draws an arrow pointing upward with stars bursting around it",
}
```

### Option C — Post-processing Filter (Stretch Goal)
Apply a whiteboard-style visual effect to existing Veo cinematic output using
FFmpeg filters or a style-transfer model. Heavier lift, lower priority.

---

## 🎛️ UI Changes Required

Add a third card under **Video Background** in the Visual Settings panel:

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│  📹 Stock        │  │ ✨ Gemini Veo    │  │ ✏️ Whiteboard Anim  │
│  Videos          │  │ (Cinematic)      │  │ (Explainer style)   │
│                  │  │ Beta             │  │ Beta                │
└─────────────────┘  └─────────────────┘  └─────────────────────┘
```

Backend: new `video_source` value → `"veo_whiteboard"`
Service: `VeoVideoService.build_whiteboard_prompt(scene_number, concept)`

---

## 📋 Acceptance Criteria

- [ ] Whiteboard prompt template generates consistent white-background drawing clips
- [ ] New "Whiteboard Animation" card visible in Visual Settings UI
- [ ] `video_source=veo_whiteboard` stored in render_settings and respected by pipeline
- [ ] Fallback chain: Whiteboard Veo → Cinematic Veo → Gemini AI image → gradient
- [ ] Generation time acceptable (target: same ~60s as cinematic Veo)

---

## 🔗 Related

- `backend/app/services/veo_video_service.py` — `build_scene_prompt()`, `_generate_sync()`
- `frontend/src/pages/BookReviews.jsx` — Visual Settings panel
- ISSUE-028: Creative AI Tools (parent epic)
