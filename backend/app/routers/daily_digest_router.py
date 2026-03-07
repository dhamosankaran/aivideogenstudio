"""
Daily AI Digest router.

Endpoints:
  POST /api/daily-digest/rank           — LLM-rank a list of article IDs
  POST /api/daily-digest/articles       — Create a digest article from ranked IDs
  GET  /api/daily-digest/articles       — List existing digest articles
  POST /api/daily-digest/articles/{id}/script  — Generate roundup script
  POST /api/daily-digest/articles/{id}/video   — Generate video
  GET  /api/daily-digest/voice-options  — TTS voice options for daily_update
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.daily_digest_service import DailyDigestService
from app.voice_config import get_all_voice_options

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/daily-digest", tags=["daily-digest"])

_DURATION_MAP = {"60s": 60, "90s": 90, "120s": 120}


# ── Pydantic schemas ──────────────────────────────────────────────────

class RankRequest(BaseModel):
    article_ids: List[int]


class RankedArticle(BaseModel):
    article_id: int
    title: str
    rank: int
    impact_score: float
    company: str
    key_fact: str
    impact: str
    rank_reason: str
    headline_suggestion: str
    description: Optional[str] = None


class CreateDigestRequest(BaseModel):
    ranked_article_ids: List[int]
    title: str
    ranked_metadata: Optional[List[dict]] = None  # pre-computed ranking data from /rank


class DigestArticleResponse(BaseModel):
    article_id: int
    title: str
    story_count: int
    message: str


class GenerateScriptRequest(BaseModel):
    video_duration: str = "60s"  # "60s" or "90s"


class GenerateVideoRequest(BaseModel):
    script_id: Optional[int] = None
    tts_provider: Optional[str] = "openai"
    voice: Optional[str] = None
    background_mode: Optional[str] = "auto"
    image_source: Optional[str] = "stock"
    video_source: Optional[str] = "stock"
    video_duration: str = "60s"
    veo_style: Optional[str] = "auto"


# ── Endpoints ─────────────────────────────────────────────────────────

@router.post("/rank", response_model=List[RankedArticle])
async def rank_articles(
    request: RankRequest,
    db: Session = Depends(get_db),
):
    """
    Rank selected articles by AI impact, novelty, and audience relevance.

    Single batched LLM call. Falls back to recency sort if LLM fails.
    """
    if not request.article_ids:
        raise HTTPException(status_code=400, detail="article_ids cannot be empty")
    if len(request.article_ids) > 15:
        raise HTTPException(status_code=400, detail="Maximum 15 articles per digest")

    try:
        service = DailyDigestService(db=db)
        ranked = await service.rank_articles(request.article_ids)
        return ranked
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[DigestRank] Failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ranking failed: {str(e)}")


@router.post("/articles", response_model=DigestArticleResponse)
async def create_digest_article(
    request: CreateDigestRequest,
    db: Session = Depends(get_db),
):
    """
    Create a single digest Article aggregating N ranked source articles.

    The returned article_id flows into the existing script → audio → video pipeline.
    """
    if not request.ranked_article_ids:
        raise HTTPException(status_code=400, detail="ranked_article_ids cannot be empty")
    if len(request.ranked_article_ids) < 2:
        raise HTTPException(status_code=400, detail="Digest requires at least 2 articles")
    if not request.title.strip():
        raise HTTPException(status_code=400, detail="Digest title cannot be empty")

    try:
        service = DailyDigestService(db=db)
        article = await service.create_digest_article(
            ranked_article_ids=request.ranked_article_ids,
            title=request.title,
            ranked_metadata=request.ranked_metadata,
        )
        story_count = len(request.ranked_article_ids)
        return DigestArticleResponse(
            article_id=article.id,
            title=article.title,
            story_count=story_count,
            message=f"Digest article created with {story_count} stories — ready for script generation",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[DigestCreate] Failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Digest creation failed: {str(e)}")


@router.get("/articles")
async def list_digest_articles(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List existing digest articles (most recent first)."""
    try:
        service = DailyDigestService(db=db)
        articles = service.list_digest_articles(limit=limit)
        return [
            {
                "article_id": a.id,
                "title": a.title,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "story_count": len(a.key_points) if a.key_points else 0,
                "has_script": bool(a.scripts),
            }
            for a in articles
        ]
    except Exception as e:
        logger.error(f"[DigestList] Failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list digests: {str(e)}")


