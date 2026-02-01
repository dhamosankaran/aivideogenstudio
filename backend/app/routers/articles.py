"""
Article management API endpoints.

Provides article listing, filtering, analysis, and ranking.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from app.database import get_db
from app.schemas import ArticleResponse, ArticleRankingResponse, JobResponse
from app.models import Article
from app.services.content_analyzer import ContentAnalyzer

router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.get("/", response_model=List[ArticleResponse])
async def list_articles(
    analyzed: Optional[bool] = None,
    selected: Optional[bool] = None,
    days: Optional[int] = 7,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """
    List articles with optional filters.
    
    Args:
        analyzed: Filter by analysis status
        selected: Filter by selection status
        days: Only include articles from last N days
        limit: Maximum number of results
    """
    query = db.query(Article)
    
    # Apply filters
    if analyzed is not None:
        if analyzed:
            query = query.filter(Article.analyzed_at.isnot(None))
        else:
            query = query.filter(Article.analyzed_at.is_(None))
    
    if selected is not None:
        query = query.filter(Article.is_selected == selected)
    
    if days:
        since = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Article.created_at >= since)
    
    # Order by creation date (newest first)
    articles = query.order_by(Article.created_at.desc()).limit(limit).all()
    
    return articles


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single article by ID.
    
    Args:
        article_id: Article ID
    """
    article = db.query(Article).filter(Article.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return article


@router.get("/top", response_model=ArticleRankingResponse)
async def get_top_articles(
    limit: int = Query(5, le=20),
    days: int = Query(7, le=30),
    min_score: Optional[float] = Query(None, ge=0, le=10),
    db: Session = Depends(get_db)
):
    """
    Get top-ranked articles.
    
    Args:
        limit: Number of articles to return
        days: Look back this many days
        min_score: Minimum final_score threshold
    """
    analyzer = ContentAnalyzer(db)
    articles = analyzer.get_top_articles(
        limit=limit,
        days=days,
        min_score=min_score
    )
    
    top_score = articles[0].final_score if articles else None
    
    return ArticleRankingResponse(
        articles=articles,
        total=len(articles),
        top_score=top_score
    )


@router.post("/analyze", response_model=JobResponse)
async def analyze_articles(
    background_tasks: BackgroundTasks,
    limit: Optional[int] = Query(None, description="Limit number of articles to analyze"),
    db: Session = Depends(get_db)
):
    """
    Trigger LLM analysis of unanalyzed articles.
    
    This runs as a background task.
    
    Args:
        limit: Optional limit on number of articles to analyze
    """
    job_id = str(uuid.uuid4())
    
    # Add background task
    background_tasks.add_task(
        _analyze_articles_task,
        db,
        job_id,
        limit
    )
    
    return JobResponse(
        job_id=job_id,
        status="pending",
        message=f"Article analysis started",
        created_at=datetime.utcnow()
    )


@router.post("/{article_id}/select", response_model=ArticleResponse)
async def select_article(
    article_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark an article as selected for video generation.
    
    Args:
        article_id: Article ID
    """
    article = db.query(Article).filter(Article.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article.is_selected = True
    db.commit()
    db.refresh(article)
    
    return article


@router.post("/import-video", response_model=ArticleResponse)
async def import_video(
    video_url: str,
    feed_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Import a YouTube video as an article.
    
    Uses Gemini multimodal to analyze the video and extract key information.
    
    Args:
        video_url: YouTube video URL
        feed_id: Optional feed ID to associate with
    """
    from app.services.video_service import VideoService
    
    service = VideoService(db)
    
    try:
        article = await service.import_video(
            video_url=video_url,
            feed_id=feed_id
        )
        
        return article
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import video: {str(e)}"
        )


async def _analyze_articles_task(db: Session, job_id: str, limit: Optional[int]):
    """Background task for article analysis."""
    # Get unanalyzed articles
    query = db.query(Article).filter(Article.analyzed_at.is_(None))
    
    if limit:
        query = query.limit(limit)
    
    articles = query.all()
    
    print(f"Job {job_id}: Analyzing {len(articles)} articles")
    
    # Analyze
    analyzer = ContentAnalyzer(db)
    analyzed = await analyzer.batch_analyze(articles)
    
    print(f"Job {job_id}: Successfully analyzed {len(analyzed)} articles")
