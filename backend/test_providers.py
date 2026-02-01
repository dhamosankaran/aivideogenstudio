"""
Test script to verify provider implementations.

Run this script to test that providers are working correctly.
"""

import asyncio
from app.services.provider_factory import ProviderFactory
from app.services.base_provider import LLMProvider, TTSProvider
from app.config import get_settings


async def test_providers():
    """Test provider factory and implementations."""
    
    print("🧪 Testing AIVideoGen Providers\n")
    print("=" * 60)
    
    settings = get_settings()
    
    # Test LLM Provider Listing
    print("\n📋 Available LLM Providers:")
    llm_providers = ProviderFactory.list_available_llm_providers()
    for provider in llm_providers:
        print(f"  ✓ {provider}")
    
    # Test TTS Provider Listing
    print("\n📋 Available TTS Providers:")
    tts_providers = ProviderFactory.list_available_tts_providers()
    for provider in tts_providers:
        print(f"  ✓ {provider}")
    
    # Test Gemini Provider (if API key available)
    if settings.google_api_key:
        print("\n🤖 Testing Gemini Provider...")
        try:
            gemini = ProviderFactory.create_llm_provider(
                provider=LLMProvider.GEMINI
            )
            print(f"  ✓ Created: {gemini.get_provider_name()}")
            print(f"  ✓ Model: {gemini.model}")
            
            # Test cost estimation
            cost = gemini.estimate_cost(input_tokens=1000, output_tokens=500)
            print(f"  ✓ Cost estimate (1K in, 500 out): ${cost:.6f}")
            
            # Test text generation (simple prompt)
            print("  ⏳ Testing text generation...")
            response = await gemini.generate_text(
                prompt="Say 'Hello from Gemini!' in exactly 5 words.",
                max_tokens=50
            )
            print(f"  ✓ Response: {response}")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    else:
        print("\n⚠️  Gemini API key not set - skipping Gemini tests")
    
    # Test OpenAI LLM Provider (if API key available)
    if settings.openai_api_key:
        print("\n🤖 Testing OpenAI LLM Provider...")
        try:
            openai_llm = ProviderFactory.create_llm_provider(
                provider=LLMProvider.OPENAI
            )
            print(f"  ✓ Created: {openai_llm.get_provider_name()}")
            print(f"  ✓ Model: {openai_llm.model}")
            
            # Test cost estimation
            cost = openai_llm.estimate_cost(input_tokens=1000, output_tokens=500)
            print(f"  ✓ Cost estimate (1K in, 500 out): ${cost:.6f}")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    else:
        print("\n⚠️  OpenAI API key not set - skipping OpenAI LLM tests")
    
    # Test OpenAI TTS Provider (if API key available)
    if settings.openai_api_key:
        print("\n🎤 Testing OpenAI TTS Provider...")
        try:
            openai_tts = ProviderFactory.create_tts_provider(
                provider=TTSProvider.OPENAI
            )
            print(f"  ✓ Created: {openai_tts.get_provider_name()}")
            print(f"  ✓ Voice: {openai_tts.voice}")
            
            # List voices
            voices = openai_tts.list_voices()
            print(f"  ✓ Available voices: {', '.join([v['id'] for v in voices])}")
            
            # Test cost estimation
            cost = openai_tts.estimate_cost(character_count=1000)
            print(f"  ✓ Cost estimate (1000 chars): ${cost:.6f}")
            
            # Test TTS synthesis (short text)
            print("  ⏳ Testing TTS synthesis...")
            audio_bytes = await openai_tts.synthesize_speech(
                text="Hello from OpenAI TTS!",
                output_format="mp3"
            )
            print(f"  ✓ Generated audio: {len(audio_bytes)} bytes")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    else:
        print("\n⚠️  OpenAI API key not set - skipping OpenAI TTS tests")
    
    print("\n" + "=" * 60)
    print("✅ Provider tests complete!\n")


if __name__ == "__main__":
    asyncio.run(test_providers())
