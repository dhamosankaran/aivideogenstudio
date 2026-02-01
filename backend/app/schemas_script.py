"""
Script-related Pydantic schemas for request/response.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ScriptGenerateRequest(BaseModel):
    """Request to generate a script from an article."""
    article_id: int
    style: str = Field(default="engaging", pattern="^(engaging|casual|formal)$")
    target_duration: int = Field(default=90, ge=60, le=120)


class ScriptResponse(BaseModel):
    """Response containing script details."""
    id: int
    article_id: int
    article_title: Optional[str] = None
    raw_script: str
    formatted_script: Optional[str] = None
    word_count: Optional[int] = None
    estimated_duration: Optional[float] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    is_valid: bool
    validation_errors: Optional[List[str]] = None
    style: str
    has_hook: bool
    has_cta: bool
    status: str
    generation_cost: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ScriptUpdateRequest(BaseModel):
    """Request to update a script."""
    raw_script: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(generated|approved|rejected|revised)$")


class ValidationResultResponse(BaseModel):
    """Validation result for a script."""
    is_valid: bool
    errors: List[str] = []
    word_count: int
    estimated_duration: float
    has_required_sections: bool
