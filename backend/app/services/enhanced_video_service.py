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
import time
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

# Scenes that receive Veo AI video (0-indexed). For book reviews, only the 3 most
# cinematic beats get Veo — Relatable Story (3), Famous Example (4), Cheat Code (6).
# Other scenes use Gemini AI images with Ken Burns, which is faster and equally cinematic.
VEO_BOOK_REVIEW_SCENES: frozenset = frozenset([2, 3, 5])  # scenes 3, 4, 6 (1-indexed)
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
        video_source: str = "stock",  # stock, veo
        veo_style: str = "auto"  # cinematic, whiteboard, illustration, auto
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
                "video_source": video_source,
                "veo_style": veo_style,
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
        is_book_review  = (content_type_hint == "book_review")
        is_viral_news   = (content_type_hint == "viral_news")
        is_daily_digest = (content_type_hint == "daily_update")
        
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
        
        scene_images = {}  # Map scene index -> image path (populated by book/viral_news paths)

        if is_book_review:
            logger.info("[Book V3] Project-dir-first image mode")
            
            # Extract book context for entity grounding
            book_author = ''
            book_title_clean = article_title
            if script.article and hasattr(script.article, 'book_source') and script.article.book_source:
                book = script.article.book_source
                book_author = book.author or ''
                book_title_clean = book.title or article_title
            
            # Read image/video source settings early (needed for cover generation decision)
            image_source = settings.get("image_source", "stock")
            video_source_pref = settings.get("video_source", "stock")

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

            # AI image mode: generate Gemini AI book cover for Scene 1 (better quality than low-res thumbnail)
            if image_source == "ai_generated" and self.image_search.gemini_image and book_title_clean:
                ai_cover_dest = project_image_dir / "scene_1.png"
                if not ai_cover_dest.exists():
                    author_part = f' by {book_author}' if book_author else ''
                    cover_ai_prompt = (
                        f'Cinematic photorealistic image for a book review video about '
                        f'"{book_title_clean}"{author_part}. '
                        'The physical book is prominently featured — held in hands, '
                        'displayed on a reading desk, or placed in a cozy library nook. '
                        'Warm golden-hour lighting, shallow depth of field, vertical 9:16 composition. '
                        'Rich colors, inviting atmosphere. No text overlays, no watermarks. '
                        '8K cinematic quality.'
                    )
                    ai_cover = loop.run_until_complete(
                        self.image_search.gemini_image.generate_image(
                            prompt=cover_ai_prompt,
                            output_path=ai_cover_dest
                        )
                    )
                    if ai_cover:
                        if prefetched_images:
                            prefetched_images[0] = ai_cover
                        else:
                            prefetched_images.insert(0, ai_cover)
                        logger.info(f"[Book AI Cover] Scene 1: Gemini AI cover → {ai_cover_dest.name}")

            # Build entity-grounding context prefix (quoted for exact phrase matching)
            entity_context = f'"{book_title_clean}"'
            if book_author:
                entity_context = f'"{book_title_clean}" {book_author}'
            logger.info(f"[Book V3] Entity context: {entity_context}")

            # Force images_only ONLY when AI images are selected WITHOUT Veo.
            # When Veo is also requested, let Veo run first and use AI images as fallback.
            if image_source == "ai_generated" and video_source_pref != "veo":
                settings["background_mode"] = "images_only"
                logger.info("[Book V3] AI-only mode → forcing images_only (Veo not requested)")
            
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
        elif is_viral_news:
            # ── Viral News: per-scene image mapping with entity grounding ──
            # Same quality pipeline as book review — scene_images dict populated for
            # images_only mode, AI fallback (priority 0.75), and asset validation.
            import shutil as _shutil
            image_source_vn = settings.get("image_source", "stock")
            video_source_vn = settings.get("video_source", "stock")

            # AI-only mode: no stock videos needed
            if image_source_vn == "ai_generated" and video_source_vn != "veo":
                settings["background_mode"] = "images_only"
                logger.info("[VN] AI-only mode → forcing images_only")

            for i, scene in enumerate(scenes_with_timing):
                # Reuse cached image from previous run (skip for ai_generated)
                if image_source_vn != "ai_generated":
                    cached = project_image_dir / f"scene_{i+1}.jpg"
                    if cached.exists():
                        scene_images[i] = cached
                        logger.info(f"[VN] Scene {i+1}: Reusing cached image")
                        continue

                # Human presence boost when narration addresses the viewer directly
                scene_text_vn = (scene.get("text", "") or "").lower()
                use_human_boost_vn = any(
                    p in scene_text_vn.split() for p in ("you", "your", "we", "our")
                )

                found = False

                # ── Try Gemini AI image generation first ──
                if image_source_vn in ("ai_generated", "auto") and self.image_search.gemini_image:
                    visual_cues_vn = scene.get("visual_cues", "")
                    if visual_cues_vn:
                        ai_prompt_vn = (
                            f"Photojournalistic cinematic image for a viral news short.\n"
                            f"STORY: {article_title}\n"
                            f"SCENE {i+1} of {len(scenes_with_timing)}: "
                            f"{scene.get('text', '')[:120]}\n"
                            f"VISUAL DIRECTION: {visual_cues_vn}\n"
                            "Style: Vertical 9:16, photojournalistic, raw lighting, "
                            "motion blur, 8k, sharp news aesthetic."
                        )
                        try:
                            ai_img = loop.run_until_complete(
                                self.image_search.search_image_async(
                                    keywords=[f"{article_title} scene {i+1}"],
                                    topic_query=None,
                                    orientation="portrait",
                                    content_type=content_type_hint,
                                    output_dir=project_image_dir,
                                    ai_prompt=ai_prompt_vn,
                                )
                            )
                            if ai_img:
                                dest = project_image_dir / f"scene_{i+1}.png"
                                if ai_img != dest:
                                    _shutil.copy(ai_img, dest)
                                scene_images[i] = dest
                                found = True
                                logger.info(f"[VN AI] Scene {i+1}: Generated → {dest.name}")
                        except Exception as e:
                            logger.warning(f"[VN AI] Scene {i+1} generation failed: {e}")

                # ── Stock image fallback with entity grounding ──
                if not found:
                    keywords_vn = scene.get("image_keywords", [])
                    for kw in keywords_vn[:2]:
                        grounded = f"{article_title} {kw}" if article_title else kw
                        try:
                            stock_img = loop.run_until_complete(
                                self.image_search.search_image_async(
                                    keywords=[kw],
                                    topic_query=grounded[:120],
                                    orientation="portrait",
                                    content_type=content_type_hint,
                                    output_dir=project_image_dir,
                                    human_presence_boost=use_human_boost_vn,
                                )
                            )
                            if stock_img:
                                dest = project_image_dir / f"scene_{i+1}.jpg"
                                if stock_img != dest:
                                    _shutil.copy(stock_img, dest)
                                scene_images[i] = dest
                                found = True
                                logger.info(f"[VN] Scene {i+1}: Stock → {dest.name}")
                                break
                        except Exception as e:
                            logger.warning(f"[VN] Scene {i+1} stock search failed: {e}")

            logger.info(f"[VN] {len(scene_images)}/{len(scenes_with_timing)} scenes have images")

        elif is_daily_digest:
            # ── Daily Digest: per-scene image mapping, grounded by story company ──
            # Mirrors the viral_news pipeline. Each scene gets an image grounded to
            # its specific news story (company name + visual_cues + image_keywords).
            import shutil as _shutil_dd
            image_source_dd = settings.get("image_source", "stock")
            video_source_dd = settings.get("video_source", "stock")

            # AI-only mode: no stock videos needed
            if image_source_dd == "ai_generated" and video_source_dd != "veo":
                settings["background_mode"] = "images_only"
                logger.info("[DD] AI-only mode → forcing images_only")

            # ── Static brand image for hook / thread / CTA scenes ──────────
            _AI_INSIDER_IMG = Path("data/projects/news/AIInsider.png")
            _COMPANY_LOGOS_DIR = Path("assets/company_logos")
            _COMPANY_LOGOS_DIR.mkdir(parents=True, exist_ok=True)

            # ── Pre-identify thread+insight pair (shared image) ─────────────
            # Consecutive story_index=0 scenes that are NOT hook (i=0) and NOT CTA
            # (last scene) — typically the "connecting thread" + "impact/insight" pair.
            # We generate ONE image for the first in the pair and reuse for the rest.
            n_scenes = len(scenes_with_timing)
            last_idx = n_scenes - 1
            _mid_structural = [
                i for i, sc in enumerate(scenes_with_timing)
                if sc.get("story_index", 0) == 0 and i != 0 and i != last_idx
            ]
            # Map each scene in the pair → the index whose image it will share
            # (first scene generates, subsequent ones reuse)
            _shared_image_map: dict[int, int] = {}  # scene_idx → leader_idx
            if len(_mid_structural) >= 2:
                leader = _mid_structural[0]
                for follower in _mid_structural[1:]:
                    _shared_image_map[follower] = leader
                logger.info(
                    f"[DD] Shared image group: scenes {[i+1 for i in _mid_structural]} "
                    f"(saves {len(_mid_structural)-1} Gemini call(s))"
                )

            for i, scene in enumerate(scenes_with_timing):
                # Reuse cached image from a previous run (skip for ai_generated)
                if image_source_dd != "ai_generated":
                    cached = project_image_dir / f"scene_{i+1}.jpg"
                    if cached.exists():
                        scene_images[i] = cached
                        logger.info(f"[DD] Scene {i+1}: Reusing cached image")
                        continue

                # Extract scene metadata for grounded prompts
                scene_text_dd   = (scene.get("text", "") or "")
                visual_cues_dd  = (scene.get("visual_cues", "") or "")
                company_dd      = (scene.get("company", "") or "")
                story_index_dd  = scene.get("story_index", 0)  # 0 = hook/thread/cta, >0 = story beat
                keywords_dd     = scene.get("image_keywords", [])

                # ── Shared image reuse (insight/thread pair) ──
                if i in _shared_image_map:
                    leader_i = _shared_image_map[i]
                    leader_img = scene_images.get(leader_i)
                    if leader_img and Path(leader_img).exists():
                        dest = project_image_dir / f"scene_{i+1}{Path(leader_img).suffix}"
                        _shutil_dd.copy(leader_img, dest)
                        scene_images[i] = dest
                        logger.info(
                            f"[DD] Scene {i+1} (insight): Reusing scene {leader_i+1} "
                            f"image → saved 1 Gemini call"
                        )
                        continue



                # ── CTA (last scene only) → use static AIInsider.png brand image ──
                # Hook and insight/thread scenes get unique Gemini images since they
                # each have specific visual cues (AI logos collage, data centers, etc.)
                is_cta_scene = (story_index_dd == 0 and i == len(scenes_with_timing) - 1)
                if is_cta_scene and _AI_INSIDER_IMG.exists():
                    dest = project_image_dir / f"scene_{i+1}.png"
                    _shutil_dd.copy(_AI_INSIDER_IMG, dest)
                    scene_images[i] = dest
                    logger.info(f"[DD] Scene {i+1} (CTA): Using static AIInsider.png brand image")
                    continue

                found = False

                # ── Try company icon logo first (assets/company_logos/openai.png) ──
                if company_dd:
                    company_slug = company_dd.lower().replace(" ", "_").replace("-", "_")
                    for ext in (".png", ".jpg", ".jpeg"):
                        logo_path = _COMPANY_LOGOS_DIR / f"{company_slug}{ext}"
                        if logo_path.exists():
                            dest = project_image_dir / f"scene_{i+1}{ext}"
                            _shutil_dd.copy(logo_path, dest)
                            scene_images[i] = dest
                            found = True
                            logger.info(f"[DD] Scene {i+1} ({company_dd}): Using logo {logo_path.name}")
                            break

                # ── Try Gemini AI image generation (story beats only) ──
                if not found and image_source_dd in ("ai_generated", "auto") and self.image_search.gemini_image:
                    # Build a grounded photojournalistic prompt
                    if story_index_dd and story_index_dd > 0 and company_dd:
                        subject_line = f"COMPANY/TOPIC: {company_dd}"
                    else:
                        subject_line = f"STORY: {article_title}"

                    visual_dir = visual_cues_dd if visual_cues_dd else (
                        keywords_dd[0] if keywords_dd else "news studio photojournalistic"
                    )

                    # AI Insider dark cinematic style prefix — mandatory for all Daily Digest images
                    _DD_STYLE_PREFIX = (
                        "Dark cinematic lighting, shallow depth of field, high-tech bokeh, "
                        "midnight blue and obsidian color palette, hyper-realistic textures, "
                        "professional tech journalism style. "
                        "No overlaid text. No watermarks. No bright office. No generic stock."
                    )

                    # Topic-aware visual direction (maps key AI companies to specific compositions)
                    _DD_TOPIC_MAP = {
                        "openai": "glowing minimalist OpenAI logo on brushed titanium surface, dimly lit research lab background",
                        "google": "Google DeepMind neural network dark server room, blue holographic glow, obsidian surface",
                        "deepmind": "Google DeepMind neural network dark server room, blue holographic glow, obsidian surface",
                        "anthropic": "Claude AI symbol on dark carbon surface, cyan glow, minimal tech lab",
                        "meta": "Meta AI holographic interface, dark studio, midnight blue gradient",
                        "microsoft": "Microsoft Azure dark data center, electric blue light traces, obsidian",
                        "nvidia": "NVIDIA GPU chip on dark motherboard, green circuit glow, hyper-realistic macro",
                        "robot": "robotic hand delicately holding silicon chip, intricate wiring visible, laboratory setting, midnight blue",
                        "robotics": "robotic hand delicately holding silicon chip, intricate wiring visible, laboratory setting, midnight blue",
                        "fund": "venture capital dark boardroom, holographic AI projection on obsidian table, dramatic rim lighting",
                        "policy": "capitol building AI regulation dramatic storm sky, dark cinematic",
                        "regulation": "capitol building AI regulation dramatic storm sky, dark cinematic",
                    }

                    company_lower = company_dd.lower() if company_dd else ""
                    topic_visual = next(
                        (v for k, v in _DD_TOPIC_MAP.items() if k in company_lower or k in visual_dir.lower()),
                        None
                    )

                    if topic_visual:
                        composition = topic_visual
                    elif company_dd:
                        composition = f"{company_dd} product announcement, dark cinematic obsidian surface, high-tech bokeh"
                    else:
                        composition = visual_dir or "AI news investigation, dark cinematic, midnight blue"

                    ai_prompt_dd = (
                        f"{_DD_STYLE_PREFIX}\n"
                        f"{subject_line}\n"
                        f"SCENE {i+1} narration: {scene_text_dd[:150]}\n"
                        f"COMPOSITION: {composition}\n"
                    )

                    # If this is the thread scene (leader of the shared pair), blend in the
                    # insight scene's visual cues to produce an image that works for both
                    _followers = [fi for fi, li in _shared_image_map.items() if li == i]
                    if _followers:
                        next_scene = scenes_with_timing[_followers[0]]
                        next_cues = (next_scene.get("visual_cues") or "")[:120]
                        if next_cues:
                            ai_prompt_dd += f"ALSO COVERS NEXT SCENE: {next_cues}\n"
                    ai_prompt_dd += "Vertical 9:16 portrait orientation. No overlaid text."


                    try:
                        ai_img_dd = loop.run_until_complete(
                            self.image_search.search_image_async(
                                keywords=[f"{company_dd or article_title} scene {i+1}"],
                                topic_query=None,
                                orientation="portrait",
                                content_type=content_type_hint,
                                output_dir=project_image_dir,
                                ai_prompt=ai_prompt_dd,
                            )
                        )
                        if ai_img_dd:
                            dest = project_image_dir / f"scene_{i+1}.png"
                            if ai_img_dd != dest:
                                _shutil_dd.copy(ai_img_dd, dest)
                            scene_images[i] = dest
                            found = True
                            logger.info(f"[DD AI] Scene {i+1} ({company_dd or 'story'}): Gemini → {dest.name}")
                    except Exception as e:
                        logger.warning(f"[DD AI] Scene {i+1} Gemini generation failed: {e}")

                # ── Stock image fallback with company grounding ──
                if not found:
                    for kw in keywords_dd[:2]:
                        grounded_kw = f"{company_dd} {kw}" if company_dd else (
                            f"{article_title} {kw}" if article_title else kw
                        )
                        try:
                            stock_img_dd = loop.run_until_complete(
                                self.image_search.search_image_async(
                                    keywords=[kw],
                                    topic_query=grounded_kw[:120],
                                    orientation="portrait",
                                    content_type=content_type_hint,
                                    output_dir=project_image_dir,
                                )
                            )
                            if stock_img_dd:
                                dest = project_image_dir / f"scene_{i+1}.jpg"
                                if stock_img_dd != dest:
                                    _shutil_dd.copy(stock_img_dd, dest)
                                scene_images[i] = dest
                                found = True
                                logger.info(f"[DD] Scene {i+1}: Stock ({grounded_kw[:60]}) → {dest.name}")
                                break
                        except Exception as e:
                            logger.warning(f"[DD] Scene {i+1} stock search failed: {e}")

            logger.info(f"[DD] {len(scene_images)}/{len(scenes_with_timing)} scenes have images")

        else:
            # Generic non-viral non-book non-digest content: bulk prefetch up to 6 images
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
            scene_images = {}  # Not used for generic content
        
        # ===== PRE-RENDER: PLAN INTERRUPTS + VALIDATE ASSETS =====
        # Generate alternating Ken Burns directions (7-second reset logic)
        scene_directions = self.pattern_interrupt.get_scene_directions(len(scenes_with_timing))
        logger.info(f"[PatternInterrupt] Scene directions: {scene_directions}")

        # Story beat timing tracker — used to build per-scene ticker overlay for Daily Digest.
        # Each entry: {"company": str, "story_index": int, "start": float, "duration": float}
        dd_story_beats: list = []
        
        # Validate all pre-fetched scene images exist before entering render loop
        # Prevents 'black screen' errors from stale paths or failed downloads
        if (is_book_review or is_viral_news or is_daily_digest) and scene_images:
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
        callout_clips = []  # Kinetic punch callouts (book review only)
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
            video_source = settings.get("video_source", "stock")  # read early so elif guards can use it
            image_source_render = settings.get("image_source", "stock")  # used for AI image fallback
            logger.info(f"[Background] Mode: {background_mode}, Video: {video_source}, Image: {image_source_render} for scene {i+1}")
            
            # Retention Logic: alternating push-in/pull-out Ken Burns direction
            kb_direction = scene_directions[i] if i < len(scene_directions) else "push_in"
            
            # BOOK REVIEW V3: Scene 1 (Hook) always uses book cover image
            # Scenes 2+ try video first for visual variety, then fall back to images
            if is_book_review and i == 0 and i in scene_images:
                image_path = scene_images[i]
                logger.info(f"[Book V3] Scene 1 (Hook): Using book cover {image_path.name}")
                bg_clip = self._create_ken_burns_clip(image_path, scene_duration, (w, h), direction=kb_direction, scene_index=i)
            elif background_mode == "images_only":
                # Images only mode: use pre-fetched images, skip video search entirely
                if i in scene_images:
                    image_path = scene_images[i]
                    logger.info(f"[Images Only] Scene {i+1}: Using image {image_path.name}")
                    bg_clip = self._create_ken_burns_clip(image_path, scene_duration, (w, h), direction=kb_direction, scene_index=i)
            elif is_book_review and i in scene_images and not self.video_search and video_source != "veo":
                # No video service available AND user didn't explicitly request Veo — use pre-fetched image
                image_path = scene_images[i]
                logger.info(f"[Book V3] Scene {i+1}: Using image (no video service) {image_path.name}")
                bg_clip = self._create_ken_burns_clip(image_path, scene_duration, (w, h), direction=kb_direction, scene_index=i)
            elif is_daily_digest and i in scene_images and not self.video_search and video_source != "veo":
                # Daily Digest: no video service available — use per-scene Gemini/stock image with Ken Burns
                image_path = scene_images[i]
                logger.info(f"[DD] Scene {i+1}: Using image (no video service) {image_path.name}")
                bg_clip = self._create_ken_burns_clip(image_path, scene_duration, (w, h), direction=kb_direction, scene_index=i)
            
            # PRIORITY 0.5: Try Veo AI video generation (if video_source is "veo")
            # For book reviews: Veo only fires on the 3 most cinematic beats (scenes 3, 4, 6).
            # Other scenes use Gemini AI images — faster, equally cinematic for those beats.
            veo_allowed = (
                not is_book_review              # non-book: Veo allowed on all scenes
                or i in VEO_BOOK_REVIEW_SCENES  # book review: only scenes 3, 4, 6 (0-indexed: 2, 3, 5)
            )
            if is_book_review and video_source == "veo" and not veo_allowed:
                logger.info(f"[Veo] Scene {i+1}: Skipping (not in VEO_BOOK_REVIEW_SCENES — AI image fallback used)")
            if veo_allowed and bg_clip is None and video_source == "veo" and self.veo_video and background_mode != "images_only":
                try:
                    scene_text_for_vid = scene.get("text", "")
                    visual_cues_for_vid = scene.get("visual_cues", "")

                    # Resolve style for this specific scene
                    veo_style_setting = settings.get("veo_style", "auto")
                    effective_style = self.veo_video.resolve_scene_style(veo_style_setting, i + 1)

                    veo_prompt = self.veo_video.build_prompt(
                        veo_style=effective_style,
                        scene_number=i + 1,
                        scene_text=scene_text_for_vid,
                        visual_cues=visual_cues_for_vid,
                        book_title=article_title if is_book_review else "",
                        book_author=book_author if is_book_review else "",
                        total_scenes=len(scenes_with_timing),
                        content_type=content_type_hint or "daily_update",
                    )
                    veo_output = project_video_dir / f"scene_{i+1}_veo_{effective_style}.mp4"
                    logger.info(f"[Veo] Scene {i+1}: style={effective_style} ({len(veo_prompt)} chars)")
                    veo_path = loop.run_until_complete(
                        self.veo_video.generate_video(
                            prompt=veo_prompt,
                            output_path=veo_output,
                        )
                    )
                    if veo_path:
                        bg_clip = self._create_video_background(veo_path, scene_duration, (w, h))
                        if bg_clip:
                            logger.info(f"[Veo] Scene {i+1}: Using AI-generated video ({effective_style})")
                except Exception as veo_err:
                    logger.warning(f"[Veo] Scene {i+1} generation failed (falling back): {veo_err}")
                finally:
                    # Rate-limit: space out sequential Veo calls to avoid 429 quota errors
                    if i < len(scenes_with_timing) - 1:
                        time.sleep(5)
            
            # PRIORITY 0.75: Gemini AI image fallback (Veo failed or not selected, AI images requested)
            # This is the "Nano Banana" fallback — cinematic AI image with Ken Burns beats stock video.
            if bg_clip is None and i in scene_images and image_source_render in ("ai_generated", "auto"):
                image_path = scene_images[i]
                logger.info(f"[AI Image] Scene {i+1}: Gemini AI image fallback (Nano Banana) → {image_path.name}")
                bg_clip = self._create_ken_burns_clip(image_path, scene_duration, (w, h), direction=kb_direction, scene_index=i)

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
                bg_clip = self._create_ken_burns_clip(image_path, scene_duration, (w, h), direction=kb_direction, scene_index=i)
            
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
                            bg_clip = self._create_ken_burns_clip(image_path, scene_duration, (w, h), direction=kb_direction, scene_index=i)
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
            # Both book review and viral news honour per-scene transition hints.
            use_hints = is_book_review or is_viral_news
            transition_hint = scene.get("transition_hint", "fade") if use_hints else "fade"
            effects = []
            if i > 0:
                if transition_hint == "cut":
                    # Hard cut: no transition effect
                    pass
                elif transition_hint == "match_cut":
                    # Quick dissolve for match-cuts
                    effects.append(vfx.FadeIn(0.3))
                else:
                    # Default fade — shorter for news (punchy), longer for book (cinematic)
                    fade_duration = 0.8 if is_book_review else 0.4
                    effects.append(vfx.FadeIn(fade_duration))
            if i < len(scenes_with_timing) - 1:
                # Fade out uses same hint as the NEXT scene's transition_hint
                next_hint = scenes_with_timing[i + 1].get("transition_hint", "fade") if use_hints else "fade"
                if next_hint == "cut":
                    pass
                elif next_hint == "match_cut":
                    effects.append(vfx.FadeOut(0.3))
                else:
                    fade_duration = 0.8 if is_book_review else 0.4
                    effects.append(vfx.FadeOut(fade_duration))
            if effects:
                scene_clip = scene_clip.with_effects(effects)
            
            scene_clips.append(scene_clip)

            # Collect story beat timing for Daily Digest per-scene ticker overlay
            if is_daily_digest:
                dd_story_beats.append({
                    "company":       scene.get("company", "").strip(),
                    "story_index":   scene.get("story_index", 0),
                    "text":          scene.get("text", ""),
                    "start":         scene_start,
                    "duration":      scene_duration,
                    # True for hook / connecting thread / insight / CTA — no ticker badge
                    "is_structural": (scene.get("story_index", 0) == 0),
                })

            # ── Kinetic callout (book review only) ──────────────────────────────
            # Bold 2-3 word punch text that animates in at scene start (0→1.5s).
            # Gold accent for the 3 punchy beats (scenes 1, 4, 6); white for others.
            if is_book_review:
                callout_text = scene.get("callout", "").strip().upper()
                if callout_text:
                    accent = i in (0, 3, 5)  # scenes 1, 4, 6 (0-indexed)
                    callout_clip = self._create_kinetic_callout(
                        callout_text=callout_text,
                        video_size=(w, h),
                        scene_start=scene_start,
                        accent=accent,
                    )
                    if callout_clip:
                        callout_clips.append(callout_clip)
                        logger.info(f"[Callout] Scene {i+1}: '{callout_text}' (accent={accent})")

        # Create subtitle clips — sentence-level CC style for book review + viral news,
        # word-level for all other content types.
        if is_book_review or is_viral_news or is_daily_digest:
            logger.info("Creating sentence-level subtitles (YouTube CC style + kinetic color flip)...")
            visual_interrupt_times = [ev["time"] for ev in interrupt_plan]
            all_subtitle_clips = self._create_sentence_subtitles(
                all_words, all_segments, (w, h), interrupt_times=visual_interrupt_times,
                is_daily_digest=is_daily_digest
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
        
        # Source attribution overlay for viral news (top bar, first 8 seconds)
        source_overlay_clips = []
        if is_viral_news:
            news_source = ''
            news_category = ''
            if script.article:
                news_source = script.article.author or ''
                if hasattr(script.article, 'viral_news_source') and script.article.viral_news_source:
                    news_source = news_source or (script.article.viral_news_source.source_name or '')
                    news_category = script.article.viral_news_source.news_category or ''
            if news_source:
                source_overlay_clips = self._create_news_source_overlay(
                    source_name=news_source,
                    category=news_category,
                    duration=min(8.0, duration),
                    video_size=(w, h),
                )
                logger.info(f"[SourceOverlay] Via '{news_source}' ({news_category})")

        # AI INSIDER EXCLUSIVE header overlay for Daily Digest (Y: 10%–20% safe zone)
        # Persistent static title bar — bold condensed font, 2px drop shadow
        digest_header_clips = []
        if is_daily_digest:
            digest_header_clips = self._create_digest_header_overlay(
                duration=duration,
                video_size=(w, h),
                article_title=getattr(script, "catchy_title", None) or article_title or "",
            )
            logger.info("[DigestHeader] Added 'AI INSIDER EXCLUSIVE' header overlay")

        # Per-scene story title ticker for Daily Digest (Y: ~22% — below header bar)
        # Shows which company/story is currently being covered:
        # e.g. "STORY 1 · OPENAI"  →  "STORY 2 · ANTHROPIC"  →  "STORY 3 · GOOGLE"
        story_ticker_clips = []
        if is_daily_digest and dd_story_beats:
            story_ticker_clips = self._create_story_ticker_clips(
                story_beats=dd_story_beats,
                video_size=(w, h),
            )
            logger.info(f"[StoryTicker] Built {len(story_ticker_clips)} ticker clips")

        # PiP book cover overlay (brand anchor — bottom-right corner, ≥30% duration)
        pip_clips = []
        if is_book_review and prefetched_images:
            pip_clip = self._create_pip_book_cover(
                book_cover_path=prefetched_images[0],
                video_size=(w, h),
                total_duration=duration,
                start_time=0.0
            )
            if pip_clip:
                pip_clips.append(pip_clip)

        # Layer order (bottom → top): scenes → pip → callouts → subtitles → title_overlay → source_overlay → digest_header → story_ticker
        # story_ticker at ~22% Y (below header), subtitles at 50% Y — no spatial overlap
        all_clips = scene_clips + pip_clips + callout_clips + all_subtitle_clips + title_overlay_clips + source_overlay_clips + digest_header_clips + story_ticker_clips
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
            # Loop music to cover video + end screen duration (no end screen for daily_update)
            end_screen_extra = 0 if content_type == "daily_update" else 4
            total_duration = duration + end_screen_extra
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
        
        # ── SFX Layer: Pacing-Break-Aware Pattern Interrupt Audio ──
        # Use natural speech pause timestamps (Whisper segment gaps) instead of
        # fixed 7-10s intervals — SFX hits land exactly where the speaker breathes.
        # Falls back to interrupt_plan if no pacing breaks detected.
        # Enabled for both book review and viral news.
        if is_book_review or is_viral_news:
            pacing_break_times = self._detect_pacing_breaks(all_segments)

            if pacing_break_times:
                sfx_events = [
                    {"time": t, "sfx_type": "whoosh" if idx % 2 == 0 else "thud"}
                    for idx, t in enumerate(pacing_break_times)
                ]
                logger.info(f"[SFX] Using {len(sfx_events)} pacing-break timestamps (speech-sync mode)")
            elif interrupt_plan:
                sfx_events = [
                    {"time": ev["time"], "sfx_type": ev.get("sfx_type", "whoosh")}
                    for ev in interrupt_plan
                    if ev.get("type") == "audio"
                ]
                logger.info(f"[SFX] No pacing breaks detected, falling back to {len(sfx_events)} fixed-interval events")
            else:
                sfx_events = []

            if sfx_events:
                sfx_clips = [final_audio]
                sfx_added = 0
                for event in sfx_events:
                    sfx_time = event["time"]
                    sfx_type = event.get("sfx_type", "whoosh")
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
                    logger.info(f"[PatternInterrupt] Added {sfx_added} pacing-sync SFX clips to audio mix")
        
        # Set audio on main video
        main_video = main_video.with_audio(final_audio.subclipped(0, duration))
        
        # Create end screen clip (4 seconds) — skip for daily_update (CTA scene has brand card)
        is_daily_digest_render = content_type == "daily_update"
        if is_daily_digest_render:
            logger.info("[DD] Skipping end screen — CTA scene already has AIInsider.png brand card")
            final_video = main_video
        else:
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
        direction: str = "push_in",
        scene_index: int = 0
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
        target_zoom = min(zoom or 1.1, 1.3)  # Increased cap for more aggressive Nano Banana zoom
        target_aspect = w / h  # 0.5625 for 9:16

        # Subtle alternating rotation per scene for dynamic visual energy (±0.3°)
        rotation_deg = 0.3 if scene_index % 2 == 0 else -0.3

        # Load image and detect aspect ratio
        try:
            pil_img = PILImage.open(str(image_path)).convert("RGB")
            # Apply subtle pre-rotation for dynamic feel
            pil_img = pil_img.rotate(rotation_deg, resample=PILImage.BILINEAR, expand=False)
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
            # Use rotated PIL array (already rotated above) instead of raw path
            img_clip = ImageClip(np.array(pil_img))
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
            # Smoothstep ease-in-out: feels dynamic, not robotic
            progress = max(0.0, min(1.0, t / max(duration, 0.1)))
            t_eased = progress * progress * (3.0 - 2.0 * progress)
            return zoom_start + (zoom_end - zoom_start) * t_eased
        
        img_clip = img_clip.resized(lambda t: zoom_effect(t))
        img_clip = img_clip.with_position("center")
        img_clip = img_clip.with_duration(duration)
        
        return img_clip

    def _detect_pacing_breaks(self, segments: list) -> list:
        """Detect natural speech pauses > 0.4s between Whisper segments.

        Returns timestamps (midpoint of each pause) suitable for SFX injection.
        Falls back to empty list if segments are unavailable or too few.
        """
        THRESHOLD = 0.4  # seconds — tunable
        if not segments or len(segments) < 2:
            return []
        sorted_segs = sorted(segments, key=lambda s: s.get("start", 0))
        breaks = []
        for idx in range(len(sorted_segs) - 1):
            current_end = sorted_segs[idx].get("end", 0)
            next_start = sorted_segs[idx + 1].get("start", 0)
            gap = next_start - current_end
            if gap > THRESHOLD:
                breaks.append(round(current_end + gap / 2.0, 2))
        logger.info(f"[PacingBreak] Detected {len(breaks)} breaks from {len(sorted_segs)} segments (threshold={THRESHOLD}s)")
        return breaks

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
        interrupt_times: List[float] = None,
        is_daily_digest: bool = False
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
        
        # Safe Zone Y positions:
        # - Daily Digest: Y=50% → centers captions in content zone, header overlay sits at Y=12%
        # - Book Review / Viral News: Y=75% → keeps captions in lower third, avoids focal points
        if is_daily_digest:
            y_position = int(h * 0.50)  # Center content zone (header at 12% leaves room above)
        else:
            y_position = int(h * 0.75)  # Lower third (book/news focal points are upper half)
        
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

    def _create_digest_header_overlay(
        self,
        duration: float,
        video_size: Tuple[int, int],
        article_title: str = "",
    ) -> List:
        """Create a persistent 2-row header bar for Daily Digest.

        Layout (Y positions within Shorts safe zone):
          Y  0%–10%: YouTube UI (channel name, follow button) — do not render
          Y 10%–24%: Header zone ← this method renders here
            Row 1 (Y=12%): ⚡ AI INSIDER · EXCLUSIVE BRIEFING — cyan, 28px
            Row 2 (Y=17%): Article catchy title — white bold, 34px, PROMINENT
          Y 24%–80%: Content zone (captions at 50%)
          Y 80%+:    YouTube subscribe button no-fly zone

        Args:
            duration:      Total video duration in seconds
            video_size:    (width, height) of the video frame
            article_title: The script's catchy_title to display as Row 2
        """
        from PIL import Image as PILImage
        import numpy as np

        w, h = video_size
        clips = []

        y_bar_top   = int(h * 0.10)   # bar starts at 10%
        bar_height  = 120              # taller bar for 2 rows
        y_brand_row = int(h * 0.12)   # Row 1: brand line at 12%
        y_title_row = int(h * 0.17)   # Row 2: article title at 17%

        # ── Semi-transparent obsidian background bar ──────────────────────
        try:
            bar_img   = PILImage.new('RGBA', (w, bar_height), (6, 8, 16, 230))  # 90% opacity
            bar_array = np.array(bar_img)
            bar_clip  = (
                ImageClip(bar_array)
                .with_position(('center', y_bar_top))
                .with_start(0)
                .with_duration(duration)
            )
            clips.append(bar_clip)

            # Cyan accent glow line at the bottom edge of the bar
            glow_img   = PILImage.new('RGBA', (w, 4), (0, 200, 255, 210))
            glow_array = np.array(glow_img)
            glow_clip  = (
                ImageClip(glow_array)
                .with_position(('center', y_bar_top + bar_height - 2))
                .with_start(0)
                .with_duration(duration)
            )
            clips.append(glow_clip)
        except Exception as e:
            logger.warning(f"[DigestHeader] Could not create background bar: {e}")

        # ── Row 1: Brand line — ⚡ AI INSIDER · EXCLUSIVE BRIEFING ────────
        try:
            brand_clip = (
                TextClip(
                    text="⚡ AI INSIDER  ·  EXCLUSIVE BRIEFING",
                    font_size=28,
                    color='#00C8FF',          # Cyan
                    font='/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                    stroke_color='black',
                    stroke_width=1,
                    text_align='center',
                )
                .with_position(('center', y_brand_row))
                .with_start(0)
                .with_duration(duration)
            )
            clips.append(brand_clip)
        except Exception as e:
            logger.warning(f"[DigestHeader] Brand line failed: {e}")

        # ── Row 2: Article title — WHITE BOLD, prominent ──────────────────
        if article_title:
            # Truncate to fit 9:16 frame width (≈42 chars at 34px)
            display_title = article_title.strip()
            if len(display_title) > 42:
                display_title = display_title[:40] + "…"
            display_title = display_title.upper()
            try:
                title_clip = (
                    TextClip(
                        text=display_title,
                        font_size=34,
                        color='#FFFFFF',          # White — stands out on dark bar
                        font='/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                        stroke_color='#000000',
                        stroke_width=2,
                        text_align='center',
                    )
                    .with_position(('center', y_title_row))
                    .with_start(0)
                    .with_duration(duration)
                )
                clips.append(title_clip)
                logger.info(f"[DigestHeader] Article title: '{display_title}'")
            except Exception as e:
                logger.warning(f"[DigestHeader] Title row failed: {e}")

        return clips


    def _create_story_ticker_clips(
        self,
        story_beats: list,
        video_size: Tuple[int, int],
    ) -> List:
        """Render a per-scene story title badge for Daily Digest videos.

        Layout (Y positions within safe zone):
          Y 10%-18%: AI INSIDER header bar      (persistent)
          Y 20%-27%: Story ticker badge ← here  (changes per scene)
          Y 30%-70%: Content zone               (captions at 50%)
          Y 80%+:    YouTube UI no-fly zone

        Story beats (story_index > 0): "STORY N  ·  COMPANY NAME" in cyan pill
        Hook / thread / impact / CTA scenes (story_index == 0): no badge shown

        Args:
            story_beats: List of dicts with company, story_index, start, duration
            video_size:  (width, height) of the video frame
        """
        from PIL import Image as PILImage
        import numpy as np

        w, h = video_size
        clips = []

        y_ticker = int(h * 0.22)   # 22% from top
        bar_height = 44
        y_bar = y_ticker - 10

        story_num = 0  # Track displayed story count

        for beat in story_beats:
            company      = beat.get("company", "").strip().upper()
            story_index  = beat.get("story_index", 0)
            beat_start   = beat.get("start", 0.0)
            beat_dur     = beat.get("duration", 5.0)
            scene_text   = beat.get("text", "")
            is_structural = beat.get("is_structural", story_index == 0)

            # Skip hook / connecting thread / insight / CTA scenes — no badge
            if is_structural:
                continue

            # Fallback: extract company from scene text if LLM left field empty
            if not company and scene_text:
                try:
                    from app.services.daily_digest_service import _extract_company
                    company = _extract_company(scene_text).upper()
                except Exception:
                    pass

            # If we still have no company name, skip silently (no "STORY N" fallback)
            if not company:
                continue

            story_num += 1
            # Label = company name only — clean, no redundant "STORY N ·" counter
            label = company
            if len(label) > 36:
                label = label[:34] + "…"

            # Dark navy pill background
            try:
                pill_img   = PILImage.new('RGBA', (w, bar_height), (6, 18, 32, 215))
                pill_array = np.array(pill_img)
                pill_clip  = (
                    ImageClip(pill_array)
                    .with_position(('center', y_bar))
                    .with_start(beat_start)
                    .with_duration(beat_dur)
                    .with_effects([vfx.FadeIn(0.3), vfx.FadeOut(0.2)])
                )
                clips.append(pill_clip)
            except Exception as e:
                logger.warning(f"[StoryTicker] Pill bg failed (story {story_num}): {e}")

            # Cyan label text — company name only
            try:
                label_clip = (
                    TextClip(
                        text=label,
                        font_size=28,
                        color='#00C8FF',
                        font='/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                        stroke_color='black',
                        stroke_width=1,
                        text_align='center',
                    )
                    .with_position(('center', y_ticker))
                    .with_start(beat_start)
                    .with_duration(beat_dur)
                    .with_effects([vfx.FadeIn(0.3), vfx.FadeOut(0.2)])
                )
                clips.append(label_clip)
                logger.debug(f"[StoryTicker] t={beat_start:.1f}s: '{label}'")
            except Exception as e:
                logger.warning(f"[StoryTicker] Label failed (story {story_num}): {e}")

        logger.info(f"[StoryTicker] Rendered {story_num} story badges")
        return clips

    def _create_news_source_overlay(

        self,
        source_name: str,
        category: str,
        duration: float,
        video_size: Tuple[int, int],
    ) -> List:
        """Create a news source attribution overlay for viral news videos.

        Shows "🔥 CATEGORY  •  Via SourceName" in a semi-transparent top bar
        for the first `duration` seconds (default 8s), then fades out.
        Styled in warm gold to match the kinetic subtitle color palette.

        Args:
            source_name: News outlet name (e.g., "Reuters", "Bloomberg")
            category:    News category (e.g., "technology", "business")
            duration:    How long to display (seconds) — caller caps at min(8, total)
            video_size:  (width, height) of the video frame
        """
        from PIL import Image as PILImage
        import numpy as np

        w, h = video_size
        clips = []

        # Position: 12% from top — below the YouTube Shorts channel bar safe zone
        y_bar = int(h * 0.12)

        # Semi-transparent background bar
        try:
            bar_height = 64
            bar_img = PILImage.new('RGBA', (w, bar_height), (0, 0, 0, 180))
            bar_array = np.array(bar_img)
            bar_clip = (
                ImageClip(bar_array)
                .with_position(('center', y_bar - 12))
                .with_start(0)
                .with_duration(duration)
                .with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.8)])
            )
            clips.append(bar_clip)
        except Exception as e:
            logger.warning(f"[SourceOverlay] Background bar failed: {e}")

        # Source attribution text: "🔥 TECHNOLOGY  •  Via Reuters"
        cat_label = f"🔥 {category.upper()}" if category else "🔥 BREAKING"
        label_text = f"{cat_label}  •  Via {source_name}"

        try:
            txt_clip = (
                TextClip(
                    text=label_text,
                    font_size=30,
                    color='#FFD700',    # warm gold — matches kinetic subtitle accent
                    font='/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                    stroke_color='black',
                    stroke_width=1,
                    text_align='center',
                )
                .with_position(('center', y_bar))
                .with_start(0)
                .with_duration(duration)
                .with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.8)])
            )
            clips.append(txt_clip)
        except Exception as e:
            logger.warning(f"[SourceOverlay] Text clip failed: {e}")

        return clips

    def _create_pip_book_cover(
        self,
        book_cover_path: Path,
        video_size: Tuple[int, int],
        total_duration: float,
        start_time: float = 0.0
    ) -> Optional[ImageClip]:
        """Create a Picture-in-Picture book cover overlay for brand recognition.

        Positions the cover in the bottom-right corner at 15% frame width.
        Enforces ≥30% visibility duration per the "60 Second Books" brand rule.
        Includes rounded corners and a subtle drop shadow.

        Returns ImageClip ready to composite, or None on failure.
        """
        from PIL import Image as PILImage, ImageDraw, ImageFilter
        import numpy as np

        w, h = video_size

        try:
            cover_img = PILImage.open(str(book_cover_path)).convert("RGBA")
        except Exception as e:
            logger.warning(f"[PiP] Cannot open book cover {book_cover_path}: {e}")
            return None

        # Scale to 15% of frame width, preserving aspect ratio
        pip_width = int(w * 0.15)
        cover_w, cover_h = cover_img.size
        pip_height = int(pip_width * cover_h / cover_w)

        cover_resized = cover_img.resize((pip_width, pip_height), PILImage.LANCZOS)

        # Rounded-corner mask
        corner_radius = max(4, int(pip_width * 0.08))
        mask = PILImage.new("L", (pip_width, pip_height), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([(0, 0), (pip_width - 1, pip_height - 1)], radius=corner_radius, fill=255)
        cover_resized.putalpha(mask)

        # Drop shadow layer
        shadow_offset = 4
        canvas_w = pip_width + shadow_offset * 2
        canvas_h = pip_height + shadow_offset * 2
        shadow_img = PILImage.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        shadow_layer = PILImage.new("RGBA", (pip_width, pip_height), (0, 0, 0, 180))
        shadow_layer.putalpha(mask)
        shadow_img.paste(shadow_layer, (shadow_offset, shadow_offset), shadow_layer)
        shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=4))

        # Composite shadow + cover
        canvas = PILImage.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        canvas.paste(shadow_img, (0, 0), shadow_img)
        canvas.paste(cover_resized, (shadow_offset, shadow_offset), cover_resized)

        pip_array = np.array(canvas)

        # Enforce ≥30% visibility (minimum 5s floor)
        min_duration = max(total_duration * 0.30, 5.0)
        overlay_duration = min(total_duration - start_time, min_duration)
        overlay_duration = max(overlay_duration, 0.5)

        # Bottom-right corner, 8% margin — stay above YouTube Shorts UI bar (bottom 12%)
        margin_x = int(w * 0.08)
        margin_y = int(h * 0.08)
        pip_x = w - canvas_w - margin_x
        safe_bottom = int(h * 0.88)
        pip_y = min(h - canvas_h - margin_y, safe_bottom - canvas_h)

        try:
            pip_clip = (
                ImageClip(pip_array)
                .with_position((pip_x, pip_y))
                .with_start(start_time)
                .with_duration(overlay_duration)
            )
            logger.info(
                f"[PiP] Book cover overlay: {pip_width}x{pip_height}px at ({pip_x},{pip_y}), "
                f"duration={overlay_duration:.1f}s ({overlay_duration/total_duration*100:.0f}% of video)"
            )
            return pip_clip
        except Exception as e:
            logger.warning(f"[PiP] Failed to create PiP clip: {e}")
            return None

    def _create_kinetic_callout(
        self,
        callout_text: str,
        video_size: Tuple[int, int],
        scene_start: float,
        accent: bool = False,
    ) -> Optional[ImageClip]:
        """Render a 2-3 word bold callout with a scale-punch animation.

        The callout appears at scene_start + 0.15s, scales from 0.65→1.0 over 0.25s
        (quadratic ease-out), holds, then fades out over 0.3s. Total duration: 1.5s.

        Args:
            callout_text: ALL-CAPS text (2-3 words max)
            video_size:   (width, height) of the output video
            scene_start:  Absolute start time of the scene in the final video
            accent:       True = gold (#FFD700), False = white — use gold for punch beats
        """
        if not callout_text or not callout_text.strip():
            return None
        callout_text = callout_text.strip()
        try:
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np

            w, h = video_size
            font_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
            font_size = 68
            canvas_h = 160  # Tall enough for two-line callout safety margin

            try:
                font = ImageFont.truetype(font_path, size=font_size)
            except OSError:
                font = ImageFont.load_default()

            color = "#FFD700" if accent else "#FFFFFF"  # gold vs white
            stroke_color = "#000000"
            stroke_w = 4

            # Render text on transparent RGBA canvas, centered
            canvas = Image.new("RGBA", (w, canvas_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(canvas)
            draw.text(
                (w // 2, canvas_h // 2),
                callout_text,
                font=font,
                fill=color,
                anchor="mm",
                stroke_width=stroke_w,
                stroke_fill=stroke_color,
            )

            base_clip = ImageClip(np.array(canvas), is_mask=False)

            # Scale-punch: quadratic ease-out from 0.65 → 1.0 over 0.25s
            PUNCH_DUR = 0.25
            FADE_DUR = 0.30
            TOTAL_DUR = 1.50

            def scale_func(t: float) -> float:
                if t < PUNCH_DUR:
                    progress = t / PUNCH_DUR
                    ease = 1.0 - (1.0 - progress) ** 2   # quadratic ease-out
                    return 0.65 + 0.35 * ease
                return 1.0

            callout_clip = (
                base_clip
                .resized(scale_func)
                .with_position(("center", int(h * 0.42)))
                .with_start(scene_start + 0.15)
                .with_duration(TOTAL_DUR)
                .with_effects([vfx.FadeOut(FADE_DUR)])
            )
            return callout_clip

        except Exception as e:
            logger.warning(f"[Callout] Failed to create kinetic callout for '{callout_text}': {e}")
            return None

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
