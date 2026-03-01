"""
Central content type registry — single source of truth.

Every service (music, end screens, thumbnails, metadata, etc.)
should import from here instead of maintaining separate dicts.
"""

# ─── Master registry ────────────────────────────────────────────
# Keys are the content_type strings stored in the DB (Script.content_type).
# Add new journeys here and every downstream service picks them up.

CONTENT_TYPES = {
    # ── News / AI ──
    "daily_update": {
        "label": "News",
        "channel": "@realAIInsider",
        "music": "Tech.mp3",
        "cta": "Subscribe for Daily AI News!",
        "footer": "🔔 Turn on notifications!",
        "music_volume": 0.12,
    },
    "big_tech": {
        "label": "Tech",
        "channel": "@realAIInsider",
        "music": "Tech.mp3",
        "cta": "Follow for In-Depth Analysis!",
        "footer": "🔔 Turn on notifications!",
        "music_volume": 0.12,
    },
    "leader_quote": {
        "label": "Quotes",
        "channel": "@IconsoftheWorld-w7f",
        "music": "Tech.mp3",
        "cta": "Get Inspired Daily!",
        "footer": "💡 Daily Wisdom Awaits!",
        "music_volume": 0.08,
    },
    "arxiv_paper": {
        "label": "Research",
        "channel": "@realAIInsider",
        "music": "Tech.mp3",
        "cta": "Learn Cutting-Edge AI!",
        "footer": "🧠 Stay Ahead of AI Research!",
        "music_volume": 0.10,
    },
    # ── Books ──
    "book_review": {
        "label": "Books",
        "channel": "@60sBooks-review",
        "music": "Books.mp3",
        "cta": "Subscribe for Book Reviews!",
        "footer": "📚 More Book Summaries Weekly!",
        "music_volume": 0.10,
    },
    # ── Movies / Entertainment ──
    "movies": {
        "label": "Movies",
        "channel": "@TheNextChapter-bp2zx",
        "music": "Movies.mp3",
        "cta": "Subscribe for Movie Reviews!",
        "footer": "🎬 New Reviews Every Week!",
        "music_volume": 0.12,
    },
    # ── Robotics ──
    "robotics": {
        "label": "Robotics",
        "channel": "@realAIInsider",
        "music": "Tech.mp3",
        "cta": "Follow for Robotics Updates!",
        "footer": "🤖 The Future Is Now!",
        "music_volume": 0.12,
    },
    # ── Finance ──
    "finance": {
        "label": "Finance",
        "channel": "@WallStreetWire",
        "music": "Tech.mp3",
        "cta": "Subscribe for Market Updates!",
        "footer": "📈 Stay Ahead of the Markets!",
        "music_volume": 0.12,
    },
    # ── Crypto ──
    "crypto": {
        "label": "Crypto",
        "channel": "@BitCoinPulse-d4p",
        "music": "Tech.mp3",
        "cta": "Subscribe for Crypto Updates!",
        "footer": "₿ Stay on Top of Crypto!",
        "music_volume": 0.12,
    },
    # ── YouTube Import (catch-all) ──
    "youtube_import": {
        "label": "Import",
        "channel": "@realAIInsider",
        "music": "Tech.mp3",
        "cta": "Subscribe for More Insights!",
        "footer": "🔔 Turn on notifications!",
        "music_volume": 0.12,
    },
    # ── Viral News ──
    "viral_news": {
        "label": "Viral",
        "channel": "@realAIInsider",
        "music": "Tech.mp3",
        "cta": "Subscribe for Viral News!",
        "footer": "🔥 Breaking Stories Daily!",
        "music_volume": 0.12,
    },
}

# ─── Convenience helpers ────────────────────────────────────────

DEFAULT_CONTENT_TYPE = "daily_update"
DEFAULT_FALLBACK_MUSIC = "Tech.mp3"


def get_registry(content_type: str) -> dict:
    """Get the registry entry for a content type, with safe fallback."""
    return CONTENT_TYPES.get(content_type, CONTENT_TYPES[DEFAULT_CONTENT_TYPE])


def get_all_content_type_keys() -> list[str]:
    """Return all registered content_type keys."""
    return list(CONTENT_TYPES.keys())


def get_channel_name(content_type: str) -> str:
    return get_registry(content_type)["channel"]


def get_music_file(content_type: str) -> str:
    return get_registry(content_type).get("music", DEFAULT_FALLBACK_MUSIC)


def get_music_volume(content_type: str) -> float:
    return get_registry(content_type).get("music_volume", 0.12)


def get_project_subfolder(content_type: str) -> str:
    """Return the top-level project subfolder name (e.g. 'books', 'news')."""
    return get_registry(content_type)["label"].lower()
