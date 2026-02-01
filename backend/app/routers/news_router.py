"""
NewsAPI router for real-time news search and import.

Provides endpoints for searching NewsAPI and importing articles.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.services.news_api_service import NewsAPIService
from app.config import settings


router = APIRouter(prefix="/api/news", tags=["news"])


# Pydantic models
class NewsSearchResponse(BaseModel):
    """Response model for news search."""
    status: str
    total_results: int
    articles: List[dict]
    page: int
    page_size: int


class ImportRequest(BaseModel):
    """Request model for importing articles."""
    articles: List[dict]
    source_name: Optional[str] = "NewsAPI"


class ImportResponse(BaseModel):
    """Response model for import operation."""
    imported: int
    duplicates: int
    errors: int
    total_processed: int


class SourceResponse(BaseModel):
    """Response model for news sources."""
    sources: List[dict]


@router.get("/search", response_model=NewsSearchResponse)
async def search_news(
    q: str = Query(..., description="Search query"),
    from_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    language: str = Query("en", description="Language code"),
    sort_by: str = Query("publishedAt", description="Sort by (publishedAt, relevancy, popularity)"),
    page_size: int = Query(10, ge=1, le=100, description="Results per page"),
    page: int = Query(1, ge=1, description="Page number")
):
    """
    Search for news articles using NewsAPI.
    
    Examples:
    - q="Davos" - All Davos coverage
    - q="Jensen Huang" - Specific person
    - q="AI AND regulation" - Combined topics
    - q="Nvidia OR AMD" - Multiple companies
    """
    try:
        service = NewsAPIService()
        result = service.search_articles(
            query=q,
            from_date=from_date,
            to_date=to_date,
            language=language,
            sort_by=sort_by,
            page_size=page_size,
            page=page
        )
        
        return NewsSearchResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/headlines", response_model=NewsSearchResponse)
async def get_top_headlines(
    category: Optional[str] = Query(None, description="Category (business, technology, etc.)"),
    country: str = Query("us", description="Country code"),
    page_size: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1)
):
    """
    Get top headlines from NewsAPI.
    
    Categories: business, entertainment, general, health, science, sports, technology
    """
    try:
        service = NewsAPIService()
        result = service.get_top_headlines(
            category=category,
            country=country,
            page_size=page_size,
            page=page
        )
        
        return NewsSearchResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch headlines: {str(e)}")


@router.post("/import", response_model=ImportResponse)
async def import_articles(
    request: ImportRequest,
    db: Session = Depends(get_db)
):
    """
    Import NewsAPI articles to the database.
    
    Articles will be deduplicated by URL.
    """
    try:
        service = NewsAPIService()
        result = service.import_articles_to_db(
            articles=request.articles,
            db=db,
            source_name=request.source_name
        )
        
        return ImportResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/sources", response_model=SourceResponse)
async def get_sources(
    category: Optional[str] = Query(None, description="Filter by category"),
    language: str = Query("en", description="Filter by language")
):
    """
    Get available news sources from NewsAPI.
    
    Returns list of sources with metadata.
    """
    try:
        service = NewsAPIService()
        sources = service.get_sources(category=category, language=language)
        
        return SourceResponse(sources=sources)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sources: {str(e)}")


@router.get("/test")
async def test_newsapi():
    """
    Test NewsAPI connection and configuration.
    
    Returns status and sample search result.
    """
    try:
        service = NewsAPIService()
        
        # Test with a simple search
        result = service.search_articles(
            query="AI",
            page_size=1
        )
        
        return {
            "status": "ok",
            "api_configured": True,
            "total_results": result.get("total_results", 0),
            "message": "NewsAPI is working correctly"
        }
        
    except ValueError as e:
        return {
            "status": "error",
            "api_configured": False,
            "message": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "api_configured": True,
            "message": f"API error: {str(e)}"
        }
