"""
Pydantic schemas for YouTube transcript analysis.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class InsightItem(BaseModel):
    """
    Single insight extracted from transcript.
    
    NOTE: All fields MUST be required (no defaults) for Gemini JSON schema compatibility.
    Gemini rejects schemas with 'default', 'minimum', or 'maximum' fields.
    """
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    transcript_text: str = Field(..., description="Original transcript text for this segment")
    summary: str = Field(..., description="Brief summary of the insight")
    hook: str = Field(..., description="Suggested viral hook for Shorts")
    key_points: List[str] = Field(..., description="Key takeaways")
    viral_score: int = Field(..., description="Viral potential score from 1 to 10")
    engagement_type: str = Field(..., description="Type: educational, controversial, emotional, surprising, practical")


class InsightsOutput(BaseModel):
    """LLM output schema for insight extraction."""
    insights: List[InsightItem] = Field(..., description="List of extracted insights")


# API Request/Response Schemas

class YouTubeAnalyzeRequest(BaseModel):
    """Request to analyze a YouTube video."""
    youtube_url: str = Field(..., description="Full YouTube URL")


class YouTubeSourceResponse(BaseModel):
    """Response containing YouTube source data."""
    id: int
    youtube_url: str
    youtube_video_id: str
    title: Optional[str] = None
    channel_name: Optional[str] = None
    channel_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    thumbnail_url: Optional[str] = None
    analysis_status: str
    error_message: Optional[str] = None
    insights_count: int = 0
    created_at: datetime
    analyzed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class InsightResponse(BaseModel):
    """Response for a single insight."""
    index: int
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    formatted_time: str
    formatted_end_time: Optional[str] = None
    transcript_text: str = ""
    summary: Optional[str] = None
    hook: Optional[str] = None
    key_points: List[str] = []
    viral_score: int = 5
    engagement_type: Optional[str] = None


class YouTubeSourceDetailResponse(BaseModel):
    """Detailed response with insights."""
    id: int
    youtube_url: str
    youtube_video_id: str
    title: Optional[str] = None
    channel_name: Optional[str] = None
    channel_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    thumbnail_url: Optional[str] = None
    analysis_status: str
    error_message: Optional[str] = None
    insights: List[InsightResponse] = []
    created_at: datetime
    analyzed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CreateShortRequest(BaseModel):
    """Request to create a Short from an insight."""
    mode: str = Field(..., pattern="^[AB]$", description="Mode A (clip+commentary) or B (original)")
    content_type: str = Field(default="daily_update", description="Content type for styling")


class CreateShortResponse(BaseModel):
    """Response after creating a Short."""
    article_id: int
    mode: str
    message: str
    redirect_to: str = "/scripts"


class VideoSummaryResponse(BaseModel):
    """Response containing the full video summary."""
    source_id: int
    title: Optional[str] = None
    channel_name: Optional[str] = None
    video_summary: str
    generated_at: Optional[datetime] = None


class ModeAGenerateRequest(BaseModel):
    """Request to generate Mode A (Clip + Commentary) video."""
    commentary_style: str = Field(default="reaction", description="Style: reaction, analysis, or educational")
    auto_approve: bool = Field(default=True, description="Auto-approve script and start video generation")


class ModeAGenerateResponse(BaseModel):
    """Response for Mode A generation."""
    status: str
    message: str
    article_id: Optional[int] = None
    script_id: Optional[int] = None
    video_id: Optional[int] = None
    clip_path: Optional[str] = None
    redirect_to: str = "/validation"


class ModeBGenerateRequest(BaseModel):
    """Request to generate Mode B (Original content) article."""
    content_type: str = Field(default="daily_update", description="Content type for styling")


class ModeBGenerateResponse(BaseModel):
    """Response for Mode B generation."""
    status: str
    message: str
    article_id: int
    script_id: Optional[int] = None
    redirect_to: str = "/scripts"

