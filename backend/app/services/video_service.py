import os
import math
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
import logging

from sqlalchemy.orm import Session
from moviepy.editor import (
    ColorClip, 
    TextClip, 
    CompositeVideoClip, 
    AudioFileClip,
    ImageClip
)
from moviepy.config import change_settings

from app.models import Script, Audio, Video, Article
from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class VideoCompositionService:
    """Service for composing and rendering videos."""
    
    VIDEO_DIR = Path("data/videos")
    
    def __init__(self, db: Session):
        self.db = db
        # Ensure video directory exists
        self.VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        
    def create_video_task(
        self, 
        script_id: int, 
        audio_id: Optional[int] = None,
        background_style: str = "gradient"
    ) -> Video:
        """Create a video record and return it (before processing)."""
        # 1. Fetch Script
        script = self.db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise ValueError(f"Script not found: {script_id}")
            
        # 2. Fetch Audio
        if audio_id:
            audio = self.db.query(Audio).filter(Audio.id == audio_id).first()
        else:
            audio = (
                self.db.query(Audio)
                .filter(Audio.script_id == script_id, Audio.status == "completed")
                .order_by(Audio.created_at.desc())
                .first()
            )
            
        if not audio:
            raise ValueError(f"No completed audio found for script: {script_id}")
            
        # 3. Create Video Record
        video = Video(
            script_id=script_id,
            audio_id=audio.id,
            status="pending", # Start as pending
            render_settings={
                "resolution": "1080x1920",
                "fps": 30,
                "background": background_style
            }
        )
        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)
        return video

    def process_video(self, video_id: int):
        """Process a video task (render it). Intended to be run in background."""
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            logger.error(f"Video task not found: {video_id}")
            return

        try:
            # Update status to rendering
            video.status = "rendering"
            self.db.commit()
            
            script = video.script
            audio = video.audio
            
            logger.info(f"Starting render for Video {video_id} (Script {script.id})")
            start_time = datetime.now()
            
            # Perform Composition
            output_filename = f"video_{video.id}_{start_time.strftime('%Y%m%d_%H%M%S')}.mp4"
            output_path = self.VIDEO_DIR / output_filename
            
            self._compose_video(
                script=script,
                audio_path=Path(audio.file_path),
                output_path=output_path,
                settings=video.render_settings or {}
            )
            
            # Update Record (Completed)
            video.file_path = str(output_path)
            video.status = "completed"
            video.completed_at = datetime.utcnow()
            video.processing_time = (datetime.now() - start_time).total_seconds()
            
            # Get file size
            if output_path.exists():
                video.file_size = output_path.stat().st_size
                video.duration = audio.duration
                
            self.db.commit()
            logger.info(f"Render complete for Video {video_id}")
            
        except Exception as e:
            logger.error(f"Video {video_id} generation failed: {e}")
            video.status = "failed"
            video.error_message = str(e)
            self.db.commit()

    def _compose_video(
        self, 
        script: Script, 
        audio_path: Path, 
        output_path: Path,
        settings: Dict[str, Any]
    ):
        """Core logic to compose clips using MoviePy."""
        
        # Audio
        if not audio_path.exists():
             # Try absolute path resolution if relative fails
            full_path = Path.cwd() / audio_path
            if full_path.exists():
                audio_path = full_path
            else:
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
                
        audio_clip = AudioFileClip(str(audio_path))
        duration = audio_clip.duration
        
        # Resolution (1080x1920 for Shorts)
        w, h = 1080, 1920
        fps = settings.get("fps", 30)
        
        # 1. Background
        # For MVP, simple solid color
        # Dark Blue-Grey: #1F2937
        bg_clip = ColorClip(size=(w, h), color=(31, 41, 55), duration=duration)
        
        # 2. Subtitles
        # Generate text clips timed to audio
        subtitle_clips = self._generate_subtitles(
            text=script.formatted_script or script.raw_script,
            duration=duration,
            video_size=(w, h)
        )
        
        # 3. Composite
        final_video = CompositeVideoClip([bg_clip] + subtitle_clips)
        final_video = final_video.set_audio(audio_clip)
        final_video = final_video.set_duration(duration)
        
        # 4. Write File
        # preset='ultrafast' for speed during dev/MVP
        final_video.write_videofile(
            str(output_path), 
            fps=fps, 
            codec="libx264", 
            audio_codec="aac",
            preset="ultrafast",
            threads=4
        )
        
        # Cleanup
        audio_clip.close()
        final_video.close()

    def _generate_subtitles(
        self, 
        text: str, 
        duration: float, 
        video_size: Tuple[int, int]
    ) -> List[TextClip]:
        """
        Split text and generate timed TextClips.
        MVP Strategy: Even processing time allocation per word.
        """
        w, h = video_size
        words = text.split()
        if not words:
            return []
            
        # Group words into chunks (3-5 words) for better readability
        chunks = []
        chunk_size = 4
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i + chunk_size]))
            
        time_per_chunk = duration / len(chunks)
        
        clips = []
        for i, chunk in enumerate(chunks):
            start_time = i * time_per_chunk
            end_time = (i + 1) * time_per_chunk
            
            # Ensure last chunk matches exact duration
            if i == len(chunks) - 1:
                end_time = duration
                
            txt_clip = (
                TextClip(
                    chunk, 
                    fontsize=70, 
                    color='white', 
                    font='Arial-Bold', 
                    method='caption', # Word wrap
                    size=(w - 100, None), # Margins
                    align='center'
                )
                .set_position('center')
                .set_start(start_time)
                .set_duration(end_time - start_time)
            )
            clips.append(txt_clip)
            
        return clips
    
    # Video Validation Methods (Issue #017)
    
    def get_pending_videos(self) -> List[Video]:
        """Get all videos with pending validation status."""
        videos = self.db.query(Video).filter(
            Video.validation_status == "pending",
            Video.status.in_(["pending", "rendering", "completed"])
        ).order_by(Video.created_at.desc()).all()

        # Data Integrity Check: Ensure files exist for completed videos
        for video in videos:
            if video.status == "completed" and video.file_path:
                path = Path(video.file_path)
                if not path.exists():
                     # Check relative path
                    if not (Path.cwd() / path).exists():
                        logger.warning(f"Video file missing for Video {video.id}. marking as failed.")
                        video.status = "failed"
                        video.error_message = "File lost from disk (server restart?)"
                        self.db.add(video)
        
        self.db.commit() # Commit any status changes
        return videos
    
    def get_video_with_metadata(self, video_id: int) -> Optional[Dict]:
        """
        Get video with full metadata including script and article.
        
        Returns:
            Dict with 'video', 'script', and 'article' keys, or None if not found
        """
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return None
        
        script = video.script
        article = script.article if script else None
        
        return {
            "video": video,
            "script": script,
            "article": article
        }
    
    def update_video_metadata(
        self,
        video_id: int,
        youtube_title: Optional[str] = None,
        youtube_description: Optional[str] = None,
        hashtags: Optional[List[str]] = None
    ) -> Optional[Video]:
        """
        Update video metadata for YouTube upload.
        
        Args:
            video_id: Video ID to update
            youtube_title: YouTube title (max 100 chars)
            youtube_description: YouTube description (max 5000 chars)
            hashtags: List of hashtags
            
        Returns:
            Updated Video or None if not found
        """
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return None
        
        if youtube_title is not None:
            video.youtube_title = youtube_title[:100]  # Enforce limit
        if youtube_description is not None:
            video.youtube_description = youtube_description[:5000]  # Enforce limit
        if hashtags is not None:
            # Store as JSON array
            video.hashtags = hashtags
        
        video.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(video)
        
        return video
    
    def approve_video(self, video_id: int) -> Optional[Video]:
        """
        Approve video for YouTube upload.
        
        Args:
            video_id: Video ID to approve
            
        Returns:
            Updated Video or None if not found
        """
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return None
        
        video.validation_status = "approved"
        video.approved_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(video)
        
        return video
    
    def reject_video(self, video_id: int, reason: str) -> Optional[Video]:
        """
        Reject video with a reason.
        
        Args:
            video_id: Video ID to reject
            reason: Reason for rejection
            
        Returns:
            Updated Video or None if not found
        """
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return None
        
        video.validation_status = "rejected"
        video.rejection_reason = reason
        
        self.db.commit()
        self.db.refresh(video)
        
        return video
