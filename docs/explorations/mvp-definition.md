# Exploration: AIVideoGen MVP

**Date**: 2026-01-19  
**Status**: Complete ✅

---

## Problem Statement

Build an automated platform that generates 2-minute AI news videos daily with minimal cost and full end-to-end automation (no manual video editing required).

---

## User Story

As a content creator, I want an automated system that ingests AI news, generates engaging scripts, creates videos with voiceover, so that I can post daily content to YouTube without manual video editing.

---

## Scope

### ✅ In Scope (MVP)

**Use Case 1: AI News Aggregation (Primary)**
- RSS feed ingestion from 5-10 sources
- Web scraping of AI news sites
- LLM-based content ranking and selection
- Automated script generation
- Text-to-speech audio generation
- Video composition with stock footage
- Web UI to control the entire pipeline
- **Model selection UI** - Choose LLM and TTS providers

**Use Case 2: Content Repurposing (Secondary)**
- YouTube URL → Transcript extraction (using Gemini multimodal)
- Key perspective extraction
- Derivative content generation
- Start with transcript-only (no video download)

### ❌ Out of Scope (MVP)

- Auto-upload to YouTube (manual for validation)
- Thumbnail generation
- Multi-language support
- Real-time processing
- Mobile app
- Your own voice recording

### 🔄 Deferred (Post-MVP)

- AI avatar host integration
- Viral clip detection
- RAG chat with video library
- Multi-platform distribution (TikTok, Instagram)

---

## Key Decisions Made

### 1. LLM Provider Strategy
**Decision**: Multi-provider support with UI selection  
**Options**:
- **Gemini 2.0 Flash** (default) - Best cost/performance ($0.003/video)
- **OpenAI GPT-4o Mini** - Backup option
- **Claude 3.5 Haiku** - Premium quality option

**Rationale**: Gemini multimodal can analyze videos directly (no download), cheapest option, good quality.

### 2. TTS Provider Strategy
**Decision**: Multi-provider support with UI selection  
**Options**:
- **Google Cloud TTS** - Cheapest ($0.02/video) but robotic
- **OpenAI TTS** - Best balance ($0.10/video)
- **ElevenLabs** - Premium quality ($0.73/video or subscription)

**Rationale**: Let user experiment to find best quality/cost ratio.

### 3. Video Download Approach
**Decision**: Start with Gemini multimodal (no download)  
**Why**: URL → Gemini API → transcript (no yt-dlp, no Whisper needed)  
**Fallback**: Add yt-dlp later if needed

### 4. Budget Constraint
**Decision**: Target <$5/month for daily videos  
**Stack**: Gemini Flash + OpenAI TTS = ~$3.30/month

---

## Architecture Pattern

```
Frontend (React) 
    ↓
  Settings Panel (Model Selection)
    ↓
FastAPI Backend
    ↓
Service Layer (LLM/TTS Adapters)
    ↓
Provider APIs (Gemini, OpenAI, etc.)
```

**Pattern**: Strategy pattern for LLM/TTS providers (swap implementations via config)

---

## Dependencies

### Required APIs
- Google AI Studio (Gemini) - FREE tier available
- OpenAI API - $5 credit to start
- Pexels API - FREE for stock footage
- (Optional) ElevenLabs - $22/month subscription

### System Dependencies
- FFmpeg (video processing)
- Python 3.11+
- Node.js 18+ (frontend)

---

## Risks

| Risk | Mitigation |
|------|------------|
| API costs exceed budget | Default to Gemini (cheapest), monitor usage dashboard |
| TTS quality too robotic | UI lets user switch providers easily |
| Gemini multimodal fails | Fallback to yt-dlp + Whisper |
| Stock footage repetitive | Curate diverse Pexels search queries |
| No video validation yet | Start manually posting to validate content |

---

## Open Questions

✅ All answered:
- ✅ Budget? Low (target <$5/month)
- ✅ LLM provider? Gemini Flash (with UI selection)
- ✅ TTS quality? OpenAI TTS default (with UI selection)
- ✅ Frontend needed? Yes, full dashboard
- ✅ Video download? Gemini multimodal first

---

## Ready for Planning?

- [x] All scope questions answered
- [x] Data model understood (feeds, articles, videos, scripts)
- [x] Integration points identified (Gemini, OpenAI, Pexels, FFmpeg)
- [x] User confirmed understanding
- [x] Budget constraints clear

**Status**: ✅ Ready for `/create-plan`
