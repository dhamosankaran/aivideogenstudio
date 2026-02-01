"""
Provider factory for creating LLM and TTS provider instances.

This factory centralizes provider instantiation and makes it easy
to swap providers based on configuration or user selection.
"""

from typing import Optional
from app.services.base_provider import (
    BaseLLMProvider,
    BaseTTSProvider,
    LLMProvider,
    TTSProvider
)
from app.providers.gemini import GeminiProvider
from app.providers.openai_provider import OpenAILLMProvider, OpenAITTSProvider
from app.providers.google_tts_provider import GoogleTTSProvider
from app.config import get_settings


class ProviderFactory:
    """Factory for creating provider instances."""
    
    # Registry of LLM providers
    LLM_PROVIDERS = {
        LLMProvider.GEMINI: GeminiProvider,
        LLMProvider.OPENAI: OpenAILLMProvider,
        # LLMProvider.CLAUDE: ClaudeProvider,  # TODO: Implement
    }
    
    # Registry of TTS providers
    TTS_PROVIDERS = {
        TTSProvider.OPENAI: OpenAITTSProvider,
        TTSProvider.GOOGLE: GoogleTTSProvider,
        # TTSProvider.ELEVENLABS: ElevenLabsTTSProvider,  # TODO: Implement
    }
    
    @classmethod
    def create_llm_provider(
        cls,
        provider: Optional[LLMProvider] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ) -> BaseLLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider: Provider enum (uses default from config if None)
            api_key: API key (fetches from config if None)
            model: Model name (uses provider default if None)
            
        Returns:
            Initialized LLM provider
            
        Raises:
            ValueError: If provider not supported or API key missing
        """
        settings = get_settings()
        
        # Use default provider if not specified
        if provider is None:
            provider = LLMProvider(settings.default_llm_provider)
        
        # Get API key from config if not provided
        if api_key is None:
            api_key = cls._get_llm_api_key(provider, settings)
        
        if not api_key:
            raise ValueError(f"API key not found for provider: {provider}")
        
        # Get provider class from registry
        provider_class = cls.LLM_PROVIDERS.get(provider)
        if not provider_class:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        return provider_class(api_key=api_key, model=model)
    
    @classmethod
    def create_tts_provider(
        cls,
        provider: Optional[TTSProvider] = None,
        api_key: Optional[str] = None,
        voice: Optional[str] = None
    ) -> BaseTTSProvider:
        """
        Create a TTS provider instance.
        
        Args:
            provider: Provider enum (uses default from config if None)
            api_key: API key (fetches from config if None)
            voice: Voice ID (uses provider default if None)
            
        Returns:
            Initialized TTS provider
            
        Raises:
            ValueError: If provider not supported or API key missing
        """
        settings = get_settings()
        
        # Use default provider if not specified
        if provider is None:
            provider = TTSProvider(settings.default_tts_provider)
        
        # Get API key from config if not provided
        if api_key is None:
            api_key = cls._get_tts_api_key(provider, settings)
        
        if not api_key:
            raise ValueError(f"API key not found for provider: {provider}")
        
        # Get provider class from registry
        provider_class = cls.TTS_PROVIDERS.get(provider)
        if not provider_class:
            raise ValueError(f"Unsupported TTS provider: {provider}")
        
        return provider_class(api_key=api_key, voice=voice)
    
    @staticmethod
    def _get_llm_api_key(provider: LLMProvider, settings) -> Optional[str]:
        """Get API key for LLM provider from settings."""
        key_map = {
            LLMProvider.GEMINI: settings.google_api_key,
            LLMProvider.OPENAI: settings.openai_api_key,
            LLMProvider.CLAUDE: settings.anthropic_api_key,
        }
        return key_map.get(provider)
    
    @staticmethod
    def _get_tts_api_key(provider: TTSProvider, settings) -> Optional[str]:
        """Get API key for TTS provider from settings."""
        key_map = {
            TTSProvider.OPENAI: settings.openai_api_key,
            TTSProvider.GOOGLE: settings.google_api_key,
            TTSProvider.ELEVENLABS: settings.elevenlabs_api_key,
        }
        return key_map.get(provider)
    
    @classmethod
    def list_available_llm_providers(cls) -> list[str]:
        """List all available LLM providers."""
        return [provider.value for provider in cls.LLM_PROVIDERS.keys()]
    
    @classmethod
    def list_available_tts_providers(cls) -> list[str]:
        """List all available TTS providers."""
        return [provider.value for provider in cls.TTS_PROVIDERS.keys()]
