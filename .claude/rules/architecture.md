# Architecture Reference

## Content Type Routing
Script generation routes by `content_type` in `script_service.py` at ~line 118:

| Content Type | Prompt Function | Duration | Notes |
|-------------|-----------------|----------|-------|
| `book_review` | `_build_book_review_script_prompt()` | 85s fixed | Genre persona, Nano Banana 8-scene |
| `viral_news` | `_build_viral_news_script_prompt()` | caller-specified (60/120/300s) | News persona |
| `daily_update` | `_build_daily_digest_script_prompt()` | caller-specified (60s=3 stories, 90s=5 stories) | Skips URL extraction |

New pipelines: add content type to `content_types.py`, add prompt function to `prompts/__init__.py`, route it in `script_service.py`.

## Daily Digest Article Pattern
1. User selects N source articles from Content Library
2. `DailyDigestService.rank_articles()` — single batched LLM call ranks them
3. `DailyDigestService.create_digest_article()` — creates one aggregate `Article` with:
   - `url` = `digest://YYYYMMDD-{uuid8}` (synthetic, prevents URL extraction)
   - `suggested_content_type` = `"daily_update"`
   - `key_points` = `[{title, source, company, key_fact, impact, description, rank}]`
4. Digest `article.id` flows into the existing script → audio → video pipeline

## Video Rendering Pipeline
`ScriptService.finalize_video_generation(video_id)` orchestrates:
1. `AudioService` (TTS) — generates audio from approved script
2. `EnhancedVideoCompositionService` — composes final video

Key parameters for `create_video_task()`:
- `background_mode`: "auto", "solid", "gradient"
- `image_source`: "stock" | "ai_generated" (→ GeminiImageService, 1K 9:16)
- `video_source`: "stock" | "veo" (→ VeoVideoService)
- `veo_style`: "auto", "whiteboard", etc.

Sentence-level subtitle rendering (YouTube CC style) is active for: `book_review`, `viral_news`, `daily_update`.

## Shared CSS Architecture
`ViralNews.css` exports shared `vn-*` layout classes. All three pipeline pages import it:
```jsx
import './ViralNews.css';       // shared layout/buttons/forms
import './DailyDigest.css';     // page-specific cards/steps/scenes
```

## Router Registration
All routers registered in `backend/app/main.py`. Adding a new pipeline:
1. Create `backend/app/routers/new_pipeline_router.py`
2. Create `backend/app/services/new_pipeline_service.py`
3. Register router in `main.py`: `app.include_router(new_pipeline_router.router)`
4. Add to `frontend/src/App.jsx` NAV_ITEMS and route

## Content Library API
`GET /api/content/articles` — returns `{items: [{id, title, source, description, published_at, ...}]}`

Important: field is `source` NOT `feed_name`. Supported filters:
- `date_range`: "today", "last_7_days", "last_30_days"
- `source`: feed name string
- `search`: text search
- `page`, `page_size`: pagination
