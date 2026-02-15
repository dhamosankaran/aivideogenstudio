"""
Enhanced video composition service for NotebookLM-style videos.

Supports scene-based composition with:
- Pexels stock VIDEOS per scene (dynamic backgrounds)
- Whisper word-level subtitle timing
- Smooth transitions (fade)
- End screen with CTAs (4 seconds)
- Background music layer (10-15% volume)
"""

import os
import math
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
import logging

from sqlalchemy.orm import Session
from moviepy import (
    ColorClip, 
    TextClip, 
    CompositeVideoClip, 
    CompositeAudioClip,
    AudioFileClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
    vfx
)

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
        
        # Use orchestrator for multi-source image search (fallback)
        self.image_search = ImageSearchOrchestrator()
        
        # NEW: Initialize Pexels Video Service for stock video backgrounds
        self.video_search = None
        try:
            from app.services.pexels_video_service import PexelsVideoService
            self.video_search = PexelsVideoService()
            logger.info("✓ Pexels Video Service initialized (stock video backgrounds)")
        except Exception as e:
            logger.warning(f"Pexels Video Service not available: {e}")
        
        logger.info(f"Image sources: {self.image_search.get_provider_status()}")
        
    def create_video_task(
        self, 
        script_id: int, 
        audio_id: Optional[int] = None,
        background_style: str = "scenes",  # "scenes" or "gradient"
        project_folder: Optional[str] = None
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
                "use_images": bool(self.image_search.unsplash or self.image_search.pexels),
                "project_folder": project_folder
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
            video.completed_at = datetime.now(timezone.utc)
            video.processing_time = (datetime.now() - start_time).total_seconds()
            
            if output_path.exists():
                video.file_size = output_path.stat().st_size
                video.duration = audio.duration
                
            self.db.commit()
            logger.info(f"Render complete for Video {video_id}")
            
            # === Best-effort: auto-generate SEO metadata ===
            try:
                import asyncio
                from app.services.metadata_generation_service import MetadataGenerationService
                
                article = script.article if script else None
                if article:
                    meta_service = MetadataGenerationService()
                    
                    # Extract book metadata if applicable
                    book_author = None
                    takeaways = None
                    content_type = script.content_type or "daily_update"
                    
                    if content_type == "book_review" and article.book_source_id:
                        book = article.book_source
                        if book:
                            book_author = book.author
                            takeaways = book.key_takeaways
                    
                    # Get script text for context
                    script_text = None
                    if script.scenes:
                        script_text = " ".join(s.get("text", "") for s in script.scenes)
                    
                    # Run async metadata generation with 30s timeout
                    loop = asyncio.new_event_loop()
                    metadata = loop.run_until_complete(
                        asyncio.wait_for(
                            meta_service.generate_metadata(
                                article_title=article.title,
                                article_description=article.description or article.summary or "",
                                script_content=script_text,
                                content_type=content_type,
                                book_author=book_author,
                                takeaways=takeaways,
                            ),
                            timeout=30.0  # 30s — only trigger fallback on true outage
                        )
                    )
                    loop.close()
                    
                    # Persist to video record
                    video.youtube_title = metadata.title[:100]
                    video.youtube_description = metadata.description[:5000]
                    video.youtube_tags = metadata.tags
                    if script:
                        script.hashtags = metadata.hashtags
                    self.db.commit()
                    logger.info(f"[SEO] Auto-generated metadata for video {video_id}: '{metadata.title[:50]}...'")
            except Exception as meta_err:
                logger.warning(f"[SEO] Auto-metadata generation failed (non-fatal): {meta_err}")
            
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
        
        # PRE-FETCH 3-4 IMAGES for variety across video
        # This ensures topic-relevant images using the article context
        logger.info("Pre-fetching topic-relevant images for video...")
        prefetched_images = []
        article_title = getattr(script.article, 'title', '') if script.article else ''
        
        # Detect content type early for image enrichment decisions
        content_type_hint = getattr(script, 'content_type', '') or getattr(script.article, 'suggested_content_type', '') or ''
        is_book_review = (content_type_hint == "book_review")
        
        # Check for project folder override
        project_folder = settings.get("project_folder")
        if project_folder and Path(project_folder).exists():
            image_dir = Path(project_folder) / "images"
            if image_dir.exists():
                # Load all valid images from project folder
                project_images = sorted([
                    p for p in image_dir.glob("*") 
                    if p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')
                ])
                if project_images:
                    prefetched_images.extend(project_images)
                    logger.info(f"[Project] Loaded {len(project_images)} images from {project_folder}")
        
        # BOOK REVIEW V2.1: Per-scene image search with ENTITY GROUNDING
        # Every search query includes book_title + author_name for relevance
        if is_book_review:
            logger.info("[Book V2.1] Entity-grounded multi-image mode")
            
            # Extract book context for entity grounding
            book_author = ''
            book_title_clean = article_title
            book_project_dir = None
            if script.article and hasattr(script.article, 'book_source') and script.article.book_source:
                book = script.article.book_source
                book_author = book.author or ''
                book_title_clean = book.title or article_title
                
                # Create per-book image directory
                import re as _re
                sanitized = _re.sub(r'[^\w\s-]', '', book_title_clean).strip().lower()
                sanitized = _re.sub(r'[-\s]+', '_', sanitized)
                book_project_dir = Path(f"data/projects/{book.id}_{sanitized}/images")
                book_project_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"[Book V2.1] Per-book image dir: {book_project_dir}")
            
            # Try to get book cover for scene 1
            if not prefetched_images:
                if script.article and hasattr(script.article, 'book_source') and script.article.book_source:
                    book = script.article.book_source
                    if book.cover_url:
                        cover_path = self._download_book_cover(book.cover_url, book.title)
                        if cover_path:
                            prefetched_images.insert(0, cover_path)
                            logger.info(f"[Book V2.1] Scene 1 cover: {cover_path.name}")
            
            # Search for unique images for each scene with entity-grounded queries
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Build entity-grounding context prefix
            entity_context = book_title_clean
            if book_author:
                entity_context = f"{book_title_clean} {book_author}"
            logger.info(f"[Book V2.1] Entity context: '{entity_context}'")
            
            scene_images = {}  # Map scene index -> image path
            for i, scene in enumerate(scenes_with_timing):
                # Scene 1 (Hook) uses the cover from prefetched_images
                if i == 0 and prefetched_images:
                    scene_images[i] = prefetched_images[0]
                    logger.info(f"[Book V2.1] Scene {i+1}: Using book cover")
                    continue
                
                # Search for scene-specific image with entity grounding
                keywords = scene.get("image_keywords", [])
                found = False
                for keyword in keywords[:2]:  # Try up to 2 keywords per scene
                    # ENTITY GROUNDING: prepend book title + author to every query
                    grounded_query = f"{entity_context} {keyword}"
                    logger.info(f"[Book V2.1] Scene {i+1}: Searching '{grounded_query[:60]}'...")
                    try:
                        image_path = loop.run_until_complete(
                            self.image_search.search_image_async(
                                keywords=[f"{book_title_clean} {keyword}"],
                                topic_query=grounded_query[:120],
                                orientation="portrait",
                                content_type=content_type_hint
                            )
                        )
                        if image_path:
                            # Copy to per-book folder if available
                            if book_project_dir:
                                import shutil
                                scene_dest = book_project_dir / f"scene_{i+1}.jpg"
                                shutil.copy(image_path, scene_dest)
                                image_path = scene_dest
                                logger.info(f"[Book V2.1] Scene {i+1}: Saved to {scene_dest.name}")
                            
                            scene_images[i] = image_path
                            found = True
                            break
                    except Exception as e:
                        logger.warning(f"[Book V2.1] Scene {i+1} search failed: {e}")
                
                if not found:
                    # Fallback: use cover or last available image
                    fallback = prefetched_images[0] if prefetched_images else None
                    if fallback:
                        scene_images[i] = fallback
                        logger.info(f"[Book V2.1] Scene {i+1}: Fallback to cover")
            
            # Summary
            unique_count = len(set(str(v) for v in scene_images.values()))
            logger.info(f"[Book V2.1] {unique_count} unique images across {len(scene_images)} scenes")
        else:
            # Non-book-review: original pre-fetch logic (collect all keywords, search up to 4)
            all_keywords = []
            for scene in scenes_with_timing:
                all_keywords.extend(scene.get("image_keywords", []))
            
            # Remove duplicates while preserving order
            seen = set()
            unique_keywords = [k for k in all_keywords if not (k in seen or seen.add(k))]
            
            # Fetch images using article context + keywords
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Search for up to 6 images for variety
            for keyword in unique_keywords[:6]:
                search_query = f"{article_title} {keyword}" if article_title else keyword
                logger.info(f"[Pre-fetch] Searching: {search_query[:60]}...")
                
                try:
                    image_path = loop.run_until_complete(
                        self.image_search.search_image_async(
                            keywords=[keyword],
                            topic_query=search_query[:100],
                            orientation="portrait",
                            content_type=content_type_hint
                        )
                    )
                    if image_path and image_path not in prefetched_images:
                        prefetched_images.append(image_path)
                        logger.info(f"[Pre-fetch] Got: {image_path.name}")
                except Exception as e:
                    logger.warning(f"Pre-fetch failed for '{keyword}': {e}")
            
            logger.info(f"Pre-fetched {len(prefetched_images)} images for video")
            scene_images = {}  # Not used for non-book content
        
        # Create scene clips
        scene_clips = []
        for i, scene in enumerate(scenes_with_timing):
            logger.info(f"Creating scene {i+1}/{len(scenes_with_timing)}")
            
            scene_start = scene["start_time"]
            scene_duration = scene["duration"]
            scene_words = scene["words"]
            
            # Get background for this scene (VIDEO > IMAGE > GRADIENT)
            bg_clip = None
            keywords = scene.get("image_keywords", [])
            
            # BOOK REVIEW V2: Use per-scene image mapping
            if is_book_review and i in scene_images:
                image_path = scene_images[i]
                logger.info(f"[Book V2] Scene {i+1}: Using {image_path.name}")
                bg_clip = self._create_ken_burns_clip(image_path, scene_duration, (w, h))
            
            # PRIORITY 1: Try to get a stock VIDEO (skip for book reviews)
            if bg_clip is None and self.video_search and keywords and not is_book_review:
                for keyword in keywords:
                    logger.info(f"[Video] Searching for: {keyword}")
                    video_path = self.video_search.search_video(
                        [keyword], 
                        orientation="portrait",
                        min_duration=5,
                        max_duration=30
                    )
                    if video_path:
                        bg_clip = self._create_video_background(video_path, scene_duration, (w, h))
                        if bg_clip:
                            logger.info(f"[Video] Using stock video for scene {i+1}")
                            break
            
            # PRIORITY 2: Fall back to stock IMAGE with Ken Burns
            if bg_clip is None and prefetched_images:
                image_index = i % len(prefetched_images)
                image_path = prefetched_images[image_index]
                logger.info(f"[Image] Using pre-fetched image {image_index+1}/{len(prefetched_images)}: {image_path.name}")
                bg_clip = self._create_ken_burns_clip(image_path, scene_duration, (w, h))
            
            # PRIORITY 3: Real-time search fallback
            if bg_clip is None and keywords:
                logger.info(f"[Image] Searching in real-time for scene {i+1}...")
                for keyword in keywords[:2]:
                    search_query = f"{article_title} {keyword}" if article_title else keyword
                    try:
                        image_path = loop.run_until_complete(
                            self.image_search.search_image_async(
                                keywords=[keyword],
                                topic_query=search_query[:100],
                                orientation="portrait",
                                content_type=content_type_hint
                            )
                        )
                        if image_path:
                            bg_clip = self._create_ken_burns_clip(image_path, scene_duration, (w, h))
                            logger.info(f"[Image] Using real-time search for scene {i+1}")
                            break
                    except Exception as e:
                        logger.warning(f"Real-time search failed: {e}")
            
            # PRIORITY 4: Final fallback to gradient
            if bg_clip is None:
                logger.info(f"Using gradient fallback for scene {i+1}")
                bg_clip = ColorClip(size=(w, h), color=(31, 41, 55), duration=scene_duration)
            
            # Composite scene
            scene_clip = bg_clip
            scene_clip = scene_clip.with_start(scene_start).with_duration(scene_duration)
            
            # Add fade/crossfade transitions
            effects = []
            if i > 0:
                fade_duration = 0.8 if is_book_review else 0.5  # Longer crossfade for book reviews
                effects.append(vfx.FadeIn(fade_duration))
            if i < len(scenes_with_timing) - 1:
                fade_duration = 0.8 if is_book_review else 0.5
                effects.append(vfx.FadeOut(fade_duration))
            if effects:
                scene_clip = scene_clip.with_effects(effects)
            
            scene_clips.append(scene_clip)
        
        # Create subtitle clips — use phrase-level for book reviews, word-level for others
        if is_book_review:
            logger.info("Creating phrase-level subtitles (Book V2)...")
            all_subtitle_clips = self._create_phrase_subtitles(all_words, (w, h))
        else:
            logger.info("Creating word-level subtitles...")
            all_subtitle_clips = self._create_word_subtitles(all_words, (w, h))
        
        # Add book title overlay for book reviews
        title_overlay_clips = []
        if is_book_review:
            book_author = ''
            if script.article and hasattr(script.article, 'book_source') and script.article.book_source:
                book_author = script.article.book_source.author or ''
            title_overlay_clips = self._create_book_title_overlay(
                book_title=article_title,
                book_author=book_author,
                duration=duration,
                video_size=(w, h)
            )
            logger.info(f"Added book title overlay: '{article_title}'")
        
        # Composite all scenes + subtitles + overlay
        all_clips = scene_clips + all_subtitle_clips + title_overlay_clips
        main_video = CompositeVideoClip(all_clips, size=(w, h))
        main_video = main_video.with_duration(duration)
        
        # Get content type for music and end screen selection
        content_type = getattr(script, 'content_type', 'daily_update') or 'daily_update'
        logger.info(f"Content type for video: {content_type} (script.content_type={script.content_type})")
        
        # Add background music (10-15% volume)
        logger.info("Adding background music...")
        music_path = self.music_service.get_music_for_content(content_type)
        if music_path:
            music_volume = self.music_service.get_recommended_volume(content_type)
            music_clip = AudioFileClip(str(music_path))
            # Loop music to cover video + end screen duration
            total_duration = duration + 4  # +4s for end screen
            if music_clip.duration < total_duration:
                # Loop the music using MoviePy 2.x API
                from moviepy.audio.fx.AudioLoop import AudioLoop
                music_clip = music_clip.with_effects([AudioLoop(duration=total_duration)])
            else:
                music_clip = music_clip.subclipped(0, total_duration)
            music_clip = music_clip.with_volume_scaled(music_volume)
            # Mix narration + music
            final_audio = CompositeAudioClip([audio_clip, music_clip.with_start(0)])
            logger.info(f"Mixed music at {music_volume*100:.0f}% volume")
        else:
            final_audio = audio_clip
            logger.warning("No background music available, using narration only")
        
        # Set audio on main video
        main_video = main_video.with_audio(final_audio.subclipped(0, duration))
        
        # Create end screen clip (4 seconds)
        logger.info("Adding end screen...")
        end_screen_path = self.end_screen_service.generate_end_screen(content_type)
        end_screen_clip = ImageClip(str(end_screen_path))
        end_screen_clip = end_screen_clip.with_duration(4)
        end_screen_clip = end_screen_clip.resized((w, h))
        end_screen_clip = end_screen_clip.with_effects([vfx.FadeIn(0.5)])
        
        # Add music to end screen if available
        if music_path:
            end_screen_audio = final_audio.subclipped(duration, duration + 4)
            end_screen_clip = end_screen_clip.with_audio(end_screen_audio)
        
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

    def _download_book_cover(self, cover_url: str, book_title: str) -> Optional[Path]:
        """Download book cover from OpenLibrary for use as scene background."""
        import httpx
        cache_key = hashlib.md5(f"bookcover_{book_title}".encode()).hexdigest()[:16]
        cover_dir = Path("data/images/book_reviews")
        cover_dir.mkdir(parents=True, exist_ok=True)
        cover_path = cover_dir / f"{cache_key}.jpg"
        
        if cover_path.exists():
            logger.info(f"[Book] Using cached cover: {cover_path}")
            return cover_path
        
        try:
            # Try large cover first, fall back to medium
            large_cover_url = cover_url.replace("-M.jpg", "-L.jpg")
            response = httpx.get(large_cover_url, timeout=10, follow_redirects=True)
            if response.status_code == 200 and len(response.content) > 1000:
                cover_path.write_bytes(response.content)
                logger.info(f"[Book] Downloaded large cover: {cover_path} ({len(response.content)} bytes)")
                return cover_path
            
            # Fallback to medium cover
            response = httpx.get(cover_url, timeout=10, follow_redirects=True)
            if response.status_code == 200 and len(response.content) > 1000:
                cover_path.write_bytes(response.content)
                logger.info(f"[Book] Downloaded medium cover: {cover_path} ({len(response.content)} bytes)")
                return cover_path
                
        except Exception as e:
            logger.warning(f"[Book] Failed to download cover: {e}")
        return None

    def _create_ken_burns_clip(self, image_path: Path, duration: float, size: Tuple[int, int], zoom: float = None):
        """Create image clip with Ken Burns effect (slow zoom).
        
        Uses a "Fit & Blur" strategy for images that don't match 9:16:
        - Images close to 9:16 → fill (resize by height, slight crop OK)
        - Images NOT 9:16 (e.g., book covers, landscapes) → center-fit over 
          a blurred+scaled copy of the same image as background
        
        Args:
            image_path: Path to image file
            duration: Scene duration in seconds
            size: Target video size (width, height), e.g. (1080, 1920)
            zoom: Optional zoom factor override (default: 1.0 to 1.1, capped at 1.15)
        """
        from PIL import Image as PILImage, ImageFilter
        import numpy as np
        
        w, h = size  # e.g., 1080 x 1920
        target_zoom = min(zoom or 1.1, 1.15)  # Cap zoom to prevent text cutoff
        target_aspect = w / h  # 0.5625 for 9:16
        
        # Load image and detect aspect ratio
        try:
            pil_img = PILImage.open(str(image_path)).convert("RGB")
        except Exception as e:
            logger.warning(f"[KenBurns] Failed to open image {image_path}: {e}")
            # Return a gradient fallback
            return ColorClip(size=(w, h), color=(31, 41, 55), duration=duration)
        
        img_w, img_h = pil_img.size
        img_aspect = img_w / img_h
        
        aspect_diff = abs(img_aspect - target_aspect)
        logger.info(f"[KenBurns] Image {img_w}x{img_h} (aspect={img_aspect:.3f}), target={target_aspect:.3f}, diff={aspect_diff:.3f}")
        
        if aspect_diff < 0.15:
            # ===== FILL MODE: Image is close to 9:16 =====
            # Resize by height (slight horizontal crop is acceptable)
            img_clip = ImageClip(str(image_path))
            img_clip = img_clip.resized(height=int(h * 1.15))  # 15% headroom for zoom
            img_clip = img_clip.with_position("center")
        else:
            # ===== FIT & BLUR MODE: Image doesn't match 9:16 =====
            logger.info(f"[KenBurns] Fit & Blur mode for non-9:16 image")
            
            # 1. Create blurred background (stretch original to fill frame)
            bg_img = pil_img.copy()
            bg_img = bg_img.resize((w, h), PILImage.LANCZOS)
            bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=25))
            # Darken the blurred background for better contrast
            from PIL import ImageEnhance
            bg_img = ImageEnhance.Brightness(bg_img).enhance(0.5)
            bg_array = np.array(bg_img)
            bg_clip = ImageClip(bg_array).with_duration(duration)
            
            # 2. Fit the original image centered (85% of frame)
            fit_scale = 0.85
            if img_aspect > target_aspect:
                # Wider than 9:16 → fit by width
                new_w = int(w * fit_scale)
                new_h = int(new_w / img_aspect)
            else:
                # Taller than 9:16 → fit by height
                new_h = int(h * fit_scale)
                new_w = int(new_h * img_aspect)
            
            fitted_img = pil_img.resize((new_w, new_h), PILImage.LANCZOS)
            fitted_array = np.array(fitted_img)
            fitted_clip = ImageClip(fitted_array).with_position("center").with_duration(duration)
            
            # 3. Composite: blurred bg + centered fitted image
            img_clip = CompositeVideoClip([bg_clip, fitted_clip], size=(w, h))
            img_clip = img_clip.with_duration(duration)
        
        # Apply Ken Burns slow zoom effect
        zoom_start = 1.0
        zoom_end = target_zoom
        def zoom_effect(t):
            return zoom_start + (zoom_end - zoom_start) * (t / max(duration, 0.1))
        
        img_clip = img_clip.resized(lambda t: zoom_effect(t))
        img_clip = img_clip.with_position("center")
        img_clip = img_clip.with_duration(duration)
        
        return img_clip

    def _create_video_background(self, video_path: Path, duration: float, size: Tuple[int, int]) -> Optional[VideoFileClip]:
        """
        Create a video clip background from stock video.
        
        Args:
            video_path: Path to the stock video file
            duration: Required scene duration
            size: Target video size (width, height)
            
        Returns:
            VideoFileClip resized and trimmed to match scene, or None if fails
        """
        try:
            w, h = size
            
            # Load the video (without audio - we have our own narration)
            vid_clip = VideoFileClip(str(video_path), audio=False)
            
            # Resize to fit portrait frame (cover the entire frame)
            # Calculate aspect ratios to determine how to scale
            vid_w, vid_h = vid_clip.size
            target_ratio = w / h  # Portrait: e.g., 1080/1920 = 0.5625
            vid_ratio = vid_w / vid_h
            
            if vid_ratio > target_ratio:
                # Video is wider - scale by height and crop sides
                vid_clip = vid_clip.resized(height=h)
            else:
                # Video is taller - scale by width and crop top/bottom
                vid_clip = vid_clip.resized(width=w)
            
            # Center the video
            vid_clip = vid_clip.with_position("center")
            
            # Handle duration: loop if stock video is too short
            stock_duration = vid_clip.duration
            if stock_duration < duration:
                # Loop the video to cover the scene duration
                loop_count = int(duration / stock_duration) + 1
                logger.info(f"Looping stock video {loop_count}x to cover {duration}s scene")
                # Use concatenate to loop (MoviePy 2.x compatible)
                vid_clip = concatenate_videoclips([vid_clip] * loop_count)
            
            # Trim to exact scene duration
            vid_clip = vid_clip.subclipped(0, duration)
            
            return vid_clip
            
        except Exception as e:
            logger.error(f"Error creating video background: {e}")
            return None

    def _create_word_subtitles(self, words: List[Dict], video_size: Tuple[int, int]) -> List[TextClip]:
        """Create word-level subtitle clips with precise timing.
        
        Styled like viral YouTube Shorts: bold white text with strong shadow at bottom of screen.
        """
        w, h = video_size
        clips = []
        
        # Calculate absolute Y position: 85% from top (leaves room for engagement UI at bottom)
        y_position = int(h * 0.85)
        
        for word_data in words:
            word = word_data["word"]
            start = word_data["start"]
            end = word_data["end"]
            word_duration = end - start
            
            if not word.strip():
                continue
            
            txt_clip = (
                TextClip(
                    text=word.strip(),
                    font_size=72,
                    color='white', 
                    font='/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                    stroke_color='black',
                    stroke_width=5,
                    text_align='center'
                )
                .with_position(('center', y_position))
                .with_start(start)
                .with_duration(word_duration)
            )
            clips.append(txt_clip)
        
        logger.info(f"Created {len(clips)} word subtitle clips at y={y_position}px")
        return clips
    
    def _create_phrase_subtitles(self, words: List[Dict], video_size: Tuple[int, int], words_per_phrase: int = 3) -> List[TextClip]:
        """Create phrase-level subtitle clips (3-4 words at a time).
        
        More professional and readable than single-word subtitles.
        Positioned within YouTube Shorts safe zone (not obscured by UI).
        
        Args:
            words: List of word timing dicts [{"word": ..., "start": ..., "end": ...}]
            video_size: (width, height) tuple
            words_per_phrase: Number of words per subtitle phrase (default: 3)
        """
        w, h = video_size
        clips = []
        
        # Position at 78% from top — within YT Shorts safe zone
        # Safe zone: top 15% (channel info) and bottom 20% (like/comment/share buttons)
        y_position = int(h * 0.78)
        
        # Group words into phrases of N words
        filtered_words = [wd for wd in words if wd["word"].strip()]
        
        i = 0
        while i < len(filtered_words):
            # Take next N words as a phrase
            phrase_words = filtered_words[i:i + words_per_phrase]
            
            if not phrase_words:
                break
            
            phrase_text = " ".join(pw["word"].strip() for pw in phrase_words)
            phrase_start = phrase_words[0]["start"]
            phrase_end = phrase_words[-1]["end"]
            phrase_duration = phrase_end - phrase_start
            
            # Minimum duration to prevent flashing
            if phrase_duration < 0.3:
                phrase_duration = 0.3
            
            txt_clip = (
                TextClip(
                    text=phrase_text,
                    font_size=64,  # Slightly smaller than word-level for multi-word fit
                    color='white',
                    font='/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                    stroke_color='black',
                    stroke_width=4,
                    text_align='center'
                )
                .with_position(('center', y_position))
                .with_start(phrase_start)
                .with_duration(phrase_duration)
            )
            clips.append(txt_clip)
            
            i += words_per_phrase
        
        logger.info(f"Created {len(clips)} phrase subtitle clips ({words_per_phrase} words each) at y={y_position}px")
        return clips
    
    def _create_book_title_overlay(
        self,
        book_title: str,
        book_author: str,
        duration: float,
        video_size: Tuple[int, int]
    ) -> List[TextClip]:
        """Create a persistent book title overlay at the top of the screen.
        
        Positioned within YouTube Shorts safe zone (below the top 10% where
        the channel name and follow button appear).
        
        Args:
            book_title: Title of the book
            book_author: Author name
            duration: Total video duration
            video_size: (width, height) tuple
            
        Returns:
            List of TextClip objects to composite
        """
        w, h = video_size
        clips = []
        
        # Y position: 12% from top (below YT Shorts channel bar safe zone)
        y_title = int(h * 0.12)
        y_author = y_title + 50  # Author line below title
        
        # Truncate long titles
        display_title = book_title[:50] + "..." if len(book_title) > 50 else book_title
        
        # Semi-transparent background bar
        try:
            from PIL import Image as PILImage
            import numpy as np
            # Create a semi-transparent dark bar
            bar_height = 100 if book_author else 60
            bar_img = PILImage.new('RGBA', (w, bar_height), (0, 0, 0, 160))  # 63% opacity black
            bar_array = np.array(bar_img)
            bar_clip = (
                ImageClip(bar_array)
                .with_position(('center', y_title - 15))
                .with_start(0)
                .with_duration(duration)
            )
            clips.append(bar_clip)
        except Exception as e:
            logger.warning(f"Could not create title bar background: {e}")
        
        # Book title text
        title_clip = (
            TextClip(
                text=f"📖 {display_title}",
                font_size=36,
                color='white',
                font='/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                stroke_color='black',
                stroke_width=2,
                text_align='center'
            )
            .with_position(('center', y_title))
            .with_start(0)
            .with_duration(duration)
        )
        clips.append(title_clip)
        
        # Author name (if available)
        if book_author:
            author_clip = (
                TextClip(
                    text=f"by {book_author}",
                    font_size=28,
                    color='#CCCCCC',
                    font='/System/Library/Fonts/Supplemental/Arial.ttf',
                    stroke_color='black',
                    stroke_width=1,
                    text_align='center'
                )
                .with_position(('center', y_author))
                .with_start(0)
                .with_duration(duration)
            )
            clips.append(author_clip)
        
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
