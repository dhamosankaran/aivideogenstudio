"""
Script management API endpoints.

Provides script generation, validation, and CRUD operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db
from app.schemas.script import (
    ScriptGenerateRequest,
    ScriptResponse,
    ScriptUpdateRequest,
    ValidationResultResponse
)
from app.models import Article, Script
from app.services.script_service import ScriptService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


@router.post("/generate", response_model=ScriptResponse, status_code=201)
async def generate_script(
    request: ScriptGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a video script from an article.
    
    Args:
        request: Script generation parameters
    """
    # Check if article exists
    article = db.query(Article).filter(Article.id == request.article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check if article has been analyzed
    if not article.analyzed_at:
        raise HTTPException(
            status_code=400,
            detail="Article must be analyzed before generating script"
        )
    
    # Generate script
    service = ScriptService(db)
    
    try:
        script = await service.generate_script(
            article=article,
            style=request.style,
            target_duration=request.target_duration
        )
        
        return script
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate script: {str(e)}"
        )


# Script Review Endpoints - Must come before /{script_id} to avoid path conflicts

@router.get("/pending", response_model=List[ScriptResponse])
async def get_pending_scripts(db: Session = Depends(get_db)):
    """
    Get all scripts pending review.
    
    Returns list of scripts with script_status='pending'.
    """
    service = ScriptService(db)
    scripts = service.get_pending_scripts()
    return scripts


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a script by ID.
    
    Args:
        script_id: Script ID
    """
    script = db.query(Script).filter(Script.id == script_id).first()
    
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    return script


@router.get("/", response_model=List[ScriptResponse])
async def list_scripts(
    article_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """
    List scripts with optional filters.
    
    Args:
        article_id: Filter by article ID
        status: Filter by status (generated, approved, rejected)
        limit: Maximum number of results
    """
    query = db.query(Script)
    
    if article_id:
        query = query.filter(Script.article_id == article_id)
    
    if status:
        query = query.filter(Script.status == status)
    
    scripts = query.order_by(Script.created_at.desc()).limit(limit).all()
    
    return scripts


@router.put("/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_id: int,
    request: ScriptUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update a script.
    
    Args:
        script_id: Script ID
        request: Update data
    """
    service = ScriptService(db)
    
    # Build update dict
    update_data = request.model_dump(exclude_unset=True)
    
    # If raw_script changed, re-validate
    if "raw_script" in update_data:
        validation = service.validate_script(update_data["raw_script"])
        update_data["is_valid"] = validation.is_valid
        update_data["validation_errors"] = validation.errors
        
        # Recalculate metrics
        update_data["word_count"] = service._count_words(update_data["raw_script"])
        update_data["estimated_duration"] = service.estimate_duration(update_data["raw_script"])
        update_data["formatted_script"] = service.format_for_tts(update_data["raw_script"])
    
    script = service.update_script(script_id, **update_data)
    
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    return script


@router.post("/{script_id}/validate", response_model=ValidationResultResponse)
async def validate_script(
    script_id: int,
    db: Session = Depends(get_db)
):
    """
    Validate a script against quality criteria.
    
    Args:
        script_id: Script ID
    """
    script = db.query(Script).filter(Script.id == script_id).first()
    
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    service = ScriptService(db)
    validation = service.validate_script(script.raw_script)
    
    return ValidationResultResponse(
        is_valid=validation.is_valid,
        errors=validation.errors,
        word_count=script.word_count or 0,
        estimated_duration=script.estimated_duration or 0.0,
        has_required_sections=script.has_hook and script.has_cta
    )


@router.post("/{script_id}/approve", response_model=ScriptResponse)
async def approve_script(
    script_id: int,
    db: Session = Depends(get_db)
):
    """
    Approve a script for video generation.
    
    Args:
        script_id: Script ID
    """
    service = ScriptService(db)
    script = service.approve_script(script_id)
    
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    return script


