# Project Context: AIVideoGen

> This file provides AI assistants with the full context needed to work effectively on this project.

---

## 🎯 Project Overview

**AIVideoGen** is an automated platform that generates engaging 2-minute AI news videos for social media.

### Primary Use Cases

1. **AI News Aggregation**
   - Ingest RSS feeds and scrape AI news sites
   - Prioritize and rank stories using LLM
   - Generate video scripts automatically
   - Compose final videos with TTS and visuals

2. **Content Repurposing**
   - Download YouTube/podcast videos
   - Transcribe and analyze content
   - Extract key perspectives and insights
   - Generate transformative new content

### Target Output
- **Duration**: 60-120 seconds
- **Format**: Vertical (9:16) for YouTube Shorts, TikTok, Reels
- **Style**: Dynamic, engaging, news-style with text overlays

---

## 🛠️ Technology Stack

### Backend
| Component | Technology | Notes |
|-----------|------------|-------|
| Framework | FastAPI | Async, auto-docs at `/docs` |
| Language | Python 3.10+ | Type hints required |
| Database | SQLite (MVP) → PostgreSQL | SQLAlchemy ORM |
| Task Queue | Celery + Redis | Background video processing |
| Transcription | OpenAI Whisper | Local on Mac M-series |
| LLM | OpenAI GPT-4 / Claude | Via API |
| TTS | ElevenLabs / OpenAI TTS | Via API |
| Video | FFmpeg + MoviePy | Local processing |

### Frontend
| Component | Technology | Notes |
|-----------|------------|-------|
| Framework | React 18 | Functional components only |
| Build Tool | Vite | Fast dev server |
| Styling | CSS + Tailwind (optional) | Keep it simple |
| State | React Context + SWR | Server-state focused |
| HTTP | Axios | Centralized API client |

---

## 📂 Directory Structure

```
AIVideoGen/
├── .ai/                          # AI instructions (you are here)
│   ├── AGENTS.md                 # Persona & workflow definitions
│   ├── CONTEXT.md                # This file
│   └── CODING_STANDARDS.md       # Code conventions
│
├── .agent/                       # Workflow command definitions
│   └── workflows/
│       ├── create-issue.md
│       ├── exploration.md
│       ├── create-plan.md
│       ├── execute.md
│       ├── review.md
│       ├── peer-review.md
│       ├── learning.md
│       └── postmortem.md
│
├── backend/                      # Python FastAPI Backend
│   ├── app/
│   │   ├── api/                  # HTTP endpoints (routes)
│   │   ├── services/             # Business logic (no HTTP)
│   │   ├── models/               # SQLAlchemy models
│   │   ├── prompts/              # LLM prompt templates
│   │   └── utils/                # Utilities
│   ├── data/                     # Downloaded/generated content
│   ├── assets/                   # Fonts, music, graphics
│   └── tests/
│
├── frontend/                     # React + Vite Frontend
│   ├── src/
│   │   ├── pages/                # Page components
│   │   ├── components/           # Reusable components
│   │   ├── hooks/                # Custom hooks
│   │   └── services/             # API client
│   └── public/
│
├── docs/                         # Documentation
│   ├── plans/                    # Implementation plans
│   ├── issues/                   # Captured ideas
│   └── explorations/             # Discovery docs
│
├── CLAUDE.md                     # Primary AI system prompt
└── README.md                     # Project documentation
```

### Directory Responsibilities

| Directory | Contains | Does NOT Contain |
|-----------|----------|------------------|
| `backend/app/api/` | HTTP routes, request/response handling | Business logic |
| `backend/app/services/` | Business logic, core algorithms | HTTP-specific code |
| `backend/app/models/` | SQLAlchemy models, Pydantic schemas | Business logic |
| `frontend/src/pages/` | Full page components with routing | Reusable UI pieces |
| `frontend/src/components/` | Reusable UI components | Page-level logic |

---

## 🔑 Key Decisions Made

### Architecture
- **Monorepo structure** - Backend and frontend in same repo for easier development
- **REST API** - Simple, well-understood, good tooling (not GraphQL for MVP)
- **SQLite for MVP** - Zero configuration, switch to PostgreSQL when needed
- **Local Whisper** - Runs fast on Mac M-series, avoid API costs

### Trade-offs
- **No real-time features in MVP** - Polling over WebSockets for simplicity
- **No containerization in MVP** - Run directly on Mac for development
- **No CI/CD in MVP** - Manual deployment initially

---

## 📊 Current Status

**Phase**: Phase 2 Complete, Phase 3 Planned
**Last Updated**: 2026-01-30

### What Exists
- [x] Project structure defined
- [x] AI workflow commands set up
- [x] CTO persona configured
- [x] Backend with FastAPI (complete)
- [x] Frontend with Vite (complete)
- [x] Video generation pipeline (NotebookLM-style)
- [x] Content Library UI
- [x] Script Review UI
- [x] Video Validation UI
- [x] Dashboard with analytics
- [x] NewsAPI integration
- [x] Thumbnail generation
- [x] End screen CTAs
- [x] Background music

### What's Next
- [ ] Phase 3: Batch processing system
- [ ] YouTube auto-upload integration
- [ ] Advanced AI features (voice cloning, multi-language)

---

## 🔐 Environment Variables

Required in `.env`:
```bash
# LLM
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# TTS
ELEVENLABS_API_KEY=...

# Optional
DATABASE_URL=sqlite:///./data/app.db
LOG_LEVEL=INFO
```

---

## 📚 External Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [Whisper GitHub](https://github.com/openai/whisper)
- [ElevenLabs API](https://docs.elevenlabs.io/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
