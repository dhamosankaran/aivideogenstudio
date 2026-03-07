"""
Book router for book review shorts feature.

Provides endpoints for searching books, analyzing them with LLM,
and creating articles for the video pipeline.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import logging

from app.database import get_db
from app.services.book_service import BookService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/books", tags=["books"])


# Pydantic schemas
class BookSearchResult(BaseModel):
    """Book search result schema."""
    open_library_key: str
    title: str
    author: Optional[str] = None
    first_publish_year: Optional[int] = None
    subjects: List[str] = []
    cover_url: Optional[str] = None
    page_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class KeyTakeaway(BaseModel):
    """Key takeaway from book analysis."""
    point: str
    hook: str
    viral_score: int


class BookDetail(BaseModel):
    """Full book details with analysis."""
    id: int
    open_library_key: str
    google_books_id: Optional[str] = None
    title: str
    author: Optional[str] = None
    first_publish_year: Optional[int] = None
    description: Optional[str] = None
    subjects: List[str] = []
    cover_url: Optional[str] = None
    page_count: Optional[int] = None
    key_takeaways: Optional[List[KeyTakeaway]] = None
    suggested_angles: Optional[List[str]] = None
    analysis_status: str
    error_message: Optional[str] = None
    created_at: datetime
    analyzed_at: Optional[datetime] = None
    # True when the book was already in the library (not newly added)
    already_existed: Optional[bool] = False
    
    class Config:
        from_attributes = True


class BookSelectRequest(BaseModel):
    """Request to create article from book."""
    angle_index: int = 0
    custom_angle: Optional[str] = None


class ArticleCreatedResponse(BaseModel):
    """Response after creating article."""
    article_id: int
    title: str
    message: str


class GenerateScriptRequest(BaseModel):
    """Request to generate a script from a book (for preview before video)."""
    angle_index: int = 0
    custom_angle: Optional[str] = None


class GenerateVideoRequest(BaseModel):
    """Request to generate a video from a book."""
    angle_index: int = 0
    custom_angle: Optional[str] = None
    project_folder: Optional[str] = None
    script_id: Optional[int] = None       # If provided, skip script generation
    tts_provider: Optional[str] = "openai" # openai, google, elevenlabs
    voice: Optional[str] = None            # Voice ID (uses content-type default if None)
    background_mode: Optional[str] = "auto"  # auto, images_only, videos_only, mixed
    image_source: Optional[str] = "stock"  # stock, ai_generated, auto
    video_source: Optional[str] = "stock"  # stock, veo
    veo_style: Optional[str] = "auto"  # cinematic, whiteboard, illustration, auto


def get_book_service(db: Session = Depends(get_db)) -> BookService:
    """Dependency to get book service instance."""
    from app.config import settings
    # Use specific Books key if available, otherwise fallback to general Google API key
    google_api_key = os.getenv("GOOGLE_BOOKS_API_KEY") or settings.google_api_key
    return BookService(db, google_books_api_key=google_api_key)


@router.get("/search", response_model=List[BookSearchResult])
async def search_books(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=20),
    service: BookService = Depends(get_book_service)
):
    """
    Search for books by title, author, or keywords.
    
    Uses Open Library API with Google Books fallback.
    """
    try:
        results = await service.search_books(q, limit=limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/select", response_model=BookDetail)
async def select_book(
    book_data: BookSearchResult,
    service: BookService = Depends(get_book_service)
):
    """
    Select a book from search results to add to library.
    
    Creates or retrieves BookSource record.
    Returns already_existed=True if the book was already in the library.
    """
    try:
        from app.models import BookSource
        # Check existence BEFORE calling get_or_create so we can flag duplicates
        existing = service.db.query(BookSource).filter(
            BookSource.open_library_key == book_data.open_library_key
        ).first()
        already_existed = existing is not None

        book = await service.get_or_create_book(book_data.model_dump())
        detail = BookDetail.model_validate(book)
        detail.already_existed = already_existed
        return detail
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to select book: {str(e)}")


@router.get("/voice-options")
async def get_voice_options(
    content_type: str = Query("book_review", description="Content type for voice recommendations")
):
    """
    Get available TTS providers, voices, and recommendations for a content type.
    
    Returns provider list with cost labels, voice options per provider,
    and the recommended default based on content type.
    """
    from app.voice_config import get_voice_options_for_frontend
    return get_voice_options_for_frontend(content_type)


@router.get("/{book_id}", response_model=BookDetail)
async def get_book(
    book_id: int,
    service: BookService = Depends(get_book_service)
):
    """Get book details by ID."""
    book = service.get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return BookDetail.model_validate(book)


@router.post("/{book_id}/analyze", response_model=BookDetail)
async def analyze_book(
    book_id: int,
    service: BookService = Depends(get_book_service)
):
    """
    Analyze a book using LLM to generate key takeaways and video angles.
    
    This triggers the AI analysis and may take a few seconds.
    """
    try:
        book = await service.analyze_book(book_id)
        return BookDetail.model_validate(book)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/{book_id}/create-article", response_model=ArticleCreatedResponse)
async def create_article_from_book(
    book_id: int,
    request: BookSelectRequest,
    service: BookService = Depends(get_book_service)
):
    """
    Create an Article from selected book and angle.
    
    The article can then flow through the normal Script → Video pipeline.
    """
    try:
        article = await service.create_article_from_book(
            book_id,
            angle_index=request.angle_index,
            custom_angle=request.custom_angle
        )
        return ArticleCreatedResponse(
            article_id=article.id,
            title=article.title,
            message="Article created successfully. Ready for script generation."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create article: {str(e)}")


@router.post("/{book_id}/prepare-assets")
async def prepare_book_assets(
    book_id: int,
    service: BookService = Depends(get_book_service)
):
    """
    Prepare assets for book video (download cover, create folder).
    
    Returns project folder path and cover image for preview/verification.
    """
    try:
        result = await service.prepare_book_assets(book_id)
        return result
    except Exception as e:
        logger.error(f"Asset preparation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Asset preparation failed: {str(e)}")


@router.post("/{book_id}/generate-script")
async def generate_book_script(
    book_id: int,
    request: GenerateScriptRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a script from a book for preview/review before video generation.
    
    Returns script details (scenes, title, word count, duration) so the user
    can review and approve before committing to TTS + video render costs.
    """
    from app.services.script_service import ScriptService
    from app.config import settings
    
    google_api_key = os.getenv("GOOGLE_BOOKS_API_KEY") or settings.google_api_key
    book_service = BookService(db, google_books_api_key=google_api_key)
    
    try:
        # Step 1: Create article from book
        logger.info(f"[BookScript] Step 1: Creating article from book {book_id}")
        article = await book_service.create_article_from_book(
            book_id,
            angle_index=request.angle_index,
            custom_angle=request.custom_angle
        )
        logger.info(f"[BookScript] Article created: {article.id} - {article.title}")
        
        # Step 2: Generate script
        logger.info(f"[BookScript] Step 2: Generating script for article {article.id}")
        script_service = ScriptService(db)
        script = await script_service.generate_script(
            article=article,
            style="engaging",
            target_duration=85
        )
        logger.info(f"[BookScript] Script created: {script.id} ({script.word_count} words, ~{script.estimated_duration:.0f}s)")
        
        return {
            "script_id": script.id,
            "catchy_title": script.catchy_title,
            "scenes": script.scenes,
            "formatted_script": script.formatted_script,
            "raw_script": script.raw_script,
            "word_count": script.word_count,
            "estimated_duration": script.estimated_duration,
            "content_type": script.content_type,
            "is_valid": script.is_valid,
            "validation_errors": script.validation_errors,
            "article_id": article.id,
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[BookScript] Failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")


@router.post("/{book_id}/generate-video")
async def generate_book_video(
    book_id: int,
    request: GenerateVideoRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate video from a book.
    
    If script_id is provided, uses the existing (reviewed) script.
    Otherwise, generates a new script (legacy one-click flow).
    
    Accepts tts_provider and voice for user-selected TTS configuration.
    """
    from app.services.script_service import ScriptService
    from app.services.audio_service import AudioService
    from app.services.enhanced_video_service import EnhancedVideoCompositionService
    from app.config import settings
    
    google_api_key = os.getenv("GOOGLE_BOOKS_API_KEY") or settings.google_api_key
    book_service = BookService(db, google_books_api_key=google_api_key)
    script_service = ScriptService(db)
    
    try:
        if request.script_id:
            # Use existing reviewed script
            logger.info(f"[BookVideo] Using existing script {request.script_id}")
            script = script_service.get_script(request.script_id)
            if not script:
                raise ValueError(f"Script {request.script_id} not found")
            
            # Approve the script
            script = script_service.approve_script(script.id)
            logger.info(f"[BookVideo] Script {script.id} approved")
        else:
            # Legacy one-click flow: create article + generate script
            logger.info(f"[BookVideo] Step 1: Creating article from book {book_id}")
            article = await book_service.create_article_from_book(
                book_id,
                angle_index=request.angle_index,
                custom_angle=request.custom_angle
            )
            logger.info(f"[BookVideo] Article created: {article.id}")
            
            script = await script_service.generate_script(
                article=article,
                style="engaging",
                target_duration=85
            )
            script = script_service.approve_script(script.id)
            logger.info(f"[BookVideo] Script created and approved: {script.id}")
        
        # Generate TTS audio with user-selected provider and voice
        tts_provider = request.tts_provider or "openai"
        logger.info(f"[BookVideo] Generating TTS audio (provider={tts_provider}, voice={request.voice})")
        audio_service = AudioService(db)
        audio = await audio_service.generate_audio_from_script(
            script_id=script.id,
            tts_provider=tts_provider,
            voice=request.voice
        )
        logger.info(f"[BookVideo] Audio generated: {audio.id}")
        
        # Create video task
        logger.info(f"[BookVideo] Creating video task")
        video_service = EnhancedVideoCompositionService(db)
        video = video_service.create_video_task(
            script_id=script.id,
            audio_id=audio.id,
            background_style="scenes",
            project_folder=request.project_folder,
            background_mode=request.background_mode or "auto",
            image_source=request.image_source or "stock",
            video_source=request.video_source or "stock",
            veo_style=request.veo_style or "auto"
        )
        db.commit()
        db.refresh(video)
        logger.info(f"[BookVideo] Video task created: {video.id}")
        
        # Queue video render in background
        logger.info(f"[BookVideo] Queuing background render for video {video.id}")
        background_tasks.add_task(
            script_service.finalize_video_generation, video.id
        )
        
        return {
            "status": "processing",
            "book_id": book_id,
            "script_id": script.id,
            "video_id": video.id,
            "tts_provider": tts_provider,
            "voice": audio.voice,
            "message": "Book review video generation started! Video rendering in background."
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[BookVideo] Failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")



@router.get("/", response_model=List[BookDetail])
async def list_books(
    limit: int = Query(50, ge=1, le=100),
    service: BookService = Depends(get_book_service)
):
    """List all books in the library."""
    books = service.get_all_books(limit=limit)
    return [BookDetail.model_validate(book) for book in books]