@router.post("/{script_id}/reject", response_model=ScriptResponse)
async def reject_script(
    script_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Reject a script.
    
    Args:
        script_id: Script ID
        reason: Optional rejection reason
    """
    service = ScriptService(db)
    script = service.reject_script(script_id, reason)
    
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    return script


@router.delete("/{script_id}", status_code=204)
async def delete_script(
    script_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a script.
    
    Args:
        script_id: Script ID
    """
    script = db.query(Script).filter(Script.id == script_id).first()
    
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    db.delete(script)
    db.commit()
    
    return None


@router.get("/{script_id}/detail")
async def get_script_detail(
    script_id: int,
    db: Session = Depends(get_db)
):
    """
    Get script with source article for review.
    
    Returns both script and article data for side-by-side review.
    """
    service = ScriptService(db)
    result = await service.get_script_with_article(script_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Script not found")
    
    script = result["script"]
    article = result["article"]
    
    return {
        "script": {
            "id": script.id,
            "article_id": script.article_id,
            "catchy_title": script.catchy_title,
            "content_type": script.content_type,
            "scenes": script.scenes,
            "video_description": script.video_description,
            "hashtags": script.hashtags,
            "word_count": script.word_count,
            "estimated_duration": script.estimated_duration,
            "script_status": script.script_status,
            "status": script.status,  # Also include 'status' for frontend compatibility
            "created_at": script.created_at,
            "updated_at": script.updated_at
        },
        "article": {
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "description": article.description,
            "content": article.content,
            "key_points": article.key_points,
            "published_at": article.published_at
        } if article else None,
        "catchy_title": result.get("catchy_title"),
        "scene_count": result.get("scene_count", 0),
        "article_url": result.get("article_url")
    }


@router.put("/{script_id}/content")
async def update_script_content(
    script_id: int,
    catchy_title: Optional[str] = None,
    scenes: Optional[List[dict]] = None,
    content_type: Optional[str] = None,
    video_description: Optional[str] = None,
    hashtags: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """
    Update script content during review.
    
    Allows editing title, scenes, content type, description, and hashtags.
    """
    service = ScriptService(db)
    
    script = service.update_script_content(
        script_id=script_id,
        catchy_title=catchy_title,
        scenes=scenes,
        content_type=content_type,
        video_description=video_description,
        hashtags=hashtags
    )
    
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    return script





@router.post("/{script_id}/generate-video")
async def generate_video(
    script_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate audio and video from an approved script.
    
    This is a long-running operation (3-5 minutes) that runs in the background.
    The script must be approved before calling this endpoint.
    """
    # Verify script exists check before queueing
    service = ScriptService(db)
    
    try:
        # Stage 1: Initialize (Generate Audio + DB Record) - Await this!
        video = await service.initialize_video_generation(script_id)
        
        # Stage 2: Finalize (Render Video) - Background
        # Pass the ID to the background task (method inside class)
        # Note: We can't pass instance method easily to background task if it needs fresh DB.
        # So we use the static-like method we defined or a standalone wrapper.
        pass
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # Queue background task using a class method wrapper or similar?
    # Actually, we defined finalize_video_generation in ScriptService.
    # It creates its own session. So we can run it.
    background_tasks.add_task(service.finalize_video_generation, video.id)
    
    return {
        "status": "processing",
        "script_id": script_id,
        "video_id": video.id, # KEY FIX: Return the ID!
        "message": "Video generation started. Redirecting..."
    }


@router.post("/{script_id}/reject-with-reason")
async def reject_with_reason(
    script_id: int,
    reason: str,
    db: Session = Depends(get_db)
):
    """
    Reject script with a reason.
    
    Updates script_status to 'rejected' and stores rejection reason.
    """
    service = ScriptService(db)
    script = service.reject_script_with_reason(script_id, reason)
    
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    return script


@router.post("/{script_id}/regenerate")
async def regenerate_script(
    script_id: int,
    db: Session = Depends(get_db)
):
    """
    Regenerate script from the same article.
    
    Marks old script as rejected and creates a new one.
    """
    service = ScriptService(db)
    new_script = await service.regenerate_script(script_id)
    
    if not new_script:
        raise HTTPException(status_code=404, detail="Script or article not found")
    
    return new_script
