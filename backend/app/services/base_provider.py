"""
Base provider abstractions for LLM and TTS services.

This module defines abstract base classes that all LLM and TTS providers
must implement, enabling a pluggable strategy pattern for swapping providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"


class TTSProvider(str, Enum):
    """Supported TTS providers."""
    GOOGLE = "google"
    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM providers must implement these methods to be compatible
    with the AIVideoGen system.
    """
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        """
        Initialize the LLM provider.
        
        Args:
            api_key: API key for the provider
            model: Optional model name (uses default if not specified)
        """
        self.api_key = api_key
        self.model = model or self.get_default_model()
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Return the default model name for this provider."""
        pass
    
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: The input prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    async def analyze_video(
        self,
        video_url: str,
        prompt: str,
        **kwargs
    ) -> str:
        """
        Analyze a video using multimodal capabilities.
        
        Args:
            video_url: URL or path to video
            prompt: Analysis prompt
            **kwargs: Provider-specific parameters
            
        Returns:
            Analysis result as text
            
        Raises:
            NotImplementedError: If provider doesn't support video analysis
        """
        pass
    
    @abstractmethod
    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Estimate cost for a request.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        pass
    
    def get_provider_name(self) -> str:
        """Return the provider name."""
        return self.__class__.__name__


class BaseTTSProvider(ABC):
    """
    Abstract base class for TTS providers.
    
    All TTS providers must implement these methods to be compatible
    with the AIVideoGen system.
    """
    
    def __init__(self, api_key: str, voice: Optional[str] = None):
        """
        Initialize the TTS provider.
        
        Args:
            api_key: API key for the provider
            voice: Optional voice ID (uses default if not specified)
        """
        self.api_key = api_key
        self.voice = voice or self.get_default_voice()
    
    @abstractmethod
    def get_default_voice(self) -> str:
        """Return the default voice ID for this provider."""
        pass
    
    @abstractmethod
    async def synthesize_speech(
        self,
        text: str,
        output_format: str = "mp3",
        **kwargs
    ) -> bytes:
        """
        Convert text to speech.
        
        Args:
            text: Text to convert to speech
            output_format: Audio format (mp3, wav, etc.)
            **kwargs: Provider-specific parameters
            
        Returns:
            Audio data as bytes
        """
        pass
    
    @abstractmethod
    def list_voices(self) -> List[Dict[str, Any]]:
        """
        List available voices.
        
        Returns:
            List of voice metadata dictionaries
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, character_count: int) -> float:
        """
        Estimate cost for TTS synthesis.
        
        Args:
            character_count: Number of characters to synthesize
            
        Returns:
            Estimated cost in USD
        """
        pass
    
    def get_provider_name(self) -> str:
        """Return the provider name."""
        return self.__class__.__name__
