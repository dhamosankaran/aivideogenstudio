"""
Database models for AIVideoGen.

Defines SQLAlchemy models for RSS feeds, articles, videos, and configuration.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Feed(Base):
    """RSS feed model."""
    __tablename__ = "feeds"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False, index=True)
    category = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    articles = relationship("Article", back_populates="feed", cascade="all, delete-orphan")


class Article(Base):
    """Article/news item model."""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    feed_id = Column(Integer, ForeignKey("feeds.id"), nullable=True)  # Nullable for YouTube sources
    youtube_source_id = Column(Integer, ForeignKey("youtube_sources.id"), nullable=True)
    
    # Article metadata
    title = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False, index=True)
    author = Column(String, nullable=True)
    published_at = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    
    # AI analysis
    summary = Column(Text, nullable=True)
    key_points = Column(JSON, nullable=True)  # List of key points
    sentiment = Column(String, nullable=True)  # positive, negative, neutral
    
    # LLM Scoring (Phase 2)
    relevance_score = Column(Float, nullable=True)
    engagement_score = Column(Float, nullable=True)
    recency_score = Column(Float, nullable=True)
    uniqueness_score = Column(Float, nullable=True)
    final_score = Column(Float, nullable=True, index=True)  # Weighted score for ranking
    category = Column(String, nullable=True)  # research, product, policy, industry
    key_topics = Column(JSON, nullable=True)  # List of topic tags
    why_interesting = Column(Text, nullable=True)  # One sentence pitch
    
    # Content curation (Phase 2 - UI)
    suggested_content_type = Column(String, nullable=True)  # daily_update, big_tech, leader_quote, arxiv_paper
    selected_at = Column(DateTime, nullable=True)  # When selected for script generation
    
    # YouTube Mode A/B (Phase 2.5)
    creation_mode = Column(String, nullable=True)  # "A" (clip+commentary) or "B" (original)
    clip_path = Column(String, nullable=True)  # Path to extracted YouTube clip for Mode A
    
    # Analysis metadata
    analyzed_at = Column(DateTime, nullable=True)
    
    # Status
    is_processed = Column(Boolean, default=False)
    is_selected = Column(Boolean, default=False)  # Selected for video generation
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    feed = relationship("Feed", back_populates="articles")
    youtube_source = relationship("YouTubeSource", back_populates="articles")
    scripts = relationship("Script", back_populates="article", cascade="all, delete-orphan")


class Script(Base):
    """Generated video script model."""
    __tablename__ = "scripts"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    
    # Script content
    raw_script = Column(Text, nullable=False)  # Full generated script
    formatted_script = Column(Text, nullable=True)  # Cleaned for TTS
    
    # Metadata
    word_count = Column(Integer, nullable=True)
    estimated_duration = Column(Float, nullable=True)  # seconds
    llm_provider = Column(String, nullable=True)
    llm_model = Column(String, nullable=True)
    
    # Validation
    is_valid = Column(Boolean, default=False)
    validation_errors = Column(JSON, nullable=True)
    
    # Style and structure
    style = Column(String, default="engaging")  # engaging, casual, formal
    has_hook = Column(Boolean, default=False)
    has_cta = Column(Boolean, default=False)
    scenes = Column(JSON, nullable=True)  # Scene-based structure for NotebookLM-style videos
    
    # Publishing metadata (Phase 1)
    catchy_title = Column(String, nullable=True)  # LLM-generated catchy title
    content_type = Column(String, default="daily_update")  # Content type for styling
    video_description = Column(Text, nullable=True)  # Full video description
    hashtags = Column(JSON, nullable=True)  # List of hashtags
    
    # Script review (Phase 2 - UI)
    script_status = Column(String, default="pending")  # pending, approved, rejected
    reviewed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Status
    status = Column(String, default="generated")  # generated, approved, rejected, revised
    
    # Cost tracking
    generation_cost = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    article = relationship("Article", back_populates="scripts")
    audio_files = relationship("Audio", back_populates="script", cascade="all, delete-orphan")

    videos = relationship("Video", back_populates="script", cascade="all, delete-orphan")
    
    @property
    def article_title(self) -> Optional[str]:
        """Get source article title."""
        if self.article:
            return self.article.title
        return None

class Audio(Base):
    """Generated audio (TTS) model."""
    __tablename__ = "audio"
    
    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=False)
    
    # File metadata
    file_path = Column(String, nullable=False)  # Relative path: data/audio/audio_1_20260119.mp3
    duration = Column(Float, nullable=True)  # Duration in seconds
    file_size = Column(Integer, nullable=True)  # File size in bytes
    
    # Generation metadata
    tts_provider = Column(String, nullable=False)  # openai, google, elevenlabs
    tts_model = Column(String, nullable=True)  # tts-1, tts-1-hd
    voice = Column(String, nullable=False)  # alloy, echo, fable, onyx, nova, shimmer
    
    # Cost tracking
    generation_cost = Column(Float, default=0.0)
    
    # Status
    status = Column(String, default="pending")  # pending, completed, failed
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    script = relationship("Script", back_populates="audio_files")
    videos = relationship("Video", back_populates="audio", cascade="all, delete-orphan")


class Video(Base):
    """Generated video model."""
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=False)
    audio_id = Column(Integer, ForeignKey("audio.id"), nullable=False)
    
    # File metadata
    file_path = Column(String, nullable=True)  # data/videos/video_1.mp4
    duration = Column(Float, nullable=True) 
    file_size = Column(Integer, nullable=True)
    
    # Render metadata
    render_settings = Column(JSON, nullable=True)  # {fps: 30, resolution: 1080p, style: gradient}
    processing_time = Column(Float, nullable=True)  # seconds
    
    # Publishing metadata (Phase 1)
    thumbnail_path = Column(String, nullable=True)  # Path to thumbnail image
    end_screen_path = Column(String, nullable=True)  # Path to end screen
    youtube_title = Column(String, nullable=True)  # Final YouTube title
    youtube_description = Column(Text, nullable=True)  # Final YouTube description
    
    # Video validation (Phase 2 - UI)
    validation_status = Column(String, default="pending")  # pending, approved, rejected
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    uploaded_to_youtube = Column(Boolean, default=False)
    youtube_url = Column(String, nullable=True)
    youtube_video_id = Column(String, nullable=True)
    
    # Status
    status = Column(String, default="pending")  # pending, rendering, completed, failed
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    script = relationship("Script", back_populates="videos")
    audio = relationship("Audio", back_populates="videos")
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def article_title(self) -> Optional[str]:
        """Get source article title via script."""
        if self.script and self.script.article:
            return self.script.article.title
        return None


class Config(Base):
    """Configuration/settings model."""
    __tablename__ = "config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class YouTubeSource(Base):
    """YouTube video transcript source for Phase 2.5."""
    __tablename__ = "youtube_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    youtube_url = Column(String, unique=True, nullable=False)
    youtube_video_id = Column(String, unique=True, nullable=False, index=True)
    
    # Video metadata (fetched from YouTube)
    title = Column(String, nullable=True)
    channel_name = Column(String, nullable=True)
    channel_url = Column(String, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    
    # Transcript data
    transcript = Column(JSON, nullable=True)  # [{text, start, duration}, ...]
    transcript_language = Column(String, default="en")
    
    # AI Analysis results
    insights = Column(JSON, nullable=True)  # List of KeyInsight objects
    video_summary = Column(Text, nullable=True)  # Full video summary
    summary_generated_at = Column(DateTime, nullable=True)
    analysis_status = Column(String, default="pending")  # pending, analyzing, completed, failed
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    analyzed_at = Column(DateTime, nullable=True)
    
    # Relationships
    articles = relationship("Article", back_populates="youtube_source", cascade="all, delete-orphan")
