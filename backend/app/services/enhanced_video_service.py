"""
Enhanced video composition service for NotebookLM-style videos.

Supports scene-based composition with:
- Pexels stock images per scene
- Whisper word-level subtitle timing
- Smooth transitions (fade, zoom/pan)
- End screen with CTAs (4 seconds)
- Background music layer (10-15% volume)
"""

import os
import math
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
import logging

from sqlalchemy.orm import Session
from moviepy.editor import (
    ColorClip, 
    TextClip, 
    CompositeVideoClip, 
    CompositeAudioClip,
    AudioFileClip,
    ImageClip,
    concatenate_videoclips
)
from moviepy.config import change_settings

from app.models import Script, Audio, Video, Article
from app.config import settings
from app.services.whisper_service import WhisperService
from app.services.image_search_orchestrator import ImageSearchOrchestrator
from app.services.background_music_service import BackgroundMusicService
from app.services.end_screen_service import EndScreenService

logger = logging.getLogger(__name__)


class EnhancedVideoCompositionService:
    """Service for composing NotebookLM-style videos with scenes."""
    
    VIDEO_DIR = Path("data/videos")
    
    def __init__(self, db: Session):
        self.db = db
        self.VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        self.whisper = WhisperService()
        self.music_service = BackgroundMusicService()
        self.end_screen_service = EndScreenService()
        
        # Use orchestrator for multi-source image search (Unsplash primary, Pexels fallback)
        self.image_search = ImageSearchOrchestrator()
        logger.info(f"Image sources: {self.image_search.get_provider_status()}")
        
    def create_video_task(
        self, 
        script_id: int, 
        audio_id: Optional[int] = None,
        background_style: str = "scenes"  # "scenes" or "gradient"
    ) -> Video:
        """Create a video record and return it (before processing)."""
        # Fetch Script
        script = self.db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise ValueError(f"Script not found: {script_id}")
            
        # Fetch Audio
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
            
        # Create Video Record
        video = Video(
            script_id=script_id,
            audio_id=audio.id,
            status="pending",
            render_settings={
                "resolution": "1080x1920",
                "fps": 30,
                "background": background_style,
                "use_whisper": True,
                "use_images": bool(self.image_search.unsplash or self.image_search.pexels)
            },
            # Auto-populate metadata from script
            youtube_title=script.catchy_title,
            youtube_description=script.video_description
        )
        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)
        return video

    def process_video(self, video_id: int):
        """Process a video task (render it)."""
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            logger.error(f"Video task not found: {video_id}")
            return

        try:
            video.status = "rendering"
            self.db.commit()
            
            script = video.script
            audio = video.audio
            
            logger.info(f"Starting NotebookLM-style render for Video {video_id}")
            start_time = datetime.now()
            
            output_filename = f"video_{video.id}_{start_time.strftime('%Y%m%d_%H%M%S')}.mp4"
            output_path = self.VIDEO_DIR / output_filename
            
            # Check if script has scenes
            if script.scenes and len(script.scenes) > 0:
                logger.info(f"Using scene-based composition ({len(script.scenes)} scenes)")
                self._compose_scene_based_video(
                    script=script,
                    audio_path=Path(audio.file_path),
                    output_path=output_path,
                    settings=video.render_settings or {}
                )
            else:
                logger.info("No scenes found, using legacy composition")
                self._compose_simple_video(
                    script=script,
                    audio_path=Path(audio.file_path),
                    output_path=output_path,
                    settings=video.render_settings or {}
                )
            
            # Update Record
            video.file_path = str(output_path)
            video.status = "completed"
            video.completed_at = datetime.utcnow()
            video.processing_time = (datetime.now() - start_time).total_seconds()
            
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

    def _compose_scene_based_video(
        self, 
        script: Script, 
        audio_path: Path, 
        output_path: Path,
        settings: Dict[str, Any]
    ):
        """Compose video with scene-based structure."""
        
        # Load audio
        if not audio_path.exists():
            full_path = Path.cwd() / audio_path
            if full_path.exists():
                audio_path = full_path
            else:
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
                
        audio_clip = AudioFileClip(str(audio_path))
        duration = audio_clip.duration
        
        # Get word-level timing from Whisper
        logger.info("Extracting word-level timing with Whisper...")
        timing_data = self.whisper.transcribe_audio(audio_path)
        all_words = timing_data["words"]
        
        # Resolution (1080x1920 for Shorts)
        w, h = 1080, 1920
        fps = settings.get("fps", 30)
        
        # Get scene timing
        logger.info("Mapping scenes to audio timing...")
        scenes_with_timing = self.whisper.get_scene_timing(audio_path, script.scenes)
        
        # Create scene clips
        scene_clips = []
        for i, scene in enumerate(scenes_with_timing):
            logger.info(f"Creating scene {i+1}/{len(scenes_with_timing)}")
            
            scene_start = scene["start_time"]
            scene_duration = scene["duration"]
            scene_words = scene["words"]
            
            # Get image for this scene using orchestrator (Unsplash -> Pexels -> gradient)
            image_path = None
            if scene.get("image_keywords"):
                # Try all keywords in order until we find an image
                for keyword in scene["image_keywords"]:
                    logger.info(f"Searching for: {keyword}")
                    image_path = self.image_search.search_image([keyword], orientation="portrait")
                    if image_path:
                        break
                
                # If individual searches fail, try generic fallback
                if not image_path:
                    logger.info("No specific matches, trying generic fallbacks")
                    image_path = self.image_search.search_image(["technology", "abstract"])
            
            # Create background clip
            if image_path and image_path.exists():
                # Use Pexels image with Ken Burns effect
                bg_clip = self._create_ken_burns_clip(image_path, scene_duration, (w, h))
            else:
                # Fallback to gradient
                bg_clip = ColorClip(size=(w, h), color=(31, 41, 55), duration=scene_duration)
            
            # Create word-level subtitles for this scene
            # Note: subtitle clips have absolute timing from video start, not relative to scene
            
            # Composite scene
            # Background only (subtitles will be added globally later)
            scene_clip = bg_clip
            scene_clip = scene_clip.set_start(scene_start).set_duration(scene_duration)
            
            # Add fade transition
            if i > 0:
                scene_clip = scene_clip.fadein(0.5)
            if i < len(scenes_with_timing) - 1:
                scene_clip = scene_clip.fadeout(0.5)
            
            scene_clips.append(scene_clip)
        
        # Create all subtitle clips (with absolute timing)
        logger.info("Creating word-level subtitles...")
        all_subtitle_clips = self._create_word_subtitles(all_words, (w, h))
        
        # Composite all scenes + subtitles
        main_video = CompositeVideoClip(scene_clips + all_subtitle_clips, size=(w, h))
        main_video = main_video.set_duration(duration)
        
        # Get content type for music and end screen selection
        content_type = getattr(script, 'content_type', 'daily_update') or 'daily_update'
        
        # Add background music (10-15% volume)
        logger.info("Adding background music...")
        music_path = self.music_service.get_music_for_content(content_type)
        if music_path:
            music_volume = self.music_service.get_recommended_volume(content_type)
            music_clip = AudioFileClip(str(music_path))
            # Loop music to cover video + end screen duration
            total_duration = duration + 4  # +4s for end screen
            if music_clip.duration < total_duration:
                # Loop the music
                from moviepy.audio.fx.audio_loop import audio_loop
                music_clip = audio_loop(music_clip, duration=total_duration)
            else:
                music_clip = music_clip.subclip(0, total_duration)
            music_clip = music_clip.volumex(music_volume)
            # Mix narration + music
            final_audio = CompositeAudioClip([audio_clip, music_clip.set_start(0)])
            logger.info(f"Mixed music at {music_volume*100:.0f}% volume")
        else:
            final_audio = audio_clip
            logger.warning("No background music available, using narration only")
        
        # Set audio on main video
        main_video = main_video.set_audio(final_audio.subclip(0, duration))
        
        # Create end screen clip (4 seconds)
        logger.info("Adding end screen...")
        end_screen_path = self.end_screen_service.generate_end_screen(content_type)
        end_screen_clip = ImageClip(str(end_screen_path))
        end_screen_clip = end_screen_clip.set_duration(4)
        end_screen_clip = end_screen_clip.resize((w, h))
        end_screen_clip = end_screen_clip.fadein(0.5)
        
        # Add music to end screen if available
        if music_path:
            end_screen_audio = final_audio.subclip(duration, duration + 4)
            end_screen_clip = end_screen_clip.set_audio(end_screen_audio)
        
        # Concatenate main video + end screen
        final_video = concatenate_videoclips([main_video, end_screen_clip], method="compose")
        
        # Write file
        logger.info(f"Writing video to {output_path}")
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
        if music_path:
            music_clip.close()
        final_video.close()

    def _create_ken_burns_clip(self, image_path: Path, duration: float, size: Tuple[int, int]) -> ImageClip:
        """Create image clip with Ken Burns effect (slow zoom)."""
        w, h = size
        
        # Load image
        img_clip = ImageClip(str(image_path))
        
        # Resize to fit (with some zoom headroom)
        img_clip = img_clip.resize(height=h * 1.2)  # 20% larger for zoom
        
        # Center the image
        img_clip = img_clip.set_position("center")
        
        # Apply slow zoom effect
        def zoom_effect(t):
            zoom = 1 + 0.1 * (t / duration)  # Zoom from 1.0 to 1.1
            return zoom
        
        img_clip = img_clip.resize(lambda t: zoom_effect(t))
        img_clip = img_clip.set_duration(duration)
        
        return img_clip

    def _create_word_subtitles(self, words: List[Dict], video_size: Tuple[int, int]) -> List[TextClip]:
        """Create word-level subtitle clips with precise timing."""
        w, h = video_size
        clips = []
        
        for word_data in words:
            word = word_data["word"]
            start = word_data["start"]
            end = word_data["end"]
            duration = end - start
            
            # Create text clip for this word
            txt_clip = (
                TextClip(
                    word, 
                    fontsize=80, 
                    color='white', 
                    font='Arial-Bold',
                    stroke_color='black',
                    stroke_width=3,
                    method='label'
                )
                .set_position(('center', 0.75), relative=True)  # Bottom third
                .set_start(start)
                .set_duration(duration)
            )
            clips.append(txt_clip)
        
        return clips

    def _compose_simple_video(
        self, 
        script: Script, 
        audio_path: Path, 
        output_path: Path,
        settings: Dict[str, Any]
    ):
        """Fallback to simple composition (legacy method)."""
        # Import the old video service method
        from app.services.video_service import VideoCompositionService
        old_service = VideoCompositionService(self.db)
        old_service._compose_video(script, audio_path, output_path, settings)
