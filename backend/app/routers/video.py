from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import get_db
from app.services.enhanced_video_service import EnhancedVideoCompositionService
from app.schemas.video import VideoRenderRequest, VideoResponse, VideoListResponse
from app.models import Video

router = APIRouter()

def get_video_service(db: Session = Depends(get_db)):
    return EnhancedVideoCompositionService(db)

@router.post("/render", response_model=VideoResponse)
def render_video(
    request: VideoRenderRequest,
    background_tasks: BackgroundTasks,
    service: EnhancedVideoCompositionService = Depends(get_video_service)
):
    """
    Trigger video generation.
    """
    try:
        # Create task (pending status)
        video = service.create_video_task(
            script_id=request.script_id,
            audio_id=request.audio_id,
            background_style=request.background_style or "gradient"
        )
        
        # Schedule background processing
        background_tasks.add_task(service.process_video, video.id)
        
        return video
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start video rendering: {str(e)}")

@router.get("/stats")
def get_video_stats(db: Session = Depends(get_db)):
    """Get video statistics for dashboard."""
    from sqlalchemy import func
    
    # Total count
    total = db.query(Video).count()
    
    # Count by status
    status_counts = db.query(
        Video.status,
        func.count(Video.id).label('count')
    ).group_by(Video.status).all()
    
    by_status = {status: count for status, count in status_counts}
    
    return {
        "total": total,
        "by_status": by_status
    }

# Video Validation Endpoints - Must come before /{video_id} to avoid path conflicts

@router.get("/pending", response_model=VideoListResponse)
async def get_pending_videos(db: Session = Depends(get_db)):
    """
    Get all videos pending validation.
    
    Returns list of videos with video_status='pending'.
    """
    from app.services.video_service import VideoCompositionService
    service = VideoCompositionService(db)
    videos = service.get_pending_videos()
    
    # Add download URLs
    for video in videos:
        video.download_url = f"/api/video/{video.id}/download"
    
    return {"videos": videos, "total": len(videos)}


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: int,
    db: Session = Depends(get_db)
):
    """Get video details."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
        
    # Add computed download URL
    video.download_url = f"/api/video/{video.id}/download"
    return video

@router.get("/{video_id}/download")
def download_video(
    video_id: int,
    db: Session = Depends(get_db)
):
    """Download the generated video file."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
        
    if video.status != "completed" or not video.file_path:
        raise HTTPException(status_code=400, detail="Video is not ready for download")
        
    file_path = Path(video.file_path)
    if not file_path.exists():
         # Try resolving relative path against CWD if needed, though service stores it reasonably
        full_path = Path.cwd() / file_path
        if full_path.exists():
            file_path = full_path
        else:
            raise HTTPException(status_code=404, detail=f"Video file not found on disk: {file_path}")
            
    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=f"video_{video.script_id}.mp4"
    )

