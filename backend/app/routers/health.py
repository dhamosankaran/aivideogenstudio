"""
Health monitoring endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.cleanup_service import CleanupService
import psutil

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get("/")
def health_check():
    """Basic health check."""
    return {"status": "healthy"}

@router.get("/detailed")
def detailed_health(db: Session = Depends(get_db)):
    """
    Detailed health check with system metrics.
    
    Returns database status, disk space, and memory usage.
    """
    # Database check
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Disk space
    disk = psutil.disk_usage('/')
    disk_info = {
        "free_gb": round(disk.free / (1024**3), 2),
        "total_gb": round(disk.total / (1024**3), 2),
        "percent_used": disk.percent,
        "warning": disk.free / (1024**3) < 1.0
    }
    
    # Memory
    memory = psutil.virtual_memory()
    memory_info = {
        "percent_used": memory.percent,
        "available_gb": round(memory.available / (1024**3), 2)
    }
    
    # Storage breakdown
    cleanup_service = CleanupService(db)
    storage_info = {
        "videos_gb": round(cleanup_service.get_directory_size("data/videos"), 2),
        "audio_gb": round(cleanup_service.get_directory_size("data/audio"), 2)
    }
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "disk": disk_info,
        "memory": memory_info,
        "storage": storage_info
    }

@router.post("/cleanup")
def trigger_cleanup(
    days_to_keep: int = 30,
    db: Session = Depends(get_db)
):
    """
    Manually trigger cleanup of old videos and audio.
    
    Args:
        days_to_keep: Number of days to retain content (default: 30)
    """
    cleanup_service = CleanupService(db)
    
    videos_deleted = cleanup_service.cleanup_old_videos(days_to_keep)
    audio_deleted = cleanup_service.cleanup_old_audio(days_to_keep)
    disk_status = cleanup_service.check_disk_space()
    
    return {
        "videos_deleted": videos_deleted,
        "audio_deleted": audio_deleted,
        "disk_space": disk_status
    }
