"""
Cost tracking API router.

Provides endpoints to estimate and review Gemini/Veo API spend.
All costs are estimates based on public pricing (March 2026) —
not actual billed amounts from Google.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.cost_calculator_service import (
    estimate_per_video,
    estimate_daily_spend,
    get_config_options,
)

router = APIRouter(prefix="/api/costs", tags=["costs"])


@router.get("/estimate")
async def get_cost_estimate(
    content_type: str = Query(default="book_review", description="book_review | viral_news"),
    video_source: str = Query(default="veo", description="veo | stock"),
    image_source: str = Query(default="ai_generated", description="ai_generated | stock"),
    tts_provider: str = Query(default="openai", description="openai | google | elevenlabs"),
):
    """
    Return per-video cost estimate for the given configuration.

    Use this to understand what a single generation run will cost
    before hitting Generate.
    """
    return estimate_per_video(
        content_type=content_type,
        video_source=video_source,
        image_source=image_source,
        tts_provider=tts_provider,
    )


@router.get("/daily")
async def get_daily_spend(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db),
):
    """
    Return estimated daily API spend for the past N days.

    Costs are back-calculated from video DB records using current pricing.
    Book reviews are assumed to have used Veo (matching March 1 observed spend).
    """
    return estimate_daily_spend(db=db, days=days)


@router.get("/config-options")
async def get_config_options_endpoint():
    """
    Return pricing table for all config combinations.

    Use this to show the user how much they can save by switching
    from Veo to stock video, or changing TTS provider.
    """
    return get_config_options()
