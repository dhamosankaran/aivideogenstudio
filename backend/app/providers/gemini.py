"""
Gemini LLM provider implementation.

Uses Google's Generative AI library to interact with Gemini models.
Supports multimodal video analysis without downloading files.
"""

import google.generativeai as genai
from typing import Optional
from app.services.base_provider import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """Gemini LLM provider with multimodal capabilities."""
    
    # Pricing per 1M tokens (as of Jan 2026)
    INPUT_PRICE_PER_1M = 0.075  # $0.075 per 1M input tokens
    OUTPUT_PRICE_PER_1M = 0.30  # $0.30 per 1M output tokens
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        """Initialize Gemini provider."""
        super().__init__(api_key, model)
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(self.model)
    
    def get_default_model(self) -> str:
        """Return default Gemini model."""
        return "gemini-flash-latest"
    
    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text using Gemini.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            **kwargs: Additional Gemini parameters
            
        Returns:
            Generated text
        """
        # Default safety settings to BLOCK_NONE to avoid technical/unintended blocks
        # Use proper types from google.generativeai.types
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        
        safety_settings = [
            {
                "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                "threshold": HarmBlockThreshold.BLOCK_NONE,
            },
            {
                "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                "threshold": HarmBlockThreshold.BLOCK_NONE,
            },
            {
                "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                "threshold": HarmBlockThreshold.BLOCK_NONE,
            },
            {
                "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                "threshold": HarmBlockThreshold.BLOCK_NONE,
            },
        ]
        
        # Build generation config
        generation_config = {
            "temperature": temperature,
        }
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens
        
        # Handle JSON mode with schema
        if "response_mime_type" in kwargs:
            generation_config["response_mime_type"] = kwargs["response_mime_type"]
        if "response_schema" in kwargs:
            generation_config["response_schema"] = kwargs["response_schema"]
        
        try:
            response = await self.client.generate_content_async(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            import logging
            logger = logging.getLogger(__name__)
            
            # Log finish reason for debugging
            if response.candidates:
                finish_reason = response.candidates[0].finish_reason
                logger.debug(f"Gemini finish_reason: {finish_reason}")
                
                # Check for safety blocks - but try to get text anyway
                if finish_reason == 2:  # SAFETY
                    logger.warning(f"Gemini response had SAFETY finish_reason. Prompt excerpt: {prompt[:100]}...")
                    # Try to get text anyway
                    try:
                        return response.text
                    except Exception as text_error:
                        logger.warning(f"Could not get text from blocked response: {text_error}")
                        # Return a placeholder that will fail JSON parsing gracefully
                        return "Error: Content blocked by safety filters. Please try a different insight or prompt."
                
            return response.text
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            # If it's the specific response.text error due to safety
            if "response.text" in str(e) or "finish_reason" in str(e) or "blocked" in str(e).lower():
                logger.warning(f"Gemini response error (likely safety): {str(e)}")
                return "Error: Content could not be generated due to safety filters."
            raise e

    
    async def analyze_video(
        self,
        video_url: str,
        prompt: str,
        **kwargs
    ) -> str:
        """
        Analyze video using Gemini's multimodal capabilities.
        
        Gemini can analyze videos directly from URLs without downloading.
        This is a major cost and time saver.
        
        Args:
            video_url: URL to video (YouTube, GCS, etc.)
            prompt: Analysis prompt
            **kwargs: Additional parameters
            
        Returns:
            Video analysis as text
        """
        # For YouTube URLs, Gemini can process directly
        # For other videos, we'll need to upload or use file API
        
        content = [
            prompt,
            {
                "mime_type": "video/mp4",
                "data": video_url  # Gemini handles URL fetching
            }
        ]
        
        generation_config = kwargs.get("generation_config", {})
        
        response = await self.client.generate_content_async(
            content,
            generation_config=generation_config
        )
        
        return response.text
    
    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Estimate cost for Gemini request.
        
        Args:
            input_tokens: Input token count
            output_tokens: Output token count
            
        Returns:
            Estimated cost in USD
        """
        input_cost = (input_tokens / 1_000_000) * self.INPUT_PRICE_PER_1M
        output_cost = (output_tokens / 1_000_000) * self.OUTPUT_PRICE_PER_1M
        
        return input_cost + output_cost


class GeminiTTSProvider:
    """
    Placeholder for Google TTS provider.
    
    Google Cloud Text-to-Speech API would go here.
    For now, we'll focus on OpenAI TTS as the default.
    """
    pass
