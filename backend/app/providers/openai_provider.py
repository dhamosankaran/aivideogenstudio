"""
OpenAI provider implementations for both LLM and TTS.

Implements OpenAI's GPT models for text generation and OpenAI TTS
for speech synthesis.
"""

from openai import AsyncOpenAI
from typing import Optional, List, Dict, Any
from app.services.base_provider import BaseLLMProvider, BaseTTSProvider


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI LLM provider (GPT models)."""
    
    # Pricing per 1M tokens (GPT-4o as of Jan 2026)
    INPUT_PRICE_PER_1M = 2.50  # $2.50 per 1M input tokens
    OUTPUT_PRICE_PER_1M = 10.00  # $10.00 per 1M output tokens
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        """Initialize OpenAI LLM provider."""
        super().__init__(api_key, model)
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    def get_default_model(self) -> str:
        """Return default OpenAI model."""
        return "gpt-4o"
    
    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text using OpenAI GPT.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            **kwargs: Additional OpenAI parameters
            
        Returns:
            Generated text
        """
        messages = [{"role": "user", "content": prompt}]
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return response.choices[0].message.content
    
    async def analyze_video(
        self,
        video_url: str,
        prompt: str,
        **kwargs
    ) -> str:
        """
        Video analysis not supported by OpenAI GPT.
        
        Raises:
            NotImplementedError: OpenAI doesn't support direct video analysis
        """
        raise NotImplementedError(
            "OpenAI GPT does not support direct video analysis. "
            "Use Gemini for multimodal video tasks or extract frames first."
        )
    
    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Estimate cost for OpenAI request.
        
        Args:
            input_tokens: Input token count
            output_tokens: Output token count
            
        Returns:
            Estimated cost in USD
        """
        input_cost = (input_tokens / 1_000_000) * self.INPUT_PRICE_PER_1M
        output_cost = (output_tokens / 1_000_000) * self.OUTPUT_PRICE_PER_1M
        
        return input_cost + output_cost


class OpenAITTSProvider(BaseTTSProvider):
    """OpenAI TTS provider."""
    
    # Pricing: $15 per 1M characters
    PRICE_PER_1M_CHARS = 15.00
    
    # Available models
    MODELS = {
        "tts-1": "Standard quality, faster",
        "tts-1-hd": "High definition, slower"
    }
    
    # Available voices
    VOICES = [
        "alloy", "echo", "fable", 
        "onyx", "nova", "shimmer"
    ]
    
    def __init__(self, api_key: str, voice: Optional[str] = None, model: str = "tts-1"):
        """
        Initialize OpenAI TTS provider.
        
        Args:
            api_key: OpenAI API key
            voice: Voice ID (defaults to 'alloy')
            model: TTS model ('tts-1' or 'tts-1-hd')
        """
        super().__init__(api_key, voice)
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = model
    
    def get_default_voice(self) -> str:
        """Return default voice."""
        return "alloy"
    
    async def synthesize_speech(
        self,
        text: str,
        output_format: str = "mp3",
        speed: float = 1.0,
        **kwargs
    ) -> bytes:
        """
        Convert text to speech using OpenAI TTS.
        
        Args:
            text: Text to synthesize
            output_format: Audio format (mp3, opus, aac, flac)
            speed: Speech speed (0.25 to 4.0)
            **kwargs: Additional parameters
            
        Returns:
            Audio data as bytes
        """
        response = await self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text,
            response_format=output_format,
            speed=speed
        )
        
        # Return audio bytes
        return response.content
    
    def list_voices(self) -> List[Dict[str, Any]]:
        """
        List available voices.
        
        Returns:
            List of voice metadata
        """
        return [
            {"id": voice, "name": voice.capitalize(), "provider": "openai"}
            for voice in self.VOICES
        ]
    
    def estimate_cost(self, character_count: int) -> float:
        """
        Estimate cost for TTS synthesis.
        
        Args:
            character_count: Number of characters
            
        Returns:
            Estimated cost in USD
        """
        return (character_count / 1_000_000) * self.PRICE_PER_1M_CHARS
