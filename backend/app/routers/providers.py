"""
Provider endpoints for listing providers and estimating costs.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.provider_factory import ProviderFactory
from app.services.base_provider import LLMProvider, TTSProvider


router = APIRouter(prefix="/api/providers", tags=["providers"])


class CostEstimateRequest(BaseModel):
    """Request model for cost estimation."""
    provider: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    character_count: Optional[int] = None


class CostEstimateResponse(BaseModel):
    """Response model for cost estimation."""
    provider: str
    estimated_cost: float
    currency: str = "USD"


@router.get("/llm")
async def list_llm_providers():
    """List all available LLM providers."""
    return {
        "providers": ProviderFactory.list_available_llm_providers()
    }


@router.get("/tts")
async def list_tts_providers():
    """List all available TTS providers."""
    return {
        "providers": ProviderFactory.list_available_tts_providers()
    }


@router.post("/llm/estimate-cost", response_model=CostEstimateResponse)
async def estimate_llm_cost(request: CostEstimateRequest):
    """
    Estimate cost for LLM request.
    
    Args:
        request: Cost estimation parameters
        
    Returns:
        Estimated cost
    """
    try:
        provider = LLMProvider(request.provider)
        llm = ProviderFactory.create_llm_provider(provider=provider)
        
        input_tokens = request.input_tokens or 0
        output_tokens = request.output_tokens or 0
        
        cost = llm.estimate_cost(input_tokens, output_tokens)
        
        return CostEstimateResponse(
            provider=request.provider,
            estimated_cost=cost
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tts/estimate-cost", response_model=CostEstimateResponse)
async def estimate_tts_cost(request: CostEstimateRequest):
    """
    Estimate cost for TTS request.
    
    Args:
        request: Cost estimation parameters
        
    Returns:
        Estimated cost
    """
    try:
        provider = TTSProvider(request.provider)
        tts = ProviderFactory.create_tts_provider(provider=provider)
        
        character_count = request.character_count or 0
        cost = tts.estimate_cost(character_count)
        
        return CostEstimateResponse(
            provider=request.provider,
            estimated_cost=cost
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tts/{provider}/voices")
async def list_tts_voices(provider: str):
    """
    List available voices for a TTS provider.
    
    Args:
        provider: TTS provider name
        
    Returns:
        List of available voices
    """
    try:
        provider_enum = TTSProvider(provider)
        tts = ProviderFactory.create_tts_provider(provider=provider_enum)
        voices = tts.list_voices()
        
        return {"voices": voices}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
