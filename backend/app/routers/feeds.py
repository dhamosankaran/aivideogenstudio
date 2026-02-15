"""
Feed management API endpoints.

Provides CRUD operations for RSS feeds and feed synchronization.
"""

from fastapi import APIRouter, Depends, HTTPException,BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import FeedCreate, FeedUpdate, FeedResponse, JobResponse
from app.services.feed_service import FeedService
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api/feeds", tags=["feeds"])


@router.get("/", response_model=List[FeedResponse])
async def list_feeds(
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    List all RSS feeds.
    
    Args:
        active_only: If True, only return active feeds
    """
    service = FeedService(db)
    feeds = service.get_feeds(active_only=active_only)
    return feeds


@router.post("/", response_model=FeedResponse, status_code=201)
async def create_feed(
    feed_data: FeedCreate,
    db: Session = Depends(get_db)
):
    """
    Add a new RSS feed.
    
    Args:
        feed_data: Feed creation data
    """
    service = FeedService(db)
    
    # Check if URL already exists
    existing_feeds = service.get_feeds()
    if any(f.url == str(feed_data.url) for f in existing_feeds):
        raise HTTPException(
            status_code=400,
            detail=f"Feed with URL {feed_data.url} already exists"
        )
    
    feed = service.add_feed(
        name=feed_data.name,
        url=str(feed_data.url),
        category=feed_data.category
    )
    
    return feed


@router.put("/{feed_id}", response_model=FeedResponse)
async def update_feed(
    feed_id: int,
    feed_data: FeedUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing feed.
    
    Args:
        feed_id: Feed ID
        feed_data: Updated feed data
    """
    service = FeedService(db)
    
    # Build update dict (only include provided fields)
    update_data = feed_data.model_dump(exclude_unset=True)
    
    feed = service.update_feed(feed_id, **update_data)
    
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    return feed


@router.delete("/{feed_id}", status_code=204)
async def delete_feed(
    feed_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a feed and all its articles.
    
    Args:
        feed_id: Feed ID
    """
    service = FeedService(db)
    
    success = service.delete_feed(feed_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    return None

@router.post("/{feed_id}/fetch", response_model=JobResponse)
async def fetch_feed(
    feed_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Fetch articles from a specific feed.
    
    Args:
        feed_id: Feed ID to fetch from
    """
    service = FeedService(db)
    
    # Verify feed exists
    feeds = service.get_feeds()
    feed = next((f for f in feeds if f.id == feed_id), None)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    job_id = str(uuid.uuid4())
    
    # Add background task for single feed
    background_tasks.add_task(
        _fetch_single_feed_task,
        db,
        feed_id,
        job_id
    )
    
    return JobResponse(
        job_id=job_id,
        status="pending",
        message=f"Fetching articles from feed {feed_id}",
        created_at=datetime.now(timezone.utc)
    )

async def _fetch_single_feed_task(db: Session, feed_id: int, job_id: str):
    """Background task for single feed fetch."""
    service = FeedService(db)
    count = await service.sync_single_feed(feed_id)
    print(f"Job {job_id}: Fetched {count} new articles from feed {feed_id}")


@router.post("/sync", response_model=JobResponse)
async def sync_feeds(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger feed synchronization as a background task.
    
    Fetches all active feeds and saves new articles.
    """
    job_id = str(uuid.uuid4())
    
    # Add background task
    background_tasks.add_task(
        _sync_feeds_task,
        db,
        job_id
    )
    
    return JobResponse(
        job_id=job_id,
        status="pending",
        message="Feed sync started",
        created_at=datetime.now(timezone.utc)
    )


async def _sync_feeds_task(db: Session, job_id: str):
    """Background task for feed synchronization."""
    service = FeedService(db)
    count = await service.sync_feeds()
    print(f"Job {job_id}: Synced {count} new articles")
