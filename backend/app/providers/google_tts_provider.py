import httpx
import json
import base64
from typing import Dict, Any, List
from app.services.base_provider import BaseTTSProvider

class GoogleTTSProvider(BaseTTSProvider):
    """
    Google Cloud Text-to-Speech provider using REST API.
    Uses generic API Key authentication (compatible with Gemini API keys usually).
    """
    
    API_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"
    
    def get_default_voice(self) -> str:
        """Return default Google TTS voice."""
        return "en-US-Journey-F" # Journey voices are newer and more expressive
        
    async def synthesize_speech(
        self,
        text: str,
        output_format: str = "mp3",
        **kwargs
    ) -> bytes:
        """
        Convert text to speech using Google Cloud TTS REST API.
        """
        if not self.api_key:
            raise ValueError("Google API Key is required for TTS")

        # Map simple output format to Google's enum
        audio_encoding = "MP3"
        if output_format.lower() == "wav":
            audio_encoding = "LINEAR16"
        elif output_format.lower() == "ogg":
            audio_encoding = "OGG_OPUS"
            
        # Construct payload
        payload = {
            "input": {
                "text": text
            },
            "voice": {
                "languageCode": "en-US",
                "name": self.voice or self.get_default_voice()
            },
            "audioConfig": {
                "audioEncoding": audio_encoding,
                "speakingRate": kwargs.get("speed", 1.0),
                "pitch": kwargs.get("pitch", 0.0)
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.API_URL,
                json=payload,
                headers=headers,
                timeout=120.0  # Increased for longer scripts (80-90s audio)
            )
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("error", {}).get("message", error_detail)
                except:
                    pass
                raise Exception(f"Google TTS API Error: {error_detail}")
                
            data = response.json()
            audio_content = data.get("audioContent")
            
            if not audio_content:
                raise Exception("No audio content received from Google TTS")
                
            # Decode base64
            return base64.b64decode(audio_content)
            
    def list_voices(self) -> List[Dict[str, Any]]:
        """List available voices (mocked/static for MVP to avoid extra calls)."""
        # In a real app, we could call https://texttospeech.googleapis.com/v1/voices
        return [
            {"id": "en-US-Journey-F", "name": "Journey F (Expressive)", "gender": "FEMALE"},
            {"id": "en-US-Journey-D", "name": "Journey D (Expressive)", "gender": "MALE"},
            {"id": "en-US-Neural2-A", "name": "Neural2 A", "gender": "MALE"},
            {"id": "en-US-Neural2-C", "name": "Neural2 C", "gender": "FEMALE"},
            {"id": "en-US-Neural2-F", "name": "Neural2 F", "gender": "FEMALE"},
            {"id": "en-US-Studio-M", "name": "Studio M", "gender": "MALE"},
            {"id": "en-US-Studio-O", "name": "Studio O", "gender": "FEMALE"},
        ]
        
    def estimate_cost(self, character_count: int) -> float:
        """
        Estimate cost for Google TTS.
        Standard voices: $0.000004 per char ($4/1M)
        WaveNet voices: $0.016 per char ($16/1M)
        Neural2 voices: $0.016 per char ($16/1M)
        """
        # Assume Neural2/Journey pricing (higher tier)
        price_per_char = 0.000016 
        return character_count * price_per_char
