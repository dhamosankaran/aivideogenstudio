from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class VideoRenderRequest(BaseModel):
    """Request to render a video."""
    script_id: int = Field(..., description="ID of the script to render")
    audio_id: Optional[int] = Field(None, description="Specific audio ID to use")
    background_style: Optional[str] = Field("gradient", description="Visual style: gradient, solid, image")

class VideoResponse(BaseModel):
    """Video details response."""
    id: int
    script_id: int
    audio_id: int
    file_path: Optional[str]
    duration: Optional[float]
    file_size: Optional[int]
    render_settings: Optional[Dict[str, Any]]
    processing_time: Optional[float]
    status: str
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    completed_at: Optional[datetime]
    download_url: Optional[str] = None
    article_title: Optional[str] = None
    
    class Config:
        from_attributes = True

class VideoListResponse(BaseModel):
    """List of videos response."""
    videos: List[VideoResponse]
    total: int