@router.post("/articles/{article_id}/script")
async def generate_digest_script(
    article_id: int,
    request: GenerateScriptRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a roundup script from a digest article.

    Uses _build_daily_digest_script_prompt() via the shared ScriptService.
    Duration: 60s (3 stories, 7 scenes) or 90s (5 stories, 9 scenes).
    """
    from app.models import Article
    from app.services.script_service import ScriptService

    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
    if article.suggested_content_type != "daily_update":
        raise HTTPException(status_code=400, detail="Article is not a daily digest")

    target_duration = _DURATION_MAP.get(request.video_duration, 60)

    try:
        script_service = ScriptService(db=db)
        script = await script_service.generate_script(
            article=article,
            style="engaging",
            target_duration=target_duration,
        )
        logger.info(f"[DigestScript] Script {script.id} created for article {article_id}")

        return {
            "script_id": script.id,
            "article_id": article_id,
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
        logger.error(f"[DigestScript] Failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")


@router.post("/articles/{article_id}/video")
async def generate_digest_video(
    article_id: int,
    request: GenerateVideoRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Generate a video from a digest article.

    Pipeline: (existing script) → AudioService (TTS) → EnhancedVideoCompositionService
    Background render — returns video_id immediately.
    """
    from app.models import Article
    from app.services.script_service import ScriptService
    from app.services.audio_service import AudioService
    from app.services.enhanced_video_service import EnhancedVideoCompositionService

    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
    if article.suggested_content_type != "daily_update":
        raise HTTPException(status_code=400, detail="Article is not a daily digest")

    script_service = ScriptService(db=db)

    try:
        if request.script_id:
            script = script_service.get_script(request.script_id)
            if not script:
                raise ValueError(f"Script {request.script_id} not found")
            script = script_service.approve_script(script.id)
            logger.info(f"[DigestVideo] Using existing script {script.id}")
        else:
            target_duration = _DURATION_MAP.get(request.video_duration, 60)
            script = await script_service.generate_script(
                article=article,
                style="engaging",
                target_duration=target_duration,
            )
            script = script_service.approve_script(script.id)
            logger.info(f"[DigestVideo] Generated and approved script {script.id}")

        tts_provider = request.tts_provider or "openai"
        audio_service = AudioService(db)
        audio = await audio_service.generate_audio_from_script(
            script_id=script.id,
            tts_provider=tts_provider,
            voice=request.voice,
        )
        logger.info(f"[DigestVideo] Audio generated: {audio.id}")

        video_service = EnhancedVideoCompositionService(db)
        video = video_service.create_video_task(
            script_id=script.id,
            audio_id=audio.id,
            background_style="scenes",
            background_mode=request.background_mode or "auto",
            image_source=request.image_source or "stock",
            video_source=request.video_source or "stock",
            veo_style=request.veo_style or "auto",
        )
        db.commit()
        db.refresh(video)
        logger.info(f"[DigestVideo] Video task created: {video.id}")

        background_tasks.add_task(
            script_service.finalize_video_generation, video.id
        )

        return {
            "status": "processing",
            "article_id": article_id,
            "script_id": script.id,
            "video_id": video.id,
            "tts_provider": tts_provider,
            "voice": audio.voice,
            "message": "Daily digest video generation started! Check Video Validation page.",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[DigestVideo] Failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")


@router.get("/voice-options")
async def get_voice_options(
    content_type: str = Query("daily_update"),
):
    """Get available TTS providers and voices for the daily digest."""
    try:
        return get_all_voice_options(content_type)
    except Exception as e:
        logger.error(f"[DigestVoice] Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
