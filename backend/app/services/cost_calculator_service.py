"""
API Cost Calculator Service.

Estimates Gemini/Veo API costs based on current pricing (March 2026).
Used to explain bills and project future spend before generating videos.

Pricing sources (March 2026):
  Gemini 3.1 Flash image: $60/1M output tokens; 1K resolution ≈ 1120 tokens → $0.067/image
  Veo 3.1 Standard:       $0.40/second → $3.20 per 8-second clip
  TTS costs:              OpenAI $0.02, Google $0.01, ElevenLabs $0.15 per video
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date

from app.models import Video, Script, Audio, Article

# ── Pricing Constants ─────────────────────────────────────────────────────────

# Gemini 3.1 Flash image generation
_GEMINI_PRICE_PER_1M_TOKENS = 60.00          # USD per 1M output image tokens
_GEMINI_TOKENS_PER_1K_IMAGE = 1_120          # tokens for 1K (768×1376) image
GEMINI_IMAGE_PRICE = _GEMINI_PRICE_PER_1M_TOKENS / 1_000_000 * _GEMINI_TOKENS_PER_1K_IMAGE
# = ~$0.0672 per image

# Veo 3.1 Standard video generation
VEO_PRICE_PER_SECOND = 0.40                  # USD per second of generated video
VEO_DEFAULT_DURATION_SEC = 8                 # default clip duration
VEO_PRICE_PER_CLIP = VEO_PRICE_PER_SECOND * VEO_DEFAULT_DURATION_SEC
# = $3.20 per 8-second clip

# Scenes in a book review that get Veo clips (0-indexed: 2, 3, 5 → scenes 3, 4, 6)
VEO_CLIPS_PER_BOOK_REVIEW = 3
# Total scenes in a standard book review
BOOK_REVIEW_TOTAL_SCENES = 8
# Gemini images for the remaining scenes
GEMINI_IMAGES_PER_BOOK_REVIEW = BOOK_REVIEW_TOTAL_SCENES - VEO_CLIPS_PER_BOOK_REVIEW  # 5

# Viral news: no Veo by default, ~4 Gemini images per video
GEMINI_IMAGES_PER_VIRAL_NEWS = 4
VEO_CLIPS_PER_VIRAL_NEWS = 0

# TTS cost estimates (per video, flat rate)
TTS_COST_PER_VIDEO: dict[str, float] = {
    "openai": 0.02,
    "google": 0.01,
    "elevenlabs": 0.15,
}
DEFAULT_TTS_PROVIDER = "openai"


# ── Per-video cost estimation ─────────────────────────────────────────────────

def estimate_per_video(
    content_type: str = "book_review",
    video_source: str = "veo",       # "veo" | "stock"
    image_source: str = "ai_generated",  # "ai_generated" | "stock"
    tts_provider: str = DEFAULT_TTS_PROVIDER,
) -> dict:
    """Return a detailed cost breakdown for one video generation run."""

    # Determine Veo clip count
    if video_source == "veo":
        if content_type == "book_review":
            veo_clips = VEO_CLIPS_PER_BOOK_REVIEW
        else:
            veo_clips = VEO_CLIPS_PER_VIRAL_NEWS
    else:
        veo_clips = 0

    # Determine Gemini image count
    if image_source == "ai_generated":
        if content_type == "book_review":
            gemini_images = BOOK_REVIEW_TOTAL_SCENES - veo_clips
        else:
            gemini_images = GEMINI_IMAGES_PER_VIRAL_NEWS
    else:
        gemini_images = 0

    veo_cost = round(veo_clips * VEO_PRICE_PER_CLIP, 4)
    image_cost = round(gemini_images * GEMINI_IMAGE_PRICE, 4)
    tts_cost = TTS_COST_PER_VIDEO.get(tts_provider, TTS_COST_PER_VIDEO[DEFAULT_TTS_PROVIDER])
    total = round(veo_cost + image_cost + tts_cost, 4)

    # What it would cost with stock video instead of Veo
    stock_video_total = round(image_cost + tts_cost, 4)
    veo_savings = round(veo_cost, 4)

    return {
        "content_type": content_type,
        "video_source": video_source,
        "image_source": image_source,
        "tts_provider": tts_provider,
        "veo_clips": veo_clips,
        "veo_cost": veo_cost,
        "gemini_images": gemini_images,
        "gemini_image_cost": image_cost,
        "tts_cost": tts_cost,
        "total_per_video": total,
        "without_veo_total": stock_video_total,
        "veo_savings_per_video": veo_savings,
        "pricing": {
            "veo_per_second": VEO_PRICE_PER_SECOND,
            "veo_per_clip_8s": VEO_PRICE_PER_CLIP,
            "gemini_image_1k": round(GEMINI_IMAGE_PRICE, 4),
            "tts_openai": TTS_COST_PER_VIDEO["openai"],
            "tts_google": TTS_COST_PER_VIDEO["google"],
            "tts_elevenlabs": TTS_COST_PER_VIDEO["elevenlabs"],
        },
    }


# ── Config options table ──────────────────────────────────────────────────────

def get_config_options() -> dict:
    """Return pricing table for all meaningful config combinations."""
    combos = []
    for content_type in ("book_review", "viral_news"):
        for video_source in ("veo", "stock"):
            for tts_provider in ("openai", "google", "elevenlabs"):
                est = estimate_per_video(
                    content_type=content_type,
                    video_source=video_source,
                    image_source="ai_generated",
                    tts_provider=tts_provider,
                )
                combos.append({
                    "content_type": content_type,
                    "video_source": video_source,
                    "tts_provider": tts_provider,
                    "total": est["total_per_video"],
                    "veo_cost": est["veo_cost"],
                    "image_cost": est["gemini_image_cost"],
                    "tts_cost": est["tts_cost"],
                })
    return {"options": combos, "pricing": combos[0]["total"] if combos else {}}


# ── Historical daily spend estimation ────────────────────────────────────────

def estimate_daily_spend(db: Session, days: int = 30) -> dict:
    """
    Estimate daily spend from DB records for the past N days.

    Since API costs weren't tracked historically, we estimate by:
    - Counting video generation attempts per day
    - Splitting by content_type (book_review vs viral_news)
    - Assuming book reviews used Veo (matches March 1 behaviour)
    - Reading TTS provider from audio table
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Fetch all videos created in the window with their script + audio
    rows = (
        db.query(
            Video,
            Script.content_type,
            Audio.tts_provider,
        )
        .join(Script, Video.script_id == Script.id)
        .outerjoin(Audio, Video.audio_id == Audio.id)
        .filter(Video.created_at >= since)
        .order_by(Video.created_at.desc())
        .all()
    )

    # Group by calendar date
    daily: dict[str, dict] = {}
    for video, content_type, tts_provider in rows:
        day_key = video.created_at.strftime("%Y-%m-%d") if video.created_at else "unknown"
        if day_key not in daily:
            daily[day_key] = {
                "date": day_key,
                "videos_attempted": 0,
                "book_reviews": 0,
                "viral_news": 0,
                "veo_cost": 0.0,
                "image_cost": 0.0,
                "tts_cost": 0.0,
                "estimated_cost": 0.0,
                "note": "",
            }

        ct = content_type or "book_review"
        tts = tts_provider or DEFAULT_TTS_PROVIDER

        est = estimate_per_video(
            content_type=ct,
            video_source="veo" if ct == "book_review" else "stock",
            image_source="ai_generated",
            tts_provider=tts,
        )

        daily[day_key]["videos_attempted"] += 1
        if ct == "book_review":
            daily[day_key]["book_reviews"] += 1
        else:
            daily[day_key]["viral_news"] += 1

        daily[day_key]["veo_cost"] = round(daily[day_key]["veo_cost"] + est["veo_cost"], 4)
        daily[day_key]["image_cost"] = round(daily[day_key]["image_cost"] + est["gemini_image_cost"], 4)
        daily[day_key]["tts_cost"] = round(daily[day_key]["tts_cost"] + est["tts_cost"], 4)
        daily[day_key]["estimated_cost"] = round(
            daily[day_key]["veo_cost"] + daily[day_key]["image_cost"] + daily[day_key]["tts_cost"],
            2,
        )

    # Add context note for known dates
    for day_key, entry in daily.items():
        parts = []
        if entry["book_reviews"]:
            parts.append(f"{entry['book_reviews']} book review(s) w/ Veo")
        if entry["viral_news"]:
            parts.append(f"{entry['viral_news']} viral news")
        entry["note"] = ", ".join(parts) if parts else "no videos"
        entry["veo_cost"] = round(entry["veo_cost"], 2)
        entry["image_cost"] = round(entry["image_cost"], 2)
        entry["tts_cost"] = round(entry["tts_cost"], 2)

    sorted_days = sorted(daily.values(), key=lambda x: x["date"], reverse=True)
    total_estimated = round(sum(d["estimated_cost"] for d in sorted_days), 2)

    return {
        "days": sorted_days,
        "total_estimated": total_estimated,
        "period_days": days,
    }
