"""
Audio-related Pydantic schemas for request/response.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class AudioGenerateRequest(BaseModel):
    """Request to generate audio from a script."""
    script_id: int
    voice: Optional[str] = Field(default="alloy", description="Voice ID for TTS")
    tts_provider: Optional[str] = Field(default="openai", description="TTS provider to use")
    
    @field_validator('voice')
    @classmethod
    def validate_voice(cls, v: str) -> str:
        """Allow any voice string to support multiple providers."""
        if not v:
            return "alloy"
        return v


class AudioResponse(BaseModel):
    """Response containing audio details."""
    id: int
    script_id: int
    file_path: str
    duration: Optional[float] = None
    file_size: Optional[int] = None
    tts_provider: str
    tts_model: Optional[str] = None
    voice: str
    generation_cost: float
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None  # Computed field
    
    class Config:
        from_attributes = True


class AudioListResponse(BaseModel):
    """Response containing a list of audio files."""
    audio_files: List[AudioResponse]
    total: int
