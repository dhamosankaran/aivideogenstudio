"""
Voice configuration for content-type-aware TTS voice selection.

Centralizes all voice/tone recommendations per content type and provider.
To add a new content type (e.g., movie_review), just add an entry to VOICE_PRESETS.
"""

from typing import Optional, Dict, Any, List


# ──────────────────────────────────────────────────────────────────────
# Voice presets: content_type → { provider → { voice, tone, ... } }
# ──────────────────────────────────────────────────────────────────────

VOICE_PRESETS: Dict[str, Dict[str, Any]] = {
    "book_review": {
        "label": "📚 Book Review",
        "default_provider": "elevenlabs",
        "openai": {
            "voice": "nova",
            "speed": 0.95,
            "tone": "Warm & clear — great for narration",
        },
        "google": {
            "voice": "en-US-Journey-F",
            "tone": "Expressive female voice",
        },
        "elevenlabs": {
            "voice": "Adam",
            "model": "eleven_multilingual_v2",
            "tone": "Warm, deep & emotional — perfect for storytelling",
        },
    },
    "tech_news": {
        "label": "💻 Tech News",
        "default_provider": "openai",
        "openai": {
            "voice": "onyx",
            "speed": 1.0,
            "tone": "Deep & authoritative",
        },
        "google": {
            "voice": "en-US-Journey-D",
            "tone": "Clear male voice",
        },
        "elevenlabs": {
            "voice": "Brian",
            "model": "eleven_multilingual_v2",
            "tone": "Friendly & upbeat — good for explainers",
        },
    },
    "movie_review": {
        "label": "🎬 Movie Review",
        "default_provider": "elevenlabs",
        "openai": {
            "voice": "fable",
            "speed": 1.0,
            "tone": "Storytelling & dramatic",
        },
        "google": {
            "voice": "en-US-Journey-F",
            "tone": "Expressive female voice",
        },
        "elevenlabs": {
            "voice": "Clyde",
            "model": "eleven_multilingual_v2",
            "tone": "Commanding with warmth — cinematic narration",
        },
    },
    "financial": {
        "label": "📊 Financial Update",
        "default_provider": "openai",
        "openai": {
            "voice": "echo",
            "speed": 1.05,
            "tone": "Confident & professional",
        },
        "google": {
            "voice": "en-US-Journey-D",
            "tone": "Clear male voice",
        },
        "elevenlabs": {
            "voice": "Daniel",
            "model": "eleven_multilingual_v2",
            "tone": "Balanced & trustworthy — informational delivery",
        },
    },
    "viral_news": {
        "label": "🔥 Viral News",
        "default_provider": "openai",
        "openai": {
            "voice": "onyx",
            "speed": 1.05,
            "tone": "Deep & authoritative — breaking news energy",
        },
        "google": {
            "voice": "en-US-Journey-D",
            "tone": "Clear male voice — news anchor quality",
        },
        "elevenlabs": {
            "voice": "Brian",
            "model": "eleven_multilingual_v2",
            "tone": "Friendly & upbeat — great for viral content",
        },
    },
    "daily_update": {
        "label": "📡 Daily AI Digest",
        "default_provider": "elevenlabs",  # AI Insider: ElevenLabs Thomas/Antoni
        "openai": {
            "voice": "onyx",
            "speed": 1.05,
            "tone": "Deep & authoritative — roundup energy",
        },
        "google": {
            "voice": "en-US-Journey-D",
            "tone": "Clear male voice — news anchor quality",
        },
        "elevenlabs": {
            "voice": "Thomas",  # AI Insider default — deep-dive & insider leaks
            "voice_breaking_news": "Antoni",  # Fast-paced breaking news beats
            "model": "eleven_multilingual_v2",
            "stability": 0.45,           # Balances consistency with natural delivery
            "similarity_boost": 0.75,    # Preserves unique "analyst" tone
            "style": 0.15,               # Subtle "insider" gravity
            "tone": "Authoritative investigative journalist — AI Insider persona",
        },
    },
    "default": {
        "label": "📰 General",
        "default_provider": "openai",
        "openai": {
            "voice": "alloy",
            "speed": 1.0,
            "tone": "Neutral & versatile",
        },
        "google": {
            "voice": "en-US-Journey-F",
            "tone": "Expressive female voice",
        },
        "elevenlabs": {
            "voice": "Rachel",
            "model": "eleven_multilingual_v2",
            "tone": "Natural & clear — great general-purpose voice",
        },
    },
}


