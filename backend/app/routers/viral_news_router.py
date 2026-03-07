"""
Viral news router for trending news video flow.

Provides endpoints for discovering trending news, analyzing virality,
and creating articles for the video pipeline.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import logging

from app.database import get_db
from app.services.viral_news_service import ViralNewsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/viral-news", tags=["viral-news"])


# ── Pydantic schemas ─────────────────────────────────────────────

class TrendingRequest(BaseModel):
    """Request for discovering trending news."""
    category: Optional[str] = None
    query: Optional[str] = None
    page_size: int = 15


class TrendingArticle(BaseModel):
    """A single trending article from discovery."""
    title: str
    description: Optional[str] = None
    url: str
    source_name: Optional[str] = None
    published_at: Optional[str] = None
    image_url: Optional[str] = None
    content_preview: Optional[str] = None
    category: Optional[str] = None


class SaveSourceRequest(BaseModel):
    """Request to save a trending article as a source."""
    title: str
    description: Optional[str] = None
    url: str
    source_name: Optional[str] = None
    published_at: Optional[str] = None
    image_url: Optional[str] = None
    content_preview: Optional[str] = None
    category: Optional[str] = None


class ViralNewsSourceResponse(BaseModel):
    """Response for a viral news source."""
    id: int
    original_url: str
    title: str
    source_name: Optional[str] = None
    published_at: Optional[datetime] = None
    description: Optional[str] = None
    content_preview: Optional[str] = None
    image_url: Optional[str] = None
    news_category: Optional[str] = None
    virality_score: Optional[float] = None
    virality_reasons: Optional[List[str]] = None
    suggested_angles: Optional[List[str]] = None
    key_facts: Optional[List[str]] = None
    target_audience: Optional[str] = None
    emotional_hook: Optional[str] = None
    analysis_status: str
    error_message: Optional[str] = None
    created_at: datetime
    analyzed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CreateArticleRequest(BaseModel):
    """Request to create an article from a viral news source."""
    angle_index: int = 0
    custom_angle: Optional[str] = None


class ArticleCreatedResponse(BaseModel):
    """Response after creating an article."""
    article_id: int
    title: str
    message: str


_DURATION_MAP = {"60s": 60, "120s": 120, "300s": 300}


class GenerateScriptRequest(BaseModel):
    """Request to generate a script from a viral news source."""
    angle_index: int = 0
    custom_angle: Optional[str] = None
    video_duration: str = "60s"  # "60s", "120s", "300s"


class GenerateVideoRequest(BaseModel):
    """Request to generate a video from a viral news source."""
    angle_index: int = 0
    custom_angle: Optional[str] = None
    script_id: Optional[int] = None
    tts_provider: Optional[str] = "openai"
    voice: Optional[str] = None
    background_mode: Optional[str] = "auto"
    image_source: Optional[str] = "stock"
    video_source: Optional[str] = "stock"  # stock, veo
    video_duration: str = "60s"  # "60s", "120s", "300s"


# ── Dependency ───────────────────────────────────────────────────

def get_viral_news_service(db: Session = Depends(get_db)):
    """Dependency to get viral news service instance."""
    return ViralNewsService(db=db)


# ── Endpoints ────────────────────────────────────────────────────

@router.get("/trending")
async def discover_trending(
    category: Optional[str] = Query(None, description="News category (technology, business, etc.)"),
    query: Optional[str] = Query(None, description="Optional search query"),
    page_size: int = Query(15, ge=1, le=50),
    service: ViralNewsService = Depends(get_viral_news_service),
):
    """
    Discover trending news articles via NewsAPI.

    Returns a list of articles with headlines, sources, and metadata.
    """
    try:
        articles = service.discover_trending(
            category=category,
            query=query,
            page_size=page_size,
        )
        return {"articles": articles, "count": len(articles)}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error discovering trending: {e}")
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")


@router.post("/sources", response_model=ViralNewsSourceResponse)
async def save_source(
    request: SaveSourceRequest,
    service: ViralNewsService = Depends(get_viral_news_service),
):
    """
    Save a trending article as a viral news source.

    Deduplicates by URL — returns existing source if already saved.
    """
    try:
        source = service.get_or_create_source(request.model_dump())
        return source

    except Exception as e:
        logger.error(f"Error saving source: {e}")
        raise HTTPException(status_code=500, detail=f"Save failed: {str(e)}")


@router.get("/sources", response_model=List[ViralNewsSourceResponse])
async def list_sources(
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by analysis_status"),
    service: ViralNewsService = Depends(get_viral_news_service),
):
    """List all saved viral news sources."""
    return service.get_all_sources(limit=limit, status=status)


@router.get("/sources/{source_id}", response_model=ViralNewsSourceResponse)
async def get_source(
    source_id: int,
    service: ViralNewsService = Depends(get_viral_news_service),
):
    """Get a viral news source by ID."""
    source = service.get_source_by_id(source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    return source


@router.post("/sources/{source_id}/analyze", response_model=ViralNewsSourceResponse)
async def analyze_source(
    source_id: int,
    service: ViralNewsService = Depends(get_viral_news_service),
):
    """
    Analyze a viral news source for virality using LLM.

    Returns updated source with virality score, reasons, angles, and key facts.
    """
    try:
        source = await service.analyze_virality(source_id)
        return source

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing source: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/sources/{source_id}/create-article", response_model=ArticleCreatedResponse)
async def create_article_from_source(
    source_id: int,
    request: CreateArticleRequest,
    service: ViralNewsService = Depends(get_viral_news_service),
):
    """
    Create an Article from a viral news source for the video pipeline.

    The article can then flow through the normal Script → Video pipeline.
    """
    try:
        article = await service.create_article_from_source(
            source_id=source_id,
            angle_index=request.angle_index,
            custom_angle=request.custom_angle,
        )
        return ArticleCreatedResponse(
            article_id=article.id,
            title=article.title,
            message="Article created — ready for script generation",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating article: {e}")
        raise HTTPException(status_code=500, detail=f"Article creation failed: {str(e)}")


@router.post("/sources/{source_id}/generate-script")
async def generate_viral_news_script(
    source_id: int,
    request: GenerateScriptRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a script from a viral news source for preview/review.

    Uses the shared ScriptService pipeline (same as Book Review) with
    viral_news-specific prompt and duration-aware scene structure:
      60s  → 4 scenes (Shorts / TikTok)
      120s → 6 scenes (YouTube Shorts full story)
      300s → 10 scenes (Regular video deep dive)
    """
    from app.services.script_service import ScriptService

    try:
        service = ViralNewsService(db=db)

        # Step 1: Create article from source
        logger.info(f"[ViralScript] Creating article from source {source_id}")
        article = await service.create_article_from_source(
            source_id=source_id,
            angle_index=request.angle_index,
            custom_angle=request.custom_angle,
        )
        logger.info(f"[ViralScript] Article created: {article.id} - {article.title}")

        # Step 2: Generate script via shared ScriptService
        target_duration = _DURATION_MAP.get(request.video_duration, 60)
        logger.info(f"[ViralScript] Generating script for article {article.id} (duration={target_duration}s)")
        script_service = ScriptService(db=db)
        script = await script_service.generate_script(
            article=article,
            style="engaging",
            target_duration=target_duration,
        )
        logger.info(f"[ViralScript] Script created: {script.id} ({script.word_count} words, ~{script.estimated_duration:.0f}s)")

        return {
            "script_id": script.id,
            "article_id": article.id,
            "catchy_title": script.catchy_title,
            "scenes": script.scenes,
            "formatted_script": script.formatted_script,
            "raw_script": script.raw_script,
            "word_count": script.word_count,
            "estimated_duration": script.estimated_duration,
            "content_type": script.content_type,
            "is_valid": script.is_valid,
            "validation_errors": script.validation_errors,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[ViralScript] Failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")


@router.post("/sources/{source_id}/generate-video")
async def generate_viral_news_video(
    source_id: int,
    request: GenerateVideoRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Generate a video from a viral news source.

    Uses the identical pipeline as Book Review:
    Article → ScriptService → AudioService (TTS) → EnhancedVideoCompositionService
    → background render with SEO metadata auto-generation.

    All Book Review enhancements are inherited:
    - Scene-based image search (per-scene keywords)
    - Human Presence weighted image selection
    - Phrase-level subtitles
    - Persistent branding overlay
    - Auto SEO metadata (title, description, hashtags) on render complete
    """
    from app.services.script_service import ScriptService
    from app.services.audio_service import AudioService
    from app.services.enhanced_video_service import EnhancedVideoCompositionService

    service = ViralNewsService(db=db)
    script_service = ScriptService(db=db)

    try:
        if request.script_id:
            # Use existing reviewed script
            logger.info(f"[ViralVideo] Using existing script {request.script_id}")
            script = script_service.get_script(request.script_id)
            if not script:
                raise ValueError(f"Script {request.script_id} not found")
            # Approve the script
            script = script_service.approve_script(script.id)
            logger.info(f"[ViralVideo] Script {script.id} approved")
        else:
            # One-click flow: create article + generate + approve script
            logger.info(f"[ViralVideo] Step 1: Creating article from source {source_id}")
            article = await service.create_article_from_source(
                source_id=source_id,
                angle_index=request.angle_index,
                custom_angle=request.custom_angle,
            )
            logger.info(f"[ViralVideo] Article: {article.id}")

            target_duration = _DURATION_MAP.get(request.video_duration, 60)
            logger.info(f"[ViralVideo] Generating script (duration={target_duration}s)")
            script = await script_service.generate_script(
                article=article,
                style="engaging",
                target_duration=target_duration,
            )
            script = script_service.approve_script(script.id)
            logger.info(f"[ViralVideo] Script created and approved: {script.id}")

        # Generate TTS audio with user-selected provider and voice
        tts_provider = request.tts_provider or "openai"
        logger.info(f"[ViralVideo] Generating TTS audio (provider={tts_provider}, voice={request.voice})")
        audio_service = AudioService(db)
        audio = await audio_service.generate_audio_from_script(
            script_id=script.id,
            tts_provider=tts_provider,
            voice=request.voice,
        )
        logger.info(f"[ViralVideo] Audio generated: {audio.id}")

        # Create video task (same as book review)
        logger.info(f"[ViralVideo] Creating video task")
        video_service = EnhancedVideoCompositionService(db)
        video = video_service.create_video_task(
            script_id=script.id,
            audio_id=audio.id,
            background_style="scenes",
            background_mode=request.background_mode or "auto",
            image_source=request.image_source or "stock",
            video_source=request.video_source or "stock",
        )
        db.commit()
        db.refresh(video)
        logger.info(f"[ViralVideo] Video task created: {video.id}")

        # Queue render in background (includes SEO metadata generation on complete)
        logger.info(f"[ViralVideo] Queuing background render for video {video.id}")
        background_tasks.add_task(
            script_service.finalize_video_generation, video.id
        )

        return {
            "status": "processing",
            "source_id": source_id,
            "script_id": script.id,
            "video_id": video.id,
            "tts_provider": tts_provider,
            "voice": audio.voice,
            "message": "Viral news video generation started! Check Video Validation page.",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[ViralVideo] Failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")


@router.get("/voice-options")
async def get_voice_options(
    content_type: str = Query("viral_news", description="Content type for voice recommendations"),
):
    """Get available TTS providers and voices for viral news content."""
    try:
        from app.voice_config import get_all_voice_options
        return get_all_voice_options(content_type)
    except Exception as e:
        # Fallback if voice_config isn't available
        return {
            "providers": [
                {"id": "openai", "label": "OpenAI ($$)", "cost_label": "~$0.02/video"},
                {"id": "google", "label": "Google Cloud (Free tier)", "cost_label": "Free"},
            ],
            "recommended": {"provider": "openai", "voice": "onyx"},
        }
