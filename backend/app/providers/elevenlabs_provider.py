"""
ElevenLabs TTS provider using REST API.

Uses direct HTTP calls via httpx (same pattern as google_tts_provider.py)
to avoid adding the elevenlabs SDK as a dependency.
"""

import httpx
import logging
from typing import Dict, Any, List, Optional
from app.services.base_provider import BaseTTSProvider

logger = logging.getLogger(__name__)


class ElevenLabsTTSProvider(BaseTTSProvider):
    """ElevenLabs TTS provider using REST API."""

    API_URL = "https://api.elevenlabs.io/v1/text-to-speech"

    # Pre-built voice library — stable IDs from ElevenLabs public voice library
    VOICE_LIBRARY = {
        "Rachel":  "21m00Tcm4TlvDq8ikWAM",
        "Adam":    "pNInz6obpgDQGcFmaJgB",
        "Brian":   "nPczCjzI2devNBz1zQrb",
        "Clyde":   "2EiwWnXFnvU5JabPnv8n",
        "Daniel":  "onwK4e9ZLuTAKqWW03F9",
        "Bill":    "pqHfZKP75CvOlQylNhV4",
        "Grace":   "oWAxZDx7w5VEj9dCyTzz",
        "Amelia":  "OYTbf65OHHFELVut7v2H",
    }

    # Available models
    MODELS = {
        "eleven_multilingual_v2": "Multilingual v2 — best quality, 29 languages",
        "eleven_flash_v2_5": "Flash v2.5 — 50% cheaper, low latency",
        "eleven_turbo_v2_5": "Turbo v2.5 — balanced speed/quality",
    }

    # Pricing: ~$0.30 per 1K characters on Creator plan ($22/mo)
    PRICE_PER_1K_CHARS = 0.30

    def __init__(self, api_key: str, voice: Optional[str] = None, model: str = "eleven_multilingual_v2"):
        """
        Initialize ElevenLabs TTS provider.

        Args:
            api_key: ElevenLabs API key
            voice: Voice name (e.g., "Adam") or voice ID
            model: Model ID (default: eleven_multilingual_v2)
        """
        super().__init__(api_key, voice)
        self.model = model

    def get_default_voice(self) -> str:
        """Return default ElevenLabs voice."""
        return "Rachel"

    def _resolve_voice_id(self, voice_name: str) -> str:
        """Resolve a voice name to its ElevenLabs voice ID."""
        # If it looks like a voice ID already (long alphanumeric), use as-is
        if len(voice_name) > 15:
            return voice_name
        # Look up in library
        return self.VOICE_LIBRARY.get(voice_name, self.VOICE_LIBRARY["Rachel"])

    async def synthesize_speech(
        self,
        text: str,
        output_format: str = "mp3",
        **kwargs
    ) -> bytes:
        """
        Convert text to speech using ElevenLabs REST API.

        Args:
            text: Text to synthesize
            output_format: Audio format (mp3_44100_128 default)
            **kwargs: Additional parameters (model_id, stability, similarity_boost)

        Returns:
            Audio data as bytes
        """
        voice_id = self._resolve_voice_id(self.voice)
        model_id = kwargs.get("model_id", self.model)

        # Map simple format to ElevenLabs format string
        format_map = {
            "mp3": "mp3_44100_128",
            "wav": "pcm_44100",
        }
        el_format = format_map.get(output_format, "mp3_44100_128")

        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": kwargs.get("stability", 0.5),
                "similarity_boost": kwargs.get("similarity_boost", 0.75),
                "style": kwargs.get("style", 0.0),
                "use_speaker_boost": kwargs.get("use_speaker_boost", True),
            }
        }

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        url = f"{self.API_URL}/{voice_id}?output_format={el_format}"

        logger.info(f"ElevenLabs TTS: voice={self.voice} (id={voice_id}), model={model_id}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                timeout=120.0
            )

            if response.status_code != 200:
                error_detail = response.text[:500]
                logger.error(f"ElevenLabs API error ({response.status_code}): {error_detail}")
                raise Exception(
                    f"ElevenLabs TTS API Error ({response.status_code}): {error_detail}"
                )

            logger.info(f"ElevenLabs TTS: received {len(response.content)} bytes")
            return response.content

    def list_voices(self) -> List[Dict[str, Any]]:
        """List available pre-built voices."""
        return [
            {"id": name, "name": name, "provider": "elevenlabs",
             "voice_id": vid}
            for name, vid in self.VOICE_LIBRARY.items()
        ]

    def estimate_cost(self, character_count: int) -> float:
        """
        Estimate cost for ElevenLabs TTS.

        Based on Creator plan ($22/mo, 100K chars included).
        Overage: ~$0.30 per 1K characters.
        """
        return (character_count / 1000) * self.PRICE_PER_1K_CHARS
