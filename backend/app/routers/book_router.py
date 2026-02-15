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


class GenerateVideoRequest(BaseModel):
    """Request to generate a video directly from a book."""
    angle_index: int = 0
    custom_angle: Optional[str] = None
    project_folder: Optional[str] = None  # New field for asset override


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
    """
    try:
        book = await service.get_or_create_book(book_data.model_dump())
        return BookDetail.model_validate(book)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to select book: {str(e)}")


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


@router.post("/{book_id}/generate-video")
async def generate_book_video(
    book_id: int,
    request: GenerateVideoRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    One-click video generation from a book.
    
    Chains: Article → Script → TTS Audio → Video Render.
    The video render runs in the background. Returns video_id for polling.
    """
    from app.services.script_service import ScriptService
    from app.services.audio_service import AudioService
    from app.services.enhanced_video_service import EnhancedVideoCompositionService
    from app.config import settings
    
    google_api_key = os.getenv("GOOGLE_BOOKS_API_KEY") or settings.google_api_key
    book_service = BookService(db, google_books_api_key=google_api_key)
    
    try:
        # Step 1: Create article from book (if not already created)
        logger.info(f"[BookVideo] Step 1: Creating article from book {book_id}")
        article = await book_service.create_article_from_book(
            book_id,
            angle_index=request.angle_index,
            custom_angle=request.custom_angle
        )
        logger.info(f"[BookVideo] Article created: {article.id} - {article.title}")
        
        # Step 2: Generate script
        logger.info(f"[BookVideo] Step 2: Generating script for article {article.id}")
        script_service = ScriptService(db)
        script = await script_service.generate_script(
            article=article,
            style="engaging",
            target_duration=85  # Book reviews V2: 85s with 7-8 scenes
        )
        logger.info(f"[BookVideo] Script created: {script.id} (content_type={script.content_type})")
        
        # Step 3: Auto-approve the script
        logger.info(f"[BookVideo] Step 3: Auto-approving script {script.id}")
        script = script_service.approve_script(script.id)
        
        # Step 4: Generate TTS audio
        logger.info(f"[BookVideo] Step 4: Generating TTS audio")
        audio_service = AudioService(db)
        audio = await audio_service.generate_audio_from_script(
            script_id=script.id,
            tts_provider="openai"
        )
        logger.info(f"[BookVideo] Audio generated: {audio.id}")
        
        # Step 5: Create video task
        logger.info(f"[BookVideo] Step 5: Creating video task")
        video_service = EnhancedVideoCompositionService(db)
        video = video_service.create_video_task(
            script_id=script.id,
            audio_id=audio.id,
            background_style="scenes",
            project_folder=request.project_folder  # Pass to video service
        )
        db.commit()
        db.refresh(video)
        logger.info(f"[BookVideo] Video task created: {video.id}")
        
        # Step 6: Queue video render in background
        logger.info(f"[BookVideo] Step 6: Queuing background render for video {video.id}")
        background_tasks.add_task(
            script_service.finalize_video_generation, video.id
        )
        
        return {
            "status": "processing",
            "book_id": book_id,
            "article_id": article.id,
            "script_id": script.id,
            "video_id": video.id,
            "message": "Book review video generation started! Script generated and video rendering in background."
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