@router.get("", response_model=VideoListResponse)
def list_videos(
    script_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List generated videos."""
    query = db.query(Video)
    
    if script_id:
        query = query.filter(Video.script_id == script_id)
        
    total = query.count()
    videos = query.order_by(Video.created_at.desc()).offset(offset).limit(limit).all()
    
    # Compute download URLs
    for video in videos:
        video.download_url = f"/api/video/{video.id}/download"
        
    return {"videos": videos, "total": total}


@router.get("/{video_id}/detail")
def get_video_detail(
    video_id: int,
    db: Session = Depends(get_db)
):
    """
    Get video with full metadata including script and article.
    
    Returns video, script, and article data for review.
    """
    from app.services.video_service import VideoCompositionService
    service = VideoCompositionService(db)
    result = service.get_video_with_metadata(video_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Video not found")
    
    video = result["video"]
    script = result["script"]
    article = result["article"]
    
    return {
        "video": {
            "id": video.id,
            "file_path": video.file_path,
            "download_url": f"/api/video/{video.id}/download",
            "duration": video.duration,
            "file_size": video.file_size,
            "youtube_title": video.youtube_title,
            "youtube_description": video.youtube_description,
            "youtube_tags": video.youtube_tags,
            "thumbnail_path": video.thumbnail_path,
            "end_screen_path": video.end_screen_path,
            "validation_status": video.validation_status,
            "status": video.status,  # Add render status (rendering, completed, failed)
            "error_message": video.error_message,  # Add error details if failed
            "created_at": video.created_at,
            "updated_at": video.updated_at
        },
        "script": {
            "id": script.id,
            "catchy_title": script.catchy_title,
            "content_type": script.content_type,
            "video_description": script.video_description,
            "hashtags": script.hashtags
        } if script else None,
        "article": {
            "id": article.id,
            "title": article.title,
            "url": article.url
        } if article else None
    }


class MetadataUpdateRequest(BaseModel):
    """Request body for updating video metadata."""
    youtube_title: Optional[str] = None
    youtube_description: Optional[str] = None
    hashtags: Optional[List[str]] = None
    youtube_tags: Optional[List[str]] = None


@router.put("/{video_id}/metadata")
def update_video_metadata(
    video_id: int,
    body: MetadataUpdateRequest,
    service: EnhancedVideoCompositionService = Depends(get_video_service)
):
    """
    Update video metadata for YouTube upload.
    
    Accepts a JSON body with title (max 100 chars), description (max 5000 chars),
    hashtags, and search tags as proper arrays.
    """
    video = service.update_video_metadata(
        video_id=video_id,
        youtube_title=body.youtube_title,
        youtube_description=body.youtube_description,
        hashtags=body.hashtags,
        youtube_tags=body.youtube_tags
    )
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return video


class ApprovePublishRequest(BaseModel):
    """Request body for approve & publish."""
    youtube_title: Optional[str] = None
    youtube_description: Optional[str] = None
    hashtags: Optional[List[str]] = None
    youtube_tags: Optional[List[str]] = None
    privacy_status: str = "private"  # private, unlisted, or public


@router.post("/{video_id}/approve")
def approve_video(
    video_id: int,
    body: Optional[ApprovePublishRequest] = None,
    service: EnhancedVideoCompositionService = Depends(get_video_service),
    db: Session = Depends(get_db)
):
    """
    Approve video and optionally publish to YouTube.
    
    Workflow:
    1. Persist final metadata from the UI to the database
    2. Mark as approved
    3. Upload to YouTube as Private (safe zone) via Data API v3
    4. Return YouTube URL for final review
    """
    import logging
    logger = logging.getLogger(__name__)
    
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Step 1: Persist any final metadata edits from the UI
    if body:
        if body.youtube_title is not None:
            video.youtube_title = body.youtube_title[:100]
        if body.youtube_description is not None:
            video.youtube_description = body.youtube_description[:5000]
        if body.youtube_tags is not None:
            video.youtube_tags = body.youtube_tags
        if body.hashtags is not None and video.script:
            video.script.hashtags = body.hashtags
    
    # Step 2: Approve locally
    from datetime import datetime, timezone
    video.validation_status = "approved"
    video.approved_at = datetime.now(timezone.utc)
    db.commit()
    
    # Step 3: Attempt YouTube upload
    youtube_result = None
    upload_error = None
    
    try:
        from app.services.youtube_upload_service import YouTubeUploadService
        
        if not video.file_path:
            raise FileNotFoundError("Video file path not set")
        
        uploader = YouTubeUploadService()
        
        title = video.youtube_title or video.script.catchy_title or "Untitled"
        description = video.youtube_description or video.script.video_description or ""
        tags = video.youtube_tags or []
        privacy = body.privacy_status if body else "private"
        
        youtube_result = uploader.upload_video(
            file_path=video.file_path,
            title=title,
            description=description,
            tags=tags,
            category_id="27",  # Education
            privacy_status=privacy,
            is_short=True,
        )
        
        # Persist YouTube response
        video.youtube_video_id = youtube_result["youtube_video_id"]
        video.youtube_url = youtube_result["youtube_url"]
        video.uploaded_to_youtube = True
        db.commit()
        
        logger.info(f"✅ Video {video_id} uploaded to YouTube: {youtube_result['youtube_url']}")
        
    except FileNotFoundError as e:
        upload_error = f"YouTube upload skipped: {str(e)}"
        logger.warning(upload_error)
    except Exception as e:
        upload_error = f"YouTube upload failed (video still approved locally): {str(e)}"
        logger.warning(upload_error)
    
    response = {
        "status": "approved",
        "video_id": video.id,
        "message": "Video approved and ready for upload",
    }
    
    if youtube_result:
        response.update({
            "youtube_uploaded": True,
            "youtube_video_id": youtube_result["youtube_video_id"],
            "youtube_url": youtube_result["youtube_url"],
            "privacy_status": youtube_result["privacy_status"],
            "message": f"Video approved and uploaded to YouTube ({youtube_result['privacy_status']})",
        })
    elif upload_error:
        response.update({
            "youtube_uploaded": False,
            "upload_warning": upload_error,
            "message": "Video approved locally. YouTube upload requires OAuth setup.",
        })
    
    return response


@router.post("/{video_id}/reject")
def reject_video(
    video_id: int,
    reason: str,
    service: EnhancedVideoCompositionService = Depends(get_video_service)
):
    """
    Reject video with a reason.
    
    Updates validation_status to 'rejected' and stores rejection reason.
    """
    video = service.reject_video(video_id, reason)
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return video


@router.post("/{video_id}/generate-metadata")
async def generate_video_metadata(
    video_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate SEO-optimized YouTube metadata using LLM.
    
    Returns catchy title, description with hashtags, and searchable tags.
    """
    from app.services.metadata_generation_service import MetadataGenerationService
    
    # Get video with script and article data
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    script = video.script
    article = script.article if script else None
    
    if not article:
        raise HTTPException(status_code=400, detail="No article data available")
    
    try:
        service = MetadataGenerationService()
        
        # Get script content for better context
        script_text = None
        if script and script.scenes:
            script_text = " ".join(s.get("text", "") for s in script.scenes)
        
        # Extract book metadata for book reviews
        book_author = None
        takeaways = None
        content_type = script.content_type if script else "daily_update"
        
        if content_type == "book_review" and article.book_source_id:
            book = article.book_source
            if book:
                book_author = book.author
                takeaways = book.key_takeaways
        
        metadata = await service.generate_metadata(
            article_title=article.title,
            article_description=article.description or article.summary or "",
            script_content=script_text,
            content_type=content_type,
            book_author=book_author,
            takeaways=takeaways,
        )
        
        return {
            "success": True,
            "metadata": {
                "title": metadata.title,
                "description": metadata.description,
                "hashtags": metadata.hashtags,
                "tags": metadata.tags
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate metadata: {str(e)}")


@router.get("/{video_id}/thumbnail-prompt")
async def get_thumbnail_prompt(
    video_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the auto-generated thumbnail prompt for preview/editing.
    
    Returns the prompt that would be used for thumbnail generation.
    """
    from app.services.thumbnail_generation_service import ThumbnailGenerationService
    
    # Get video with script and article data
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    script = video.script
    article = script.article if script else None
    
    if not article:
        raise HTTPException(status_code=400, detail="No article data available")
    
    try:
        service = ThumbnailGenerationService()
        
        prompt = service.get_thumbnail_prompt(
            article_title=article.title,
            article_description=article.description or article.summary or "",
            content_type=script.content_type if script else "daily_update"
        )
        
        return {
            "success": True,
            "prompt": prompt,
            "article_title": article.title
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get prompt: {str(e)}")


@router.post("/{video_id}/generate-thumbnail")
async def generate_video_thumbnail(
    video_id: int,
    custom_prompt: str = None,
    db: Session = Depends(get_db)
):
    """
    Generate AI thumbnail using Gemini image generation (NanaBanana).
    
    Args:
        custom_prompt: Optional custom prompt (uses auto-generated if not provided)
    
    Returns path to generated thumbnail.
    """
    from app.services.thumbnail_generation_service import ThumbnailGenerationService
    
    # Get video with script and article data
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    script = video.script
    article = script.article if script else None
    
    if not article:
        raise HTTPException(status_code=400, detail="No article data available")
    
    try:
        service = ThumbnailGenerationService()
        
        thumbnail_path = await service.generate_thumbnail(
            article_title=article.title,
            article_description=article.description or article.summary or "",
            content_type=script.content_type if script else "daily_update",
            custom_prompt=custom_prompt
        )
        
        if thumbnail_path:
            # Update video record with thumbnail path
            video.thumbnail_path = str(thumbnail_path)
            db.commit()
            
            return {
                "success": True,
                "thumbnail_path": str(thumbnail_path),
                "message": "Thumbnail generated successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Thumbnail generation returned no image")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate thumbnail: {str(e)}")


