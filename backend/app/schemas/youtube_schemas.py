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
    description: Optional[str] = None
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
    description: Optional[str] = None
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


class TrimAndGenerateRequest(BaseModel):
    """Request to trim a clip and generate a video from it."""
    start_time: float = Field(..., description="Trim start time in seconds")
    end_time: float = Field(..., description="Trim end time in seconds")
    commentary_style: str = Field(default="reaction", description="Style: reaction, analysis, or educational")
    auto_approve: bool = Field(default=True, description="Auto-approve and start video generation")


class TrimAndGenerateResponse(BaseModel):
    """Response for trim-and-generate endpoint."""
    status: str
    message: str
    article_id: Optional[int] = None
    script_id: Optional[int] = None
    clip_path: Optional[str] = None
    clip_duration: Optional[float] = None
    redirect_to: str = "/validation"


# ── Phase 3: Universal Download & Editor Schemas ──────────────

class VideoDownloadRequest(BaseModel):
    """Request to download a video from any supported platform."""
    url: str = Field(..., description="Video URL (YouTube, X/Twitter, LinkedIn)")
    strip_audio: bool = Field(default=False, description="Remove original audio from downloaded video")


class VideoInfoResponse(BaseModel):
    """Response containing video metadata without download."""
    platform: str
    url: str
    video_id: Optional[str] = None
    title: Optional[str] = None
    duration: Optional[float] = None
    thumbnail_url: Optional[str] = None
    channel_name: Optional[str] = None
    channel_url: Optional[str] = None
    view_count: Optional[int] = None
    upload_date: Optional[str] = None
    description: Optional[str] = None
    error: Optional[str] = None


class VideoDownloadResponse(BaseModel):
    """Response after downloading a video."""
    status: str
    message: str
    platform: str
    source_id: Optional[int] = None
    file_path: Optional[str] = None
    duration: Optional[float] = None
    file_size: Optional[int] = None
    has_audio: bool = True
    metadata: Optional[dict] = None


class TranscriptSegment(BaseModel):
    """A single transcript segment with timestamps."""
    text: str
    start: float
    end: float


class TranscriptResponse(BaseModel):
    """Response containing structured transcript data."""
    source_id: int
    title: Optional[str] = None
    transcript_source: Optional[str] = None  # "youtube_captions" or "whisper"
    segments: List[TranscriptSegment] = []
    full_text: str = ""
    duration: Optional[float] = None


class EditorTrimRequest(BaseModel):
    """Request to trim a downloaded video."""
    start_time: float = Field(..., description="Trim start time in seconds")
    end_time: float = Field(..., description="Trim end time in seconds")


class EditorMusicRequest(BaseModel):
    """Request to apply background music."""
    music_track: str = Field(..., description="Filename of music track from library")
    volume: float = Field(default=0.12, description="Music volume (0.0-1.0)")


class CaptionStyleRequest(BaseModel):
    """Caption styling options."""
    font: str = Field(default="bold", description="Font style: bold, light, cinematic")
    color: str = Field(default="white", description="Text color: white, yellow, cyan")
    position: str = Field(default="bottom", description="Position: top, center, bottom")
    bg_style: str = Field(default="dark_box", description="Background: none, dark_box, blurred")


class EditorGenerateRequest(BaseModel):
    """Full editor generation request with all options."""
    trim_start: Optional[float] = Field(None, description="Trim start time in seconds")
    trim_end: Optional[float] = Field(None, description="Trim end time in seconds")
    strip_audio: bool = Field(default=True, description="Remove original audio")
    music_track: Optional[str] = Field(None, description="Background music track filename")
    music_volume: float = Field(default=0.12, description="Music volume (0.0-1.0)")
    generate_captions: bool = Field(default=True, description="Generate captions for the video")
    caption_source: str = Field(default="transcript", description="Caption source: transcript, llm, or none")
    commentary_style: str = Field(default="reaction", description="Script style: reaction, analysis, educational")
    auto_approve: bool = Field(default=True, description="Auto-approve and start video generation")
    content_type: str = Field(default="youtube_import", description="Content type for styling")
    # Enhanced fields
    aspect_ratio: str = Field(default="16:9", description="Output aspect ratio: 16:9, 9:16, 1:1")
    caption_style: Optional[CaptionStyleRequest] = Field(None, description="Caption styling options")
    voice_id: Optional[str] = Field(None, description="Selected voice ID for TTS")
    output_mode: str = Field(default="tts", description="Output mode: tts, text_overlay, captions, tts_captions")


class EditorGenerateResponse(BaseModel):
    """Response for editor generation."""
    status: str
    message: str
    article_id: Optional[int] = None
    script_id: Optional[int] = None
    video_id: Optional[int] = None
    clip_path: Optional[str] = None
    clip_duration: Optional[float] = None
    # Script preview (returned when auto_approve=false)
    script_preview: Optional[str] = None  # Formatted script text
    catchy_title: Optional[str] = None
    scenes: Optional[list] = None  # Scene breakdown
    redirect_to: str = "/validation"


class MusicTrackResponse(BaseModel):
    """Response for a single music track."""
    filename: str
    content_type: str
    label: str
    size_kb: float


class MusicLibraryResponse(BaseModel):
    """Response containing available music tracks."""
    tracks: List[MusicTrackResponse] = []
    default_track: str = "Tech.mp3"


class VoiceOption(BaseModel):
    """A single voice option."""
    id: str
    name: str
    tone: str


class VoiceListResponse(BaseModel):
    """Response containing available voices grouped by provider."""
    default_provider: str = "openai"
    providers: List[dict] = []
    voices: dict = {}


class PreviewResponse(BaseModel):
    """Response for a generated preview clip."""
    preview_url: str
    duration: float
    source_id: int


