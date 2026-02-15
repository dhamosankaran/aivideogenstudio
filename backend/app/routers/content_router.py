"""
Content curation API router for AIVideoGen.

Provides endpoints for browsing, filtering, and selecting articles for video generation.
"""

from typing import List, Optional
from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.services.content_service import ContentService
from app.models import Article


router = APIRouter(prefix="/api/content", tags=["content"])


# Pydantic models for request/response
class ArticleListResponse(BaseModel):
    """Response model for article list."""
    items: List[dict]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        from_attributes = True


class SelectArticlesRequest(BaseModel):
    """Request model for selecting articles."""
    article_ids: List[int]


class DeleteArticlesRequest(BaseModel):
    """Request model for deleting articles."""
    article_ids: List[int]


class GenerateScriptsRequest(BaseModel):
    """Request model for generating scripts."""
    article_ids: List[int]
    content_type: Optional[str] = "daily_update"


class ManualImportRequest(BaseModel):
    """Request model for manual content import."""
    title: str
    content: str
    source_url: Optional[str] = None
    content_type: Optional[str] = "daily_update"


class ManualImportResponse(BaseModel):
    """Response model for manual content import."""
    id: int
    title: str
    word_count: int
    estimated_duration: float
    message: str
    analyzed: bool = False


@router.get("/articles")
async def list_articles(
    source: Optional[str] = Query(None, description="Filter by feed source"),
    date_range: Optional[str] = Query("last_7_days", description="Date range filter"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in title/description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    List articles with filters and pagination.
    
    Query Parameters:
    - source: Filter by feed name (e.g., "TechCrunch", "arXiv")
    - date_range: "today", "last_7_days", "last_30_days", "all"
    - content_type: "daily_update", "big_tech", "leader_quote", "arxiv_paper"
    - status: "unprocessed", "has_script", "has_video"
    - search: Search term for title/description
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    
    Returns:
    - items: List of articles
    - total: Total count
    - page: Current page
    - page_size: Items per page
    - total_pages: Total pages
    """
    service = ContentService(db)
    result = service.list_articles(
        source=source,
        date_range=date_range,
        content_type=content_type,
        status=status,
        search=search,
        page=page,
        page_size=page_size
    )
    
    # Convert SQLAlchemy models to dicts
    items_dict = []
    for article in result["items"]:
        # Get feed name - detect manual imports by URL pattern
        if article.url and article.url.startswith("manual://"):
            feed_name = "Manual Import"
        elif article.feed:
            feed_name = article.feed.name
        else:
            feed_name = "Unknown"
        
        items_dict.append({
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "description": article.description,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "source": feed_name,
            "relevance_score": article.relevance_score,
            "suggested_content_type": article.suggested_content_type,
            "is_selected": article.is_selected,
            "is_processed": article.is_processed,
            "key_points": article.key_points,
            "key_topics": article.key_topics,
            "why_interesting": article.why_interesting,
            "status": "video_created" if article.scripts and any(s.status == "approved" for s in article.scripts) 
                     else "script_generated" if article.is_processed 
                     else "unprocessed"
        })
    
    return {
        "items": items_dict,
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total_pages": result["total_pages"]
    }


@router.get("/articles/{article_id}")
async def get_article(article_id: int, db: Session = Depends(get_db)):
    """
    Get full article details.
    
    Returns complete article information including content, analysis, and related scripts.
    """
    service = ContentService(db)
    article = service.get_article(article_id)
    
    if not article:
        raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
    
    return {
        "id": article.id,
        "title": article.title,
        "url": article.url,
        "author": article.author,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "description": article.description,
        "content": article.content,
        "source": article.feed.name if article.feed else "Unknown",
        "summary": article.summary,
        "key_points": article.key_points,
        "key_topics": article.key_topics,
        "why_interesting": article.why_interesting,
        "relevance_score": article.relevance_score,
        "suggested_content_type": article.suggested_content_type,
        "is_selected": article.is_selected,
        "is_processed": article.is_processed,
        "scripts": [{"id": s.id, "status": s.status} for s in article.scripts] if article.scripts else []
    }


@router.post("/articles/select")
async def select_articles(
    request: SelectArticlesRequest,
    db: Session = Depends(get_db)
):
    """
    Mark articles as selected for script generation.
    
    Request Body:
    - article_ids: List of article IDs to select
    
    Returns:
    - selected: Number of articles selected
    - article_ids: List of selected article IDs
    """
    service = ContentService(db)
    result = service.select_articles(request.article_ids)
    return result


@router.post("/articles/delete")
async def delete_articles(
    request: DeleteArticlesRequest,
    db: Session = Depends(get_db)
):
    """
    Delete selected articles.
    
    Request Body:
    - article_ids: List of article IDs to delete
    
    Returns:
    - deleted: Number of articles deleted
    """
    service = ContentService(db)
    try:
        result = service.delete_articles(request.article_ids)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete articles: {str(e)}")


@router.post("/scripts/generate")
async def generate_scripts(
    request: GenerateScriptsRequest,
    db: Session = Depends(get_db)
):
    """
    Generate scripts from selected articles.
    
    Request Body:
    - article_ids: List of article IDs to generate scripts from
    - content_type: Content type for scripts (default: "daily_update")
    
    Returns:
    - scripts_created: Number of scripts created
    - script_ids: List of created script IDs
    - errors: List of errors (if any)
    """
    service = ContentService(db)
    result = await service.generate_scripts(
        article_ids=request.article_ids,
        content_type=request.content_type
    )
    return result


@router.post("/articles/{article_id}/analyze")
async def analyze_article(article_id: int, db: Session = Depends(get_db)):
    """
    Analyze article and generate AI insights.
    
    Uses LLM to calculate relevance score, suggest content type, and extract key points.
    
    Returns:
    - score: Relevance score (0-10)
    - content_type: Suggested content type
    - key_points: Extracted key points
    - tags: Generated tags
    """
    service = ContentService(db)
    
    try:
        result = service.analyze_article(article_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sources")
async def get_sources(db: Session = Depends(get_db)):
    """
    Get list of all feed sources.
    
    Returns list of feed names for filtering.
    """
    service = ContentService(db)
    sources = service.get_sources()
    return {"sources": sources}


@router.get("/content-types")
async def get_content_types(db: Session = Depends(get_db)):
    """
    Get list of available content types.
    
    Returns list of content types for filtering and script generation.
    """
    service = ContentService(db)
    content_types = service.get_content_types()
    return {"content_types": content_types}


@router.post("/articles/manual", response_model=ManualImportResponse)
async def import_manual_content(
    request: ManualImportRequest,
    db: Session = Depends(get_db)
):
    """
    Import manually pasted content as an article with auto-analysis.
    
    Request Body:
    - title: Article title (required)
    - content: Full article content (required)
    - source_url: Optional source URL for reference
    - content_type: Content type (default: "daily_update")
    
    Returns:
    - id: Created article ID
    - title: Article title
    - word_count: Number of words in content
    - estimated_duration: Estimated video duration in seconds
    - message: Success message
    - analyzed: Whether LLM analysis was performed
    """
    from app.services.content_analyzer import ContentAnalyzer
    
    # Validate input length
    if len(request.title.strip()) < 10:
        raise HTTPException(status_code=400, detail="Title must be at least 10 characters")
    if len(request.content.strip()) < 100:
        raise HTTPException(status_code=400, detail="Content must be at least 100 characters")
    if len(request.content) > 15000:
        raise HTTPException(status_code=400, detail="Content must be less than 15,000 characters")
    
    # Generate unique URL if not provided
    url = request.source_url.strip() if request.source_url else f"manual://import/{uuid.uuid4().hex[:12]}"
    
    # Check for duplicate URL
    existing = db.query(Article).filter(Article.url == url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Content with this URL already exists")
    
    # Calculate word count and duration
    word_count = len(request.content.split())
    estimated_duration = word_count / 2.5  # ~150 words per minute = 2.5 words per second
    
    # Create description from content (first 300 chars)
    description = request.content[:300] + "..." if len(request.content) > 300 else request.content
    
    # Create article
    article = Article(
        title=request.title.strip(),
        content=request.content.strip(),
        url=url,
        description=description,
        suggested_content_type=request.content_type,
        published_at=datetime.now(timezone.utc),
        is_processed=False,
        is_selected=False
    )
    
    db.add(article)
    db.commit()
    db.refresh(article)
    
    # Auto-analyze using LLM
    analyzed = False
    try:
        analyzer = ContentAnalyzer(db)
        scores = await analyzer.analyze_article(article)
        
        if scores:
            article.relevance_score = scores.relevance_score
            article.engagement_score = scores.engagement_score
            article.recency_score = scores.recency_score
            article.uniqueness_score = scores.uniqueness_score
            article.category = scores.category
            article.key_topics = scores.key_topics
            article.why_interesting = scores.why_interesting
            article.final_score = analyzer._calculate_final_score(scores)
            article.analyzed_at = datetime.now(timezone.utc)
            db.commit()
            analyzed = True
    except Exception as e:
        # Log but don't fail - user can manually analyze later
        import logging
        logging.getLogger(__name__).warning(f"Auto-analysis failed for article {article.id}: {e}")
    
    return ManualImportResponse(
        id=article.id,
        title=article.title,
        word_count=word_count,
        estimated_duration=round(estimated_duration, 1),
        message="Content imported successfully" + (" and analyzed" if analyzed else " (analysis pending)"),
        analyzed=analyzed
    )
