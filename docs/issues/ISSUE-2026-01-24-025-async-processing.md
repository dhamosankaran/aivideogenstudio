# Issue: Async Processing Optimization

**Date**: 2026-01-24
**Priority**: 🟡 P1 (High Performance)
**Status**: 📋 Planned

## Problem
Script generation (LLM calls) and Video rendering (FFmpeg/MoviePy) take 10s to 5mins. Currently, these *might* be blocking HTTP requests or relying on simple `await` which keeps the connection open.
*   **Risk**: UI timeouts ("Network Error") if the browser gives up waiting.
*   **Risk**: Server thread blocking if not truly async.

## Validated Solution
Refactor endpoints to use `FastAPI.BackgroundTasks` or a simple async queue to return "202 Accepted" immediately.

## Implementation Plan
1.  **Refactor `POST /api/content/scripts/generate`**:
    *   Change to return `{"status": "queued", "job_id": "..."}` immediately.
    *   Run generation in `BackgroundTasks`.
    *   Frontend polls `GET /api/content/articles` to see `is_processed` become true.
2.  **Refactor `POST /api/scripts/{id}/generate-video`**:
    *   Ensure it definitely runs in background (currently it might, need verification).
    *   Add progress tracking endpoint (optional).

## Acceptance Criteria
- [ ] UI receives immediate response when clicking "Generate".
- [ ] UI shows "Processing..." state while backend works.
- [ ] No browser timeouts for long videos.