# ──────────────────────────────────────────────────────────────────────
# Public helpers
# ──────────────────────────────────────────────────────────────────────

def get_voice_preset(content_type: str, provider: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the recommended voice settings for a content type + provider.

    Args:
        content_type: e.g. "book_review", "tech_news", "financial"
        provider: "openai", "google", or "elevenlabs" (uses default if None)

    Returns:
        Dict with voice, tone, and optional speed/model keys
    """
    preset = VOICE_PRESETS.get(content_type, VOICE_PRESETS["default"])
    provider = provider or preset.get("default_provider", "openai")
    return preset.get(provider, preset.get("openai", {}))


def get_default_provider(content_type: str) -> str:
    """Get the recommended default TTS provider for a content type."""
    preset = VOICE_PRESETS.get(content_type, VOICE_PRESETS["default"])
    return preset.get("default_provider", "openai")


def get_available_voices() -> Dict[str, List[Dict[str, str]]]:
    """
    Return all voice options per provider for the frontend TTS selector.

    Returns:
        Dict keyed by provider name, each containing a list of voice dicts.
    """
    return {
        "openai": [
            {"id": "alloy",   "name": "Alloy",   "tone": "Neutral & versatile"},
            {"id": "echo",    "name": "Echo",    "tone": "Confident & professional"},
            {"id": "fable",   "name": "Fable",   "tone": "Storytelling & dramatic"},
            {"id": "onyx",    "name": "Onyx",    "tone": "Deep & authoritative"},
            {"id": "nova",    "name": "Nova",    "tone": "Warm & clear"},
            {"id": "shimmer", "name": "Shimmer", "tone": "Bright & friendly"},
        ],
        "google": [
            {"id": "en-US-Journey-F", "name": "Journey F", "tone": "Expressive female"},
            {"id": "en-US-Journey-D", "name": "Journey D", "tone": "Clear male"},
            {"id": "en-US-Neural2-C", "name": "Neural2 C", "tone": "Natural female"},
            {"id": "en-US-Neural2-A", "name": "Neural2 A", "tone": "Natural male"},
        ],
        "elevenlabs": [
            {"id": "Rachel",  "name": "Rachel",  "tone": "Natural & clear"},
            {"id": "Adam",    "name": "Adam",    "tone": "Warm, deep & emotional"},
            {"id": "Brian",   "name": "Brian",   "tone": "Friendly & upbeat"},
            {"id": "Clyde",   "name": "Clyde",   "tone": "Commanding with warmth"},
            {"id": "Daniel",  "name": "Daniel",  "tone": "Balanced & trustworthy"},
            {"id": "Bill",    "name": "Bill",    "tone": "Classic American clarity"},
            {"id": "Grace",   "name": "Grace",   "tone": "Natural & sincere"},
            {"id": "Amelia",  "name": "Amelia",  "tone": "Enthusiastic & expressive"},
            # AI Insider personas
            {"id": "Thomas",  "name": "Thomas",  "tone": "Deep & authoritative — AI Insider deep-dives"},
            {"id": "Antoni",  "name": "Antoni",  "tone": "Fast-paced & urgent — breaking news beats"},
        ],
    }


def get_voice_options_for_frontend(content_type: str = "default") -> Dict[str, Any]:
    """
    Build the full voice options payload for the frontend TTS selector.

    Includes available voices per provider, recommended defaults, and cost estimates.
    """
    preset = VOICE_PRESETS.get(content_type, VOICE_PRESETS["default"])
    default_provider = preset.get("default_provider", "openai")

    providers = [
        {
            "id": "openai",
            "name": "OpenAI",
            "cost_label": "~$0.02/video",
            "default_voice": preset.get("openai", {}).get("voice", "alloy"),
        },
        {
            "id": "google",
            "name": "Google",
            "cost_label": "~$0.01/video",
            "default_voice": preset.get("google", {}).get("voice", "en-US-Journey-F"),
        },
        {
            "id": "elevenlabs",
            "name": "ElevenLabs",
            "cost_label": "~$0.15/video",
            "default_voice": preset.get("elevenlabs", {}).get("voice", "Rachel"),
        },
    ]

    return {
        "content_type": content_type,
        "default_provider": default_provider,
        "providers": providers,
        "voices": get_available_voices(),
    }


def get_all_voice_options(content_type: str = "default") -> Dict[str, Any]:
    """Alias for get_voice_options_for_frontend — used by viral news router."""
    return get_voice_options_for_frontend(content_type)
