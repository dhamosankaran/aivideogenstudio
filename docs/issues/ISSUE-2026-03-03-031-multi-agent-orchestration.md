# ISSUE-031: Multi-Agent Orchestration (ADK-Based Pipeline)

**Created**: 2026-03-03
**Priority**: 🔵 P3 - Future Enhancement
**Phase**: Phase 5 - AI Innovation
**Status**: 📋 Idea Captured

---

## 🎯 Problem Statement

The current pipeline uses a single monolithic LLM call (or a handful of sequential calls) to handle script writing, image sourcing, and video compilation. As the platform grows in complexity — more content types, more personas, more visual styles — a single prompt juggling all instructions becomes fragile, inconsistent, and hard to debug.

---

## 💡 Proposed Solution: Multi-Agent Orchestration via ADK

Replace the monolithic generation flow with a **team of specialist agents** orchestrated via Google's Agent Development Kit (ADK). Each agent owns one responsibility and operates with a focused, well-scoped prompt.

### Agent Team

| Agent | Responsibility |
|-------|---------------|
| **ScriptWriterAgent** | Draft the narrative — persona, tone, scene structure, word count targets |
| **ImageSourcingAgent** | Autonomously search the internet and pull relevant visuals per scene (Pexels, Gemini Image Gen, Unsplash) |
| **VideoCompilerAgent** | Stitch the assets (audio, images/video clips, subtitles, music) into the final output |
| **QualityGateAgent** *(optional)* | Review script and assets before compilation — flags issues before expensive rendering |
| **PublisherAgent** *(optional)* | Handle YouTube upload, metadata, scheduling once video is approved |

### Orchestration Modes (ADK-Native)

- **Sequential Pipeline**: ScriptWriter → ImageSourcing → VideoCompiler (default flow)
- **Parallel Execution**: ImageSourcing runs concurrently across all scenes while audio is being generated
- **Intelligent Routing**: QualityGateAgent decides whether to send back to ScriptWriter or proceed to compilation

---

## 🏗️ Architecture

```
User Request (content type, topic, persona)
        │
        ▼
┌─────────────────────┐
│  OrchestratorAgent  │  ← ADK root agent, manages the pipeline
└────────┬────────────┘
         │  sequential
         ▼
┌─────────────────────┐
│  ScriptWriterAgent  │  ← LLM: generates scenes, narration, keywords
└────────┬────────────┘
         │  parallel fan-out per scene
         ▼
┌─────────────────────┐
│ ImageSourcingAgent  │  ← Pexels / Gemini / Unsplash search per scene
└────────┬────────────┘
         │  parallel
         ▼
┌─────────────────────┐
│   AudioGenAgent     │  ← TTS (Google / ElevenLabs / OpenAI)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ VideoCompilerAgent  │  ← MoviePy/FFmpeg stitch + subtitles + music
└─────────────────────┘
```

---

## 🎯 Why ADK?

- **Specialist prompts** → each agent has a tight, focused instruction set → higher quality outputs
- **Parallel execution** → ImageSourcingAgent can fetch all 8 scene images simultaneously while audio renders, cutting total generation time by ~40%
- **Retry isolation** → if ImageSourcingAgent fails on scene 3, only that scene retries — no full pipeline restart
- **Observability** → each agent emits structured logs → easy to trace exactly where quality degrades
- **Extensibility** → adding a new content type = adding a new ScriptWriterAgent variant, not modifying a 500-line prompt

---

## 📊 Expected Impact

| Metric | Current | With Multi-Agent |
|--------|---------|-----------------|
| Generation time | ~3-5 min | ~1.5-2.5 min (parallel) |
| Prompt complexity | 1 large prompt | 4-5 focused prompts |
| Failure isolation | Full restart | Per-agent retry |
| Debuggability | Hard | Per-agent logs |
| Content type extensibility | Moderate | High (swap agents) |

---

## 🗺️ Implementation Path

1. **Phase A — ADK setup** (Prototype, ~1 week)
   - Install and configure Google ADK
   - Port `ScriptService` → `ScriptWriterAgent`
   - Run in shadow mode alongside existing pipeline
   - Compare output quality

2. **Phase B — Image & Audio Agents** (~1 week)
   - Port `ImageSearchOrchestrator` → `ImageSourcingAgent`
   - Port `AudioService` → `AudioGenAgent`
   - Enable parallel scene image fetching

3. **Phase C — Compiler & Orchestrator** (~1 week)
   - Port `EnhancedVideoService` → `VideoCompilerAgent`
   - Wire up `OrchestratorAgent` as the root
   - Replace existing pipeline entry points

4. **Phase D — Quality Gate & Publisher** (optional, ~1 week)
   - Add `QualityGateAgent` for pre-render review
   - Add `PublisherAgent` for YouTube auto-upload integration

---

## 🔗 Related

- ROADMAP: Phase 5 — AI Innovation
- ISSUE-019: Batch Processing (parallel execution complements ADK parallelism)
- ISSUE-020: YouTube Auto-Upload (PublisherAgent natural fit)
- ISSUE-027: Advanced AI Features
- `backend/app/services/script_service.py`
- `backend/app/services/enhanced_video_service.py`
- `backend/app/services/image_search_orchestrator.py`
