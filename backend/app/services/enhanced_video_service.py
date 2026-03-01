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
from app.services.pattern_interrupt_service import PatternInterruptService
from app.content_types import get_project_subfolder

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
        self.pattern_interrupt = PatternInterruptService()
        
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
        
        # Initialize Veo Video Service for AI-generated video backgrounds
        self.veo_video = None
        try:
            from app.services.veo_video_service import VeoVideoService
            veo = VeoVideoService()
            if veo.is_available:
                self.veo_video = veo
                logger.info("✓ Veo Video Service initialized (AI video backgrounds)")
            else:
                logger.info("Veo Video Service: API key not configured (optional)")
        except Exception as e:
            logger.warning(f"Veo Video Service not available: {e}")
        
        logger.info(f"Image sources: {self.image_search.get_provider_status()}")
        
    def create_video_task(
        self, 
        script_id: int, 
        audio_id: Optional[int] = None,
        background_style: str = "scenes",  # "scenes" or "gradient"
        project_folder: Optional[str] = None,
        background_mode: str = "auto",  # auto, images_only, videos_only, mixed
        image_source: str = "stock",  # stock, ai_generated, auto
        video_source: str = "stock"  # stock, veo
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
                "background_mode": background_mode,
                "use_whisper": True,
                "use_images": bool(self.image_search.unsplash or self.image_search.pexels),
                "project_folder": project_folder,
                "image_source": image_source,
                "video_source": video_source
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
        all_segments = timing_data.get("segments", [])  # Sentence-level segments for CC-style subtitles
        
        # Resolution (1080x1920 for Shorts)
        w, h = 1080, 1920
        fps = settings.get("fps", 30)
        
        # Get scene timing
        logger.info("Mapping scenes to audio timing...")
        scenes_with_timing = self.whisper.get_scene_timing(audio_path, script.scenes)
        
        # ===== PROJECT FOLDER SETUP (single source of truth for all assets) =====
        logger.info("Setting up project folder for all assets...")
        prefetched_images = []
        article_title = getattr(script.article, 'title', '') if script.article else ''
        
        # Detect content type early for image enrichment decisions
        content_type_hint = getattr(script, 'content_type', '') or getattr(script.article, 'suggested_content_type', '') or ''
        is_book_review = (content_type_hint == "book_review")
        
        # --- Topic subfolder (e.g. "books", "news", "tech") ---
        topic_subfolder = get_project_subfolder(content_type_hint or 'daily_update')
        
        # Create project directory (single location for all asset storage)
        import re as _re
        project_image_dir = None
        project_video_dir = None
        
        if is_book_review and script.article and hasattr(script.article, 'book_source') and script.article.book_source:
            book = script.article.book_source
            sanitized = _re.sub(r'[^\w\s-]', '', (book.title or article_title)).strip().lower()
            sanitized = _re.sub(r'[-\s]+', '_', sanitized)
            project_base = Path(f"data/projects/{topic_subfolder}/{book.id}_{sanitized}")
        else:
            # Non-book content: use article ID for project folder
            article_id = script.article_id or script.id
            sanitized = _re.sub(r'[^\w\s-]', '', article_title[:50]).strip().lower()
            sanitized = _re.sub(r'[-\s]+', '_', sanitized) if sanitized else 'untitled'
            project_base = Path(f"data/projects/{topic_subfolder}/article_{article_id}_{sanitized}")
        
        project_image_dir = project_base / "images"
        project_video_dir = project_base / "videos"
        project_image_dir.mkdir(parents=True, exist_ok=True)
        project_video_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[Project] Base dir: {project_base}")
        logger.info(f"[Project] Image dir: {project_image_dir}")
        logger.info(f"[Project] Video dir: {project_video_dir}")
        
        # Check for existing images in project folder (reuse from previous runs)
        project_folder = settings.get("project_folder")
        if project_folder and Path(project_folder).exists():
            image_dir = Path(project_folder) / "images"
            if image_dir.exists():
                project_images = sorted([
                    p for p in image_dir.glob("*") 
                    if p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')
                ])
                if project_images:
                    prefetched_images.extend(project_images)
                    logger.info(f"[Project] Reusing {len(project_images)} existing images")
        
        # ===== IMAGE FETCHING (project-dir-first) =====
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if is_book_review:
            logger.info("[Book V3] Project-dir-first image mode")
            
            # Extract book context for entity grounding
            book_author = ''
            book_title_clean = article_title
            if script.article and hasattr(script.article, 'book_source') and script.article.book_source:
                book = script.article.book_source
                book_author = book.author or ''
                book_title_clean = book.title or article_title
            
            # Download book cover directly to project dir (scene 1)
            if not prefetched_images:
                if script.article and hasattr(script.article, 'book_source') and script.article.book_source:
                    book = script.article.book_source
                    if book.cover_url:
                        cover_path = self._download_book_cover(
                            book.cover_url, book.title, 
                            output_dir=project_image_dir
                        )
                        if cover_path:
                            prefetched_images.insert(0, cover_path)
                            logger.info(f"[Book V3] Cover saved to project: {cover_path.name}")
            
            # Build entity-grounding context prefix (quoted for exact phrase matching)
            entity_context = f'"{book_title_clean}"'
            if book_author:
                entity_context = f'"{book_title_clean}" {book_author}'
            logger.info(f"[Book V3] Entity context: {entity_context}")
            
            # Per-scene image search → saved directly to project dir
            scene_images = {}  # Map scene index -> image path
            image_source = settings.get("image_source", "stock")
            
            # When AI-generated images are selected, force images_only background mode
            # so the render loop uses AI images as backgrounds (not stock videos)
            if image_source == "ai_generated":
                settings["background_mode"] = "images_only"
                logger.info("[Book V3] AI image source selected → forcing background_mode=images_only")
            
            for i, scene in enumerate(scenes_with_timing):
                # Scene 1 (Hook) uses the cover
                if i == 0 and prefetched_images:
                    scene_images[i] = prefetched_images[0]
                    logger.info(f"[Book V3] Scene {i+1}: Using book cover")
                    continue
                
                # Check if scene image already exists in project dir
                # SKIP cache when image_source is ai_generated — always regenerate
                if image_source != "ai_generated":
                    existing_scene = project_image_dir / f"scene_{i+1}.jpg"
                    if existing_scene.exists():
                        scene_images[i] = existing_scene
                        logger.info(f"[Book V3] Scene {i+1}: Reusing {existing_scene.name}")
                        continue
                
                # Detect if scene text uses personal pronouns → enable human presence boost
                scene_text = (scene.get("text", "") or "").lower()
                has_personal_pronouns = any(p in scene_text.split() for p in ['you', 'your', 'i', 'we', 'our', 'my'])
                use_human_boost = has_personal_pronouns and i >= 3  # Scenes 4+ for book reviews
                if use_human_boost:
                    logger.info(f"[HumanBoost] Scene {i+1}: Personal pronouns detected, boosting human imagery")
                
                # === AI IMAGE GENERATION (if image_source is ai_generated or auto) ===
                ai_prompt = None
                if image_source in ("ai_generated", "auto") and self.image_search.gemini_image:
                    ai_prompt = self.image_search.gemini_image.build_scene_prompt(
                        scene_text=scene.get("text", ""),
                        visual_cues=scene.get("visual_cues", ""),
                        book_title=book_title_clean,
                        book_author=book_author,
                        scene_number=i + 1,
                        total_scenes=len(scenes_with_timing)
                    )
                    logger.info(f"[Book V3] Scene {i+1}: Built AI prompt ({len(ai_prompt)} chars)")
                
                # Search for scene-specific image with entity grounding
                keywords = scene.get("image_keywords", [])
                found = False
                
                # If AI prompt is available, try Gemini first via orchestrator
                if ai_prompt:
                    try:
                        image_path = loop.run_until_complete(
                            self.image_search.search_image_async(
                                keywords=[f"{book_title_clean} scene {i+1}"],
                                topic_query=None,
                                orientation="portrait",
                                content_type=content_type_hint,
                                output_dir=project_image_dir,
                                ai_prompt=ai_prompt
                            )
                        )
                        if image_path:
                            import shutil
                            scene_dest = project_image_dir / f"scene_{i+1}.png"
                            if image_path != scene_dest:
                                shutil.copy(image_path, scene_dest)
                                image_path = scene_dest
                            scene_images[i] = image_path
                            found = True
                            logger.info(f"[Book V3] Scene {i+1}: AI-generated {scene_dest.name}")
                    except Exception as e:
                        logger.warning(f"[Book V3] Scene {i+1} AI generation failed: {e}")
                
                # Fallback to stock search if AI didn't produce an image
                if not found:
                    for keyword in keywords[:2]:
                        grounded_query = f"{entity_context} {keyword}"
                        logger.info(f"[Book V3] Scene {i+1}: Searching '{grounded_query[:80]}'...")
                        try:
                            image_path = loop.run_until_complete(
                                self.image_search.search_image_async(
                                    keywords=[f"{book_title_clean} {keyword}"],
                                    topic_query=grounded_query[:120],
                                    orientation="portrait",
                                    content_type=content_type_hint,
                                    output_dir=project_image_dir,
                                    human_presence_boost=use_human_boost
                                )
                            )
                            if image_path:
                                # Rename to scene_N.jpg for organized storage
                                import shutil
                                scene_dest = project_image_dir / f"scene_{i+1}.jpg"
                                if image_path != scene_dest:
                                    shutil.copy(image_path, scene_dest)
                                    image_path = scene_dest
                                
                                scene_images[i] = image_path
                                found = True
                                logger.info(f"[Book V3] Scene {i+1}: Saved {scene_dest.name}")
                                break
                        except Exception as e:
                            logger.warning(f"[Book V3] Scene {i+1} search failed: {e}")
                
                if not found:
                    fallback = prefetched_images[0] if prefetched_images else None
                    if fallback:
                        scene_images[i] = fallback
                        logger.info(f"[Book V3] Scene {i+1}: Fallback to cover")
            
            # === BOOK OBJECT GROUNDING: 30% Rule ===
            # Ensure the physical book appears in at least 3 of 8 scenes.
            # Count scenes that already use the book cover image.
            if prefetched_images:
                cover_path_str = str(prefetched_images[0])
                book_scene_count = sum(
                    1 for idx, path in scene_images.items()
                    if str(path) == cover_path_str or 'cover' in str(path).lower()
                )
                # Scene 0 always has cover; check if we need more
                min_book_scenes = 3
                if book_scene_count < min_book_scenes:
                    # Inject book cover into unfilled scene slots (prefer scene 7, then 4, then 5)
                    priority_slots = [6, 3, 4]  # 0-indexed: scene 7, 4, 5
                    for slot in priority_slots:
                        if book_scene_count >= min_book_scenes:
                            break
                        if slot < len(scenes_with_timing) and slot not in scene_images:
                            scene_images[slot] = prefetched_images[0]
                            book_scene_count += 1
                            logger.info(f"[Book30%] Injected book cover into scene {slot+1} (grounding)")
                
                logger.info(f"[Book30%] Book present in {book_scene_count}/{len(scenes_with_timing)} scenes")
            
            # Summary
            unique_count = len(set(str(v) for v in scene_images.values()))
            logger.info(f"[Book V3] {unique_count} unique images across {len(scene_images)} scenes in {project_image_dir}")
        else:
            # Non-book content: fetch images into project dir
            all_keywords = []
            for scene in scenes_with_timing:
                all_keywords.extend(scene.get("image_keywords", []))
            
            # Remove duplicates while preserving order
            seen = set()
            unique_keywords = [k for k in all_keywords if not (k in seen or seen.add(k))]
            
            # Search for up to 6 images, save to project dir
            for keyword in unique_keywords[:6]:
                search_query = f"{article_title} {keyword}" if article_title else keyword
                logger.info(f"[Pre-fetch] Searching: {search_query[:60]}...")
                
                try:
                    image_path = loop.run_until_complete(
                        self.image_search.search_image_async(
                            keywords=[keyword],
                            topic_query=search_query[:100],
                            orientation="portrait",
                            content_type=content_type_hint,
                            output_dir=project_image_dir
                        )
                    )
                    if image_path and image_path not in prefetched_images:
                        prefetched_images.append(image_path)
                        logger.info(f"[Pre-fetch] Got: {image_path.name}")
                except Exception as e:
                    logger.warning(f"Pre-fetch failed for '{keyword}': {e}")
            
            logger.info(f"Pre-fetched {len(prefetched_images)} images to {project_image_dir}")
            scene_images = {}  # Not used for non-book content
        
        # ===== PRE-RENDER: PLAN INTERRUPTS + VALIDATE ASSETS =====
        # Generate alternating Ken Burns directions (7-second reset logic)
        scene_directions = self.pattern_interrupt.get_scene_directions(len(scenes_with_timing))
        logger.info(f"[PatternInterrupt] Scene directions: {scene_directions}")
        
        # Validate all pre-fetched scene images exist before entering render loop
        # Prevents 'black screen' errors from stale paths or failed downloads
        if is_book_review and scene_images:
            for idx in list(scene_images.keys()):
                img_path = scene_images[idx]
                if img_path and not Path(img_path).exists():
                    logger.warning(f"[AssetCheck] Scene {idx+1} image missing: {img_path} — falling back to cover")
                    scene_images[idx] = prefetched_images[0] if prefetched_images else None
            logger.info(f"[AssetCheck] Asset validation complete for {len(scene_images)} scenes")
        
        # Plan audio/visual interrupts (used for SFX layer later)
        interrupt_plan = self.pattern_interrupt.plan_interrupts(scenes_with_timing, duration)
        
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
            
            # ===== BACKGROUND MODE LOGIC =====
            # Read background_mode from render settings (auto, images_only, videos_only, mixed)
            background_mode = settings.get("background_mode", "auto")
            logger.info(f"[Background] Mode: {background_mode} for scene {i+1}")
            
            # Retention Logic: alternating push-in/pull-out Ken Burns direction
            kb_direction = scene_directions[i] if i < len(scene_directions) else "push_in"
            
            # BOOK REVIEW V3: Scene 1 (Hook) always uses book cover image
            # Scenes 2+ try video first for visual variety, then fall back to images
            if is_book_review and i == 0 and i in scene_images:
                image_path = scene_images[i]
                logger.info(f"[Book V3] Scene 1 (Hook): Using book cover {image_path.name}")
                bg_clip = self._create_ken_burns_clip(image_path, scene_duration, (w, h), direction=kb_direction)
            elif background_mode == "images_only":
                # Images only mode: use pre-fetched images, skip video search entirely
                if i in scene_images:
                    image_path = scene_images[i]
                    logger.info(f"[Images Only] Scene {i+1}: Using image {image_path.name}")
                    bg_clip = self._create_ken_burns_clip(image_path, scene_duration, (w, h), direction=kb_direction)
            elif is_book_review and i in scene_images and not self.video_search:
                # No video service available — use pre-fetched image
                image_path = scene_images[i]
                logger.info(f"[Book V3] Scene {i+1}: Using image (no video service) {image_path.name}")
                bg_clip = self._create_ken_burns_clip(image_path, scene_duration, (w, h), direction=kb_direction)
            
            # PRIORITY 0.5: Try Veo AI video generation (if video_source is "veo")
            video_source = settings.get("video_source", "stock")
            if bg_clip is None and video_source == "veo" and self.veo_video and background_mode != "images_only":
                try:
                    scene_text_for_vid = scene.get("text", "")
                    visual_cues_for_vid = scene.get("visual_cues", "")
                    veo_prompt = self.veo_video.build_scene_prompt(
                        scene_text=scene_text_for_vid,
                        visual_cues=visual_cues_for_vid,
                        book_title=article_title if is_book_review else "",
                        book_author=book_author if is_book_review else "",
                        scene_number=i + 1,
                        total_scenes=len(scenes_with_timing),
                        content_type=content_type_hint or "daily_update",
                    )
                    veo_output = project_video_dir / f"scene_{i+1}_veo.mp4"
                    logger.info(f"[Veo] Scene {i+1}: Generating AI video ({len(veo_prompt)} chars)")
                    veo_path = loop.run_until_complete(
                        self.veo_video.generate_video(
                            prompt=veo_prompt,
                            output_path=veo_output,
                        )
                    )
                    if veo_path:
                        bg_clip = self._create_video_background(veo_path, scene_duration, (w, h))
                        if bg_clip:
                            logger.info(f"[Veo] Scene {i+1}: Using AI-generated video")
                except Exception as veo_err:
                    logger.warning(f"[Veo] Scene {i+1} generation failed (falling back): {veo_err}")
            
            # PRIORITY 1: Try to get a stock VIDEO (unless images_only mode)
            if bg_clip is None and self.video_search and keywords and background_mode != "images_only":
                for keyword in keywords:
                    logger.info(f"[Video] Searching for: {keyword}")
                    video_path = self.video_search.search_video(
                        [keyword], 
                        orientation="portrait",
                        min_duration=5,
                        max_duration=30,
                        output_dir=project_video_dir
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
                bg_clip = self._create_ken_burns_clip(image_path, scene_duration, (w, h), direction=kb_direction)
            
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
                                content_type=content_type_hint,
                                output_dir=project_image_dir
                            )
                        )
                        if image_path:
                            bg_clip = self._create_ken_burns_clip(image_path, scene_duration, (w, h), direction=kb_direction)
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
            
            # Add fade/crossfade transitions (driven by transition_hint from script)
            transition_hint = scene.get("transition_hint", "fade") if is_book_review else "fade"
            effects = []
            if i > 0:
                if transition_hint == "cut":
                    # Hard cut: no transition effect
                    pass
                elif transition_hint == "match_cut":
                    # Quick dissolve for match-cuts (abstract → human reaction)
                    effects.append(vfx.FadeIn(0.3))
                else:
                    # Default fade
                    fade_duration = 0.8 if is_book_review else 0.5
                    effects.append(vfx.FadeIn(fade_duration))
            if i < len(scenes_with_timing) - 1:
                # Fade out uses same hint as the NEXT scene's transition_hint
                next_hint = scenes_with_timing[i + 1].get("transition_hint", "fade") if is_book_review else "fade"
                if next_hint == "cut":
                    pass
                elif next_hint == "match_cut":
                    effects.append(vfx.FadeOut(0.3))
                else:
                    fade_duration = 0.8 if is_book_review else 0.5
                    effects.append(vfx.FadeOut(fade_duration))
            if effects:
                scene_clip = scene_clip.with_effects(effects)
            
            scene_clips.append(scene_clip)
        
        # Create subtitle clips — sentence-level for book reviews (YouTube CC style), word-level for others
        if is_book_review:
            logger.info("Creating sentence-level subtitles (Book V3 — YouTube CC style)...")
            # Extract timestamps for kinetic typography color flip (visual pattern interrupt)
            visual_interrupt_times = [ev["time"] for ev in interrupt_plan]
            all_subtitle_clips = self._create_sentence_subtitles(
                all_words, all_segments, (w, h), interrupt_times=visual_interrupt_times
            )
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
        
        # ── SFX Layer: Pattern Interrupt Audio Resets ──
        # Inject subtle whoosh/thud sound effects at planned interrupt timestamps
        # to refresh viewer attention every 7-10 seconds (only for book reviews)
        if is_book_review and interrupt_plan:
            sfx_clips = [final_audio]
            sfx_added = 0
            for interrupt in interrupt_plan:
                if interrupt.get("type") == "audio":
                    sfx_time = interrupt["time"]
                    sfx_type = interrupt.get("sfx_type", "whoosh")
                    if sfx_time < duration - 0.5:
                        try:
                            sfx_clip = self.pattern_interrupt.get_sfx_clip(sfx_type, duration=0.3)
                            if sfx_clip:
                                sfx_clip = sfx_clip.with_start(sfx_time).with_volume_scaled(0.08)
                                sfx_clips.append(sfx_clip)
                                sfx_added += 1
                        except Exception as sfx_e:
                            logger.warning(f"[SFX] Failed to add {sfx_type} at {sfx_time:.1f}s: {sfx_e}")
            if sfx_added > 0:
                final_audio = CompositeAudioClip(sfx_clips)
                logger.info(f"[PatternInterrupt] Added {sfx_added} SFX clips to audio mix")
        
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

    def _download_book_cover(self, cover_url: str, book_title: str, output_dir: Optional[Path] = None) -> Optional[Path]:
        """Download book cover from OpenLibrary directly to project folder."""
        import httpx
        
        # Save to project dir if specified, otherwise fallback
        cover_dir = output_dir or Path("data/images/_cache")
        cover_dir.mkdir(parents=True, exist_ok=True)
        cover_path = cover_dir / "cover.jpg"
        
        if cover_path.exists() and cover_path.stat().st_size > 1000:
            logger.info(f"[Book] Using existing cover: {cover_path}")
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

    def _create_ken_burns_clip(
        self,
        image_path: Path,
        duration: float,
        size: Tuple[int, int],
        zoom: float = None,
        direction: str = "push_in"
    ):
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
            direction: "push_in" (zoom in) or "pull_out" (zoom out) for 7-second reset
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
        logger.info(f"[KenBurns] {direction} | Image {img_w}x{img_h} (aspect={img_aspect:.3f}), target={target_aspect:.3f}, diff={aspect_diff:.3f}")
        
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
        
        # Apply Ken Burns zoom effect — direction controls push-in vs pull-out
        if direction == "pull_out":
            # Pull-out: start zoomed in, slowly zoom back out (7-second reset)
            zoom_start = target_zoom
            zoom_end = 1.0
        else:
            # Push-in (default): start at 1.0, slowly zoom in
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
    
    def _create_sentence_subtitles(
        self, 
        words: List[Dict], 
        segments: List[Dict], 
        video_size: Tuple[int, int],
        interrupt_times: List[float] = None
    ) -> List[TextClip]:
        """Create sentence-level subtitle clips (YouTube CC style).
        
        Implements kinetic typography color flip as a 7-second pattern interrupt:
        subtitle color alternates between white and warm gold at each interrupt
        boundary, keeping viewer attention without changing layout.
        
        Args:
            words: List of word timing dicts (fallback if segments unavailable)
            segments: List of Whisper segment dicts with 'text', 'start', 'end'
            video_size: (width, height) tuple
            interrupt_times: List of timestamps (seconds) where color flips occur
        """
        w, h = video_size
        clips = []
        
        # Position at 75% from top — slightly higher than phrase subtitles
        # to accommodate multi-line text while staying in safe zone
        y_position = int(h * 0.75)
        
        # Max characters per line before wrapping
        MAX_CHARS_PER_LINE = 35
        
        # ── Kinetic Typography Color Palette ──
        # Alternates at each pattern interrupt boundary for visual retention
        COLOR_PALETTE = [
            ('white', 'black'),       # Default: white text, black stroke
            ('#FFD700', '#1a1a1a'),   # Warm gold text, dark stroke (brand accent)
        ]
        
        if not segments:
            # Fallback to phrase-level if no segments available
            logger.warning("No Whisper segments available, falling back to phrase subtitles")
            return self._create_phrase_subtitles(words, video_size)
        
        color_index = 0
        sorted_interrupt_times = sorted(interrupt_times or [])
        next_flip_idx = 0  # Index into sorted_interrupt_times
        
        for seg in segments:
            text = seg.get("text", "").strip()
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            seg_duration = end - start
            
            if not text or seg_duration <= 0:
                continue
            
            # Minimum duration to prevent flashing
            if seg_duration < 0.5:
                seg_duration = 0.5
            
            # Check if we've crossed a pattern interrupt threshold → flip color
            while (next_flip_idx < len(sorted_interrupt_times) and
                   start >= sorted_interrupt_times[next_flip_idx]):
                color_index = (color_index + 1) % len(COLOR_PALETTE)
                next_flip_idx += 1
            
            text_color, stroke_color = COLOR_PALETTE[color_index]
            
            # Auto-wrap long sentences into multiple lines
            if len(text) > MAX_CHARS_PER_LINE:
                words_in_text = text.split()
                lines = []
                current_line = []
                current_len = 0
                
                for word in words_in_text:
                    if current_len + len(word) + 1 > MAX_CHARS_PER_LINE and current_line:
                        lines.append(" ".join(current_line))
                        current_line = [word]
                        current_len = len(word)
                    else:
                        current_line.append(word)
                        current_len += len(word) + 1
                
                if current_line:
                    lines.append(" ".join(current_line))
                
                # Cap at 3 lines max
                display_text = "\n".join(lines[:3])
            else:
                display_text = text
            
            # Determine font size based on text length
            if len(text) > 80:
                font_size = 40
            elif len(text) > 50:
                font_size = 46
            else:
                font_size = 52
            
            txt_clip = (
                TextClip(
                    text=display_text,
                    font_size=font_size,
                    color=text_color,
                    font='/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                    stroke_color=stroke_color,
                    stroke_width=3,
                    text_align='center',
                    method='caption',
                    size=(int(w * 0.9), None)  # 90% width for padding
                )
                .with_position(('center', y_position))
                .with_start(start)
                .with_duration(seg_duration)
            )
            clips.append(txt_clip)
        
        flip_count = next_flip_idx
        logger.info(
            f"Created {len(clips)} sentence subtitle clips (YouTube CC style) at y={y_position}px"
            f" | {flip_count} typography color flips applied"
        )
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
