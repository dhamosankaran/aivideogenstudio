"""
Resource cleanup service for managing disk space and old content.
"""

from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
from app.models import Video, Audio, Script
from app.utils.logger import get_logger
import psutil

logger = get_logger(__name__)

class CleanupService:
    """Service for cleaning up old files and managing resources."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def cleanup_old_videos(self, days_to_keep: int = 30) -> int:
        """
        Delete videos older than specified days.
        
        Args:
            days_to_keep: Number of days to retain videos
            
        Returns:
            Number of videos deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
        
        old_videos = self.db.query(Video).filter(
            Video.created_at < cutoff
        ).all()
        
        deleted_count = 0
        for video in old_videos:
            try:
                # Delete file from disk
                if video.file_path:
                    file_path = Path(video.file_path)
                    if file_path.exists():
                        file_path.unlink()
                        logger.info(
                            "deleted_video_file",
                            video_id=video.id,
                            file_path=str(file_path)
                        )
                
                # Delete database record
                self.db.delete(video)
                deleted_count += 1
                
            except Exception as e:
                logger.error(
                    "cleanup_error",
                    video_id=video.id,
                    error=str(e)
                )
        
        self.db.commit()
        
        logger.info(
            "cleanup_complete",
            deleted_count=deleted_count,
            days_to_keep=days_to_keep
        )
        
        return deleted_count
    
    def cleanup_old_audio(self, days_to_keep: int = 30) -> int:
        """
        Delete audio files older than specified days.
        
        Args:
            days_to_keep: Number of days to retain audio
            
        Returns:
            Number of audio files deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
        
        old_audio = self.db.query(Audio).filter(
            Audio.created_at < cutoff
        ).all()
        
        deleted_count = 0
        for audio in old_audio:
            try:
                # Delete file from disk
                if audio.file_path:
                    file_path = Path(audio.file_path)
                    if file_path.exists():
                        file_path.unlink()
                
                # Delete database record
                self.db.delete(audio)
                deleted_count += 1
                
            except Exception as e:
                logger.error(
                    "audio_cleanup_error",
                    audio_id=audio.id,
                    error=str(e)
                )
        
        self.db.commit()
        return deleted_count
    
    def check_disk_space(self, min_free_gb: float = 1.0) -> dict:
        """
        Check available disk space and warn if low.
        
        Args:
            min_free_gb: Minimum free space in GB before warning
            
        Returns:
            Dict with disk space info
        """
        disk = psutil.disk_usage('/')
        free_gb = disk.free / (1024**3)
        
        status = {
            "free_gb": round(free_gb, 2),
            "total_gb": round(disk.total / (1024**3), 2),
            "percent_used": disk.percent,
            "warning": free_gb < min_free_gb
        }
        
        if status["warning"]:
            logger.warning(
                "low_disk_space",
                free_gb=free_gb,
                threshold_gb=min_free_gb
            )
        
        return status
    
    def get_directory_size(self, directory: str) -> float:
        """
        Calculate total size of a directory in GB.
        
        Args:
            directory: Directory path
            
        Returns:
            Size in GB
        """
        total_size = 0
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return 0.0
        
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        return total_size / (1024**3)
