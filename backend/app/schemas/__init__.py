"""
Pydantic schemas for request/response models.

Separates API contracts from database models.

Submodules:
- schemas.script: Script generation request/response
- schemas.audio: Audio generation request/response
- schemas.video: Video rendering request/response
- schemas.youtube_schemas: YouTube transcript analysis
- schemas.script_generation: Structured script output (scene-based)
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, Field


# ===== Feed Schemas =====

class FeedBase(BaseModel):
    """Base feed fields."""
    name: str
    url: HttpUrl
    category: Optional[str] = None
    is_active: bool = True


class FeedCreate(FeedBase):
    """Schema for creating a new feed."""
    pass


class FeedUpdate(BaseModel):
    """Schema for updating a feed."""
    name: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class FeedResponse(FeedBase):
    """Schema for feed response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ===== Article Schemas =====

class ArticleBase(BaseModel):
    """Base article fields."""
    title: str
    url: str  # Accept any URL (including manual://, book://, etc.)
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    description: Optional[str] = None
    content: Optional[str] = None


class ArticleScores(BaseModel):
    """LLM analysis scores for an article."""
    relevance_score: float
    engagement_score: float
    recency_score: float
    uniqueness_score: float
    category: str
    key_topics: List[str]
    why_interesting: str


class ArticleResponse(ArticleBase):
    """Schema for article response."""
    id: int
    feed_id: Optional[int] = None  # Optional for manual/book sources
    youtube_source_id: Optional[int] = None
    book_source_id: Optional[int] = None
    
    # AI analysis
    summary: Optional[str] = None
    relevance_score: Optional[float] = None
    engagement_score: Optional[float] = None
    recency_score: Optional[float] = None
    uniqueness_score: Optional[float] = None
    final_score: Optional[float] = None
    category: Optional[str] = None
    key_topics: Optional[List[str]] = None
    why_interesting: Optional[str] = None
    
    # Status
    is_processed: bool
    is_selected: bool
    analyzed_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ArticleRankingResponse(BaseModel):
    """Schema for ranked articles list."""
    articles: List[ArticleResponse]
    total: int
    top_score: Optional[float] = None


class ArticleSelectRequest(BaseModel):
    """Schema for selecting an article for video generation."""
    article_id: int


# ===== Job/Task Schemas =====

class JobResponse(BaseModel):
    """Schema for background job status."""
    job_id: str
    status: str  # pending, running, completed, failed
    message: str
    created_at: datetime
