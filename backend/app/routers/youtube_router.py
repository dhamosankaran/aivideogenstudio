"""
YouTube Transcript Analysis API endpoints.

Phase 2.5: Analyze YouTube videos, extract insights, create Shorts.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db
from app.services.youtube_transcript_service import YouTubeTranscriptService
from app.schemas.youtube_schemas import (
    YouTubeAnalyzeRequest,
    YouTubeSourceResponse,
    YouTubeSourceDetailResponse,
    InsightResponse,
    CreateShortRequest,
    CreateShortResponse,
    VideoSummaryResponse,
    ModeAGenerateRequest,
    ModeAGenerateResponse,
    ModeBGenerateRequest,
    ModeBGenerateResponse,
    TrimAndGenerateRequest,
    TrimAndGenerateResponse,
    # Phase 3 schemas
    VideoDownloadRequest,
    VideoDownloadResponse,
    VideoInfoResponse,
    TranscriptResponse,
    TranscriptSegment,
    EditorGenerateRequest,
    EditorGenerateResponse,
    MusicLibraryResponse,
    MusicTrackResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/youtube", tags=["youtube"])


@router.post("/analyze", response_model=YouTubeSourceResponse)
async def analyze_youtube_video(
    request: YouTubeAnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submit a YouTube video for transcript extraction and analysis.
    
    Flow:
    1. Extract transcript immediately
    2. Start insight analysis as background task
    3. Return source with status "analyzing"
    """
    service = YouTubeTranscriptService(db)
    
    try:
        # Extract transcript (synchronous - fast)
        source = await service.extract_transcript(request.youtube_url)
        
        # Fetch video metadata in background
        background_tasks.add_task(
            _fetch_metadata_task,
            db,
            source.id
        )
        
        # Start insight analysis in background
        background_tasks.add_task(
            _analyze_insights_task,
            db,
            source.id
        )
        
        return YouTubeSourceResponse(
            id=source.id,
            youtube_url=source.youtube_url,
            youtube_video_id=source.youtube_video_id,
            title=source.title,
            channel_name=source.channel_name,
            channel_url=source.channel_url,
            duration_seconds=source.duration_seconds,
            thumbnail_url=source.thumbnail_url,
            analysis_status="analyzing",
            insights_count=0,
            created_at=source.created_at,
            analyzed_at=source.analyzed_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to analyze YouTube video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/sources", response_model=List[YouTubeSourceResponse])
async def list_youtube_sources(
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """List all analyzed YouTube sources."""
    service = YouTubeTranscriptService(db)
    sources = service.get_all_sources(limit=limit)
    
    return [
        YouTubeSourceResponse(
            id=s.id,
            youtube_url=s.youtube_url,
            youtube_video_id=s.youtube_video_id,
            title=s.title,
            channel_name=s.channel_name,
            channel_url=s.channel_url,
            duration_seconds=s.duration_seconds,
            thumbnail_url=s.thumbnail_url,
            analysis_status=s.analysis_status,
            error_message=s.error_message,
            insights_count=len(s.insights) if s.insights else 0,
            created_at=s.created_at,
            analyzed_at=s.analyzed_at
        )
        for s in sources
    ]


@router.get("/sources/{source_id}", response_model=YouTubeSourceDetailResponse)
async def get_youtube_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """Get a YouTube source with its insights."""
    service = YouTubeTranscriptService(db)
    source = service.get_source(source_id)
    
    if not source:
        raise HTTPException(status_code=404, detail="YouTube source not found")
    
    # Convert insights to response format
    insights_response = []
    if source.insights:
        for idx, insight in enumerate(source.insights):
            insights_response.append(InsightResponse(
                index=idx,
                start_time=insight['start_time'],
                end_time=insight['end_time'],
                duration=insight['duration'],
                formatted_time=insight['formatted_time'],
                formatted_end_time=insight['formatted_end_time'],
                transcript_text=insight['transcript_text'],
                summary=insight['summary'],
                hook=insight['hook'],
                key_points=insight['key_points'],
                viral_score=insight['viral_score'],
                engagement_type=insight['engagement_type']
            ))
    
    return YouTubeSourceDetailResponse(
        id=source.id,
        youtube_url=source.youtube_url,
        youtube_video_id=source.youtube_video_id,
        title=source.title,
        channel_name=source.channel_name,
        channel_url=source.channel_url,
        duration_seconds=source.duration_seconds,
        thumbnail_url=source.thumbnail_url,
        analysis_status=source.analysis_status,
        error_message=source.error_message,
        insights=insights_response,
        created_at=source.created_at,
        analyzed_at=source.analyzed_at
    )


@router.post("/sources/{source_id}/insights/{insight_index}/create-short", response_model=CreateShortResponse)
async def create_short_from_insight(
    source_id: int,
    insight_index: int,
    request: CreateShortRequest,
    db: Session = Depends(get_db)
):
    """
    Create a Short from a selected insight.
    
    Mode A: Clip + Commentary (reaction/review style)
    Mode B: Original content inspired by the insight
    """
    service = YouTubeTranscriptService(db)
    
    try:
        article = await service.create_article_from_insight(
            youtube_source_id=source_id,
            insight_index=insight_index,
            mode=request.mode
        )
        
        mode_desc = "Clip + Commentary" if request.mode == "A" else "Original Content"
        
        return CreateShortResponse(
            article_id=article.id,
            mode=request.mode,
            message=f"Created {mode_desc} article from insight. Ready for script generation.",
            redirect_to="/scripts"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create short: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create short: {str(e)}")


@router.get("/sources/{source_id}/summary", response_model=VideoSummaryResponse)
async def get_video_summary(
    source_id: int,
    db: Session = Depends(get_db)
):
    """
    Get or generate a comprehensive summary of the entire YouTube video.
    
    Returns cached summary if available, otherwise generates new one.
    """
    service = YouTubeTranscriptService(db)
    source = service.get_source(source_id)
    
    if not source:
        raise HTTPException(status_code=404, detail="YouTube source not found")
    
    try:
        summary = await service.generate_video_summary(source_id)
        
        return VideoSummaryResponse(
            source_id=source.id,
            title=source.title,
            channel_name=source.channel_name,
            video_summary=summary,
            generated_at=source.summary_generated_at
        )
    except Exception as e:
        logger.error(f"Failed to generate summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@router.post("/sources/{source_id}/insights/{insight_index}/generate-mode-a", response_model=ModeAGenerateResponse)
async def generate_mode_a_video(
    source_id: int,
    insight_index: int,
    request: ModeAGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate Mode A (Clip + Commentary) video.
    
    Full pipeline:
    1. Download clip from YouTube
    2. Generate commentary script
    3. Auto-approve and start video generation
    
    Returns immediately, video renders in background.
    """
    from app.services.clip_extractor_service import ClipExtractorService
    from app.services.script_service import ScriptService
    from app.models import Script, Article
    
    service = YouTubeTranscriptService(db)
    source = service.get_source(source_id)
    
    if not source:
        raise HTTPException(status_code=404, detail="YouTube source not found")
    
    if not source.insights or insight_index >= len(source.insights):
        raise HTTPException(status_code=400, detail=f"Invalid insight index: {insight_index}")
    
    insight = source.insights[insight_index]
    
    try:
        # Step 1: Download clip
        clip_service = ClipExtractorService()
        clip_path, clip_metadata = await clip_service.download_clip(
            youtube_url=source.youtube_url,
            video_id=source.youtube_video_id,
            start_time=insight['start_time'],
            end_time=insight['end_time']
        )
        
        # Add watermark
        clip_path = clip_service.add_watermark(
            clip_path,
            watermark_text=f"REACTING TO: {source.channel_name or 'Video'}"
        )
        
        # Step 2: Create article for the pipeline
        article = await service.create_article_from_insight(
            youtube_source_id=source_id,
            insight_index=insight_index,
            mode="A"
        )
        
        # Store clip path
        article.clip_path = str(clip_path)
        db.commit()
        
        # Step 3: Generate commentary script
        script_service = ScriptService(db)
        commentary_data = await script_service.generate_commentary_script(
            insight=insight,
            source_title=source.title or "YouTube Video",
            source_channel=source.channel_name or "Unknown Channel",
            mode=request.commentary_style,
            clip_duration=clip_metadata.get('duration', 30.0)
        )
        
        # Create Script record
        script = Script(
            article_id=article.id,
            raw_script=f"[HOOK]\n{commentary_data['hook']}\n\n" + 
                       "\n".join([f"[SCENE {s['scene_number']}]\n{s['text']}\n" for s in commentary_data['scenes']]) +
                       f"\n[CTA]\n{commentary_data['call_to_action']}",
            formatted_script=commentary_data['formatted_script'],
            scenes=commentary_data['scenes'],
            word_count=commentary_data['word_count'],
            estimated_duration=commentary_data['estimated_duration'],
            catchy_title=commentary_data['title_suggestion'],
            has_hook=True,
            has_cta=True,
            status="generated",
            script_status="pending",
            content_type="youtube_reaction",
            video_description=commentary_data['source_attribution']
        )
        db.add(script)
        db.commit()
        db.refresh(script)
        
        video_id = None
        
        # Step 4: Auto-approve and queue video generation if requested
        if request.auto_approve:
            script.script_status = "approved"
            script.status = "approved"
            db.commit()
            
            # Start video generation in background
            background_tasks.add_task(
                _generate_mode_a_video_task,
                db,
                script.id,
                str(clip_path)
            )
            
            return ModeAGenerateResponse(
                status="generating",
                message="Clip downloaded, script generated, video rendering started.",
                article_id=article.id,
                script_id=script.id,
                clip_path=str(clip_path),
                redirect_to="/validation"
            )
        else:
            return ModeAGenerateResponse(
                status="pending_review",
                message="Clip downloaded and script generated. Ready for review.",
                article_id=article.id,
                script_id=script.id,
                clip_path=str(clip_path),
                redirect_to="/scripts"
            )
        
    except Exception as e:
        logger.error(f"Mode A generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Mode A generation failed: {str(e)}")


@router.post("/sources/{source_id}/insights/{insight_index}/generate-mode-b", response_model=ModeBGenerateResponse)
async def generate_mode_b_article(
    source_id: int,
    insight_index: int,
    request: ModeBGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generate Mode B (Original Content) article and script.
    
    Creates article from insight and generates script, then redirects
    to Script Review page for manual review.
    """
    from app.services.script_service import ScriptService
    
    service = YouTubeTranscriptService(db)
    source = service.get_source(source_id)
    
    if not source:
        raise HTTPException(status_code=404, detail="YouTube source not found")
    
    try:
        # Create article
        article = await service.create_article_from_insight(
            youtube_source_id=source_id,
            insight_index=insight_index,
            mode="B"
        )
        
        # Update content type
        article.suggested_content_type = request.content_type
        db.commit()
        
        # Generate script for review
        script_service = ScriptService(db)
        script = await script_service.generate_script(
            article=article,
            style="engaging",
            target_duration=50
        )
        
        return ModeBGenerateResponse(
            status="ready_for_review",
            message="Article and script created. Ready for review.",
            article_id=article.id,
            script_id=script.id,
            redirect_to="/scripts"
        )
        
    except Exception as e:
        logger.error(f"Mode B generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Mode B generation failed: {str(e)}")




@router.post("/sources/{source_id}/reanalyze", response_model=YouTubeSourceResponse)
async def reanalyze_source(
    source_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger re-analysis of a YouTube source."""
    service = YouTubeTranscriptService(db)
    source = service.get_source(source_id)
    
    if not source:
        raise HTTPException(status_code=404, detail="YouTube source not found")
    
    # Start insight analysis in background
    background_tasks.add_task(
        _analyze_insights_task,
        db,
        source.id
    )
    
    return YouTubeSourceResponse(
        id=source.id,
        youtube_url=source.youtube_url,
        youtube_video_id=source.youtube_video_id,
        title=source.title,
        channel_name=source.channel_name,
        channel_url=source.channel_url,
        duration_seconds=source.duration_seconds,
        thumbnail_url=source.thumbnail_url,
        analysis_status="analyzing",
        insights_count=len(source.insights) if source.insights else 0,
        created_at=source.created_at,
        analyzed_at=source.analyzed_at
    )


# ═══════════════════════════════════════════════════════════════
# Phase 3: Universal Download & Editor Endpoints
# ═══════════════════════════════════════════════════════════════


@router.post("/info", response_model=VideoInfoResponse)
async def get_video_info(request: VideoDownloadRequest):
    """
    Get video metadata without downloading.
    Supports YouTube, X/Twitter, and LinkedIn URLs.
    """
    from app.services.video_downloader_service import VideoDownloaderService

    dl = VideoDownloaderService()
    info = await dl.get_video_info(request.url)
    return VideoInfoResponse(**info)


@router.post("/download", response_model=VideoDownloadResponse)
async def download_video(
    request: VideoDownloadRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Download a video from YouTube, X/Twitter, or LinkedIn.
    Creates a YouTubeSource record and stores the downloaded file.
    """
    from app.services.video_downloader_service import VideoDownloaderService

    dl = VideoDownloaderService()
    platform = dl.detect_platform(request.url)
    video_id = dl.extract_video_id(request.url, platform)

    if not video_id:
        raise HTTPException(status_code=400, detail="Could not extract video ID from URL")

    # Check for existing source
    existing = (
        db.query(YouTubeSource)
        .filter(YouTubeSource.youtube_video_id == video_id)
        .first()
    )
    if existing and existing.downloaded_path:
        from pathlib import Path
        if Path(existing.downloaded_path).exists():
            return VideoDownloadResponse(
                status="cached",
                message="Video already downloaded",
                platform=platform,
                source_id=existing.id,
                file_path=existing.downloaded_path,
                duration=existing.duration_seconds,
                has_audio=not request.strip_audio,
            )

    try:
        # Download the video
        file_path, metadata = await dl.download_video(
            url=request.url,
            strip_audio=request.strip_audio,
        )

        # Get additional info for the source record
        info = await dl.get_video_info(request.url)

        # Create or update YouTubeSource
        from app.models import YouTubeSource as YTModel
        if existing:
            source = existing
            source.downloaded_path = str(file_path)
            source.platform = platform
        else:
            source = YTModel(
                youtube_url=request.url,
                youtube_video_id=video_id,
                platform=platform,
                title=info.get("title"),
                channel_name=info.get("channel_name"),
                channel_url=info.get("channel_url"),
                duration_seconds=info.get("duration") or metadata.get("duration"),
                thumbnail_url=info.get("thumbnail_url"),
                downloaded_path=str(file_path),
                analysis_status="downloaded",
            )
            db.add(source)

        db.commit()
        db.refresh(source)

        # Start transcript extraction in background
        background_tasks.add_task(_extract_transcript_task, db, source.id)

        return VideoDownloadResponse(
            status="downloaded",
            message=f"Video downloaded from {platform}",
            platform=platform,
            source_id=source.id,
            file_path=str(file_path),
            duration=metadata.get("duration"),
            file_size=metadata.get("file_size"),
            has_audio=metadata.get("has_audio", True) and not request.strip_audio,
            metadata=metadata,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/sources/{source_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(
    source_id: int,
    db: Session = Depends(get_db),
):
    """
    Get the transcript for a YouTube source.
    Returns structured transcript segments with timestamps.
    """
    service = YouTubeTranscriptService(db)
    source = service.get_source(source_id)

    if not source:
        raise HTTPException(status_code=404, detail="YouTube source not found")

    # Build segments from transcript data
    segments = []
    full_text = ""

    if source.transcript_segments:
        segments = [
            TranscriptSegment(text=s["text"], start=s["start"], end=s["end"])
            for s in source.transcript_segments
        ]
        full_text = " ".join(s["text"] for s in source.transcript_segments)
    elif source.transcript:
        for entry in source.transcript:
            text = entry.get("text", "")
            start = entry.get("start", 0)
            duration = entry.get("duration", 3.0)
            segments.append(
                TranscriptSegment(text=text, start=start, end=start + duration)
            )
            full_text += text + " "
        full_text = full_text.strip()

    return TranscriptResponse(
        source_id=source.id,
        title=source.title,
        transcript_source=source.transcript_source or "youtube_captions",
        segments=segments,
        full_text=full_text,
        duration=source.duration_seconds,
    )


@router.get("/music-library", response_model=MusicLibraryResponse)
async def get_music_library():
    """
    Get available background music tracks.
    """
    from app.services.background_music_service import BackgroundMusicService
    from app.content_types import CONTENT_TYPES, DEFAULT_FALLBACK_MUSIC

    music_service = BackgroundMusicService()
    tracks_list = []

    for ct_key, ct_config in CONTENT_TYPES.items():
        music_file = ct_config.get("music", DEFAULT_FALLBACK_MUSIC)
        music_path = music_service.MUSIC_DIR / music_file
        if music_path.exists():
            # Avoid duplicate entries
            if not any(t.filename == music_file for t in tracks_list):
                tracks_list.append(
                    MusicTrackResponse(
                        filename=music_file,
                        content_type=ct_key,
                        label=ct_config.get("label", ct_key),
                        size_kb=music_path.stat().st_size / 1024,
                    )
                )

    return MusicLibraryResponse(
        tracks=tracks_list,
        default_track=DEFAULT_FALLBACK_MUSIC,
    )


# ═══════════════════════════════════════════════════════════════
# Phase 3.3: Script Generation (transcript-only, no download needed)
# ═══════════════════════════════════════════════════════════════

@router.post(
    "/sources/{source_id}/generate-script",
    response_model=EditorGenerateResponse,
)
async def generate_script_from_transcript(
    source_id: int,
    request: EditorGenerateRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a script preview from the video's transcript and summary.
    Does NOT require the video to be downloaded — uses transcript data only.
    Returns the script for user review before actual video generation.
    """
    from app.services.script_service import ScriptService
    from app.models import Script, Article

    service = YouTubeTranscriptService(db)
    source = service.get_source(source_id)

    if not source:
        raise HTTPException(status_code=404, detail="YouTube source not found")

    try:
        # Gather transcript text
        transcript_text = ""
        if source.transcript_segments:
            # Use trimmed portion of transcript if trim range specified
            if request.trim_start is not None and request.trim_end is not None:
                transcript_text = " ".join(
                    s["text"] for s in source.transcript_segments
                    if s.get("start", 0) >= request.trim_start
                    and s.get("end", s.get("start", 0)) <= request.trim_end
                )
            if not transcript_text:
                transcript_text = " ".join(
                    s["text"] for s in source.transcript_segments
                )
        elif source.transcript:
            transcript_text = " ".join(
                e.get("text", "") for e in source.transcript
            )

        if not transcript_text and not source.video_summary:
            raise HTTPException(
                status_code=400,
                detail="No transcript or summary available. Wait for analysis to complete."
            )

        # Reuse existing article or create new one (articles.url must be unique)
        import time
        article = (
            db.query(Article)
            .filter(Article.youtube_source_id == source.id, Article.creation_mode == "editor")
            .order_by(Article.id.desc())
            .first()
        )
        if article:
            # Update existing article
            article.content = transcript_text[:2000] if transcript_text else source.video_summary or ""
            article.summary = source.video_summary or transcript_text[:500]
            article.suggested_content_type = request.content_type
            article.is_selected = True
        else:
            # Create new article with unique URL
            unique_url = f"{source.youtube_url}#editor-{int(time.time())}"
            article = Article(
                youtube_source_id=source.id,
                title=source.title or "Video Script",
                url=unique_url,
                content=transcript_text[:2000] if transcript_text else source.video_summary or "",
                summary=source.video_summary or transcript_text[:500],
                creation_mode="editor",
                is_selected=True,
                suggested_content_type=request.content_type,
            )
            db.add(article)
        db.commit()
        db.refresh(article)

        # Calculate clip duration
        clip_duration = (
            (request.trim_end - request.trim_start)
            if request.trim_start is not None and request.trim_end is not None
            else source.duration_seconds or 60
        )

        # Build insight data for the script generator
        insight_data = {
            "summary": source.video_summary or transcript_text[:300],
            "key_points": [],
            "hook": f"This from {source.channel_name or 'this video'} is incredible!",
            "transcript_text": transcript_text[:1500],
            "start_time": request.trim_start or 0,
            "end_time": request.trim_end or (source.duration_seconds or 60),
        }

        # Generate the script using LLM
        script_service = ScriptService(db)
        commentary_data = await script_service.generate_commentary_script(
            insight=insight_data,
            source_title=source.title or "Video",
            source_channel=source.channel_name or "Unknown",
            mode=request.commentary_style,
            clip_duration=clip_duration,
        )

        # Save as pending script
        script = Script(
            article_id=article.id,
            raw_script=commentary_data.get("raw_script", ""),
            formatted_script=commentary_data.get("formatted_script", ""),
            scenes=commentary_data.get("scenes", []),
            catchy_title=commentary_data.get("title_suggestion", ""),
            estimated_duration=commentary_data.get("estimated_duration", clip_duration),
            script_status="pending",
            status="pending",
            content_type=request.content_type,
            video_description=commentary_data.get("source_attribution", ""),
        )
        db.add(script)
        db.commit()
        db.refresh(script)

        # Will set clip_path during approve-and-render
        db.commit()

        return EditorGenerateResponse(
            status="pending_review",
            message="Script generated! Review and approve to start video rendering.",
            article_id=article.id,
            script_id=script.id,
            clip_duration=clip_duration,
            script_preview=commentary_data.get("formatted_script", script.raw_script),
            catchy_title=commentary_data.get("title_suggestion", ""),
            scenes=commentary_data.get("scenes", []),
            redirect_to="/scripts",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Script generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Script generation failed: {str(e)}"
        )


@router.post(
    "/sources/{source_id}/editor/generate",
    response_model=EditorGenerateResponse,
)
async def editor_generate_video(
    source_id: int,
    request: EditorGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Full editor-based video generation.

    Pipeline:
    1. Use already-downloaded video from source
    2. Optionally trim to start/end
    3. Strip original audio
    4. Generate script from transcript/summary
    5. Generate TTS, overlay background music
    6. Burn captions
    7. Render final video
    """
    from app.services.video_editor_service import VideoEditorService
    from app.services.script_service import ScriptService
    from app.models import Script, Article
    from pathlib import Path

    service = YouTubeTranscriptService(db)
    source = service.get_source(source_id)

    if not source:
        raise HTTPException(status_code=404, detail="YouTube source not found")

    if not source.downloaded_path or not Path(source.downloaded_path).exists():
        raise HTTPException(
            status_code=400,
            detail="Video not downloaded yet. Use /download first.",
        )

    try:
        editor = VideoEditorService()
        working_path = Path(source.downloaded_path)

        # Step 1: Trim if requested
        if request.trim_start is not None and request.trim_end is not None:
            if request.trim_start >= request.trim_end:
                raise HTTPException(
                    status_code=400, detail="trim_start must be < trim_end"
                )
            working_path = editor.trim_clip(
                working_path, request.trim_start, request.trim_end
            )

        # Step 2: Strip audio if requested
        if request.strip_audio:
            working_path = editor.strip_audio(working_path)

        # Step 3: Overlay background music if specified
        if request.music_track:
            from app.services.background_music_service import BackgroundMusicService
            music_service = BackgroundMusicService()
            music_path = music_service.MUSIC_DIR / request.music_track
            if music_path.exists():
                working_path = editor.overlay_music(
                    working_path, music_path, request.music_volume
                )

        # Step 4: Create article (use summary or transcript for content)
        transcript_text = ""
        if source.transcript_segments:
            transcript_text = " ".join(
                s["text"] for s in source.transcript_segments
            )
        elif source.transcript:
            transcript_text = " ".join(
                e.get("text", "") for e in source.transcript
            )

        article = Article(
            youtube_source_id=source.id,
            title=source.title or "Edited Video",
            url=source.youtube_url,
            content=transcript_text[:2000] if transcript_text else source.video_summary or "",
            summary=source.video_summary or transcript_text[:500],
            creation_mode="editor",
            clip_path=str(working_path),
            is_selected=True,
            suggested_content_type=request.content_type,
        )
        db.add(article)
        db.commit()
        db.refresh(article)

        # Step 5: Generate script from transcript/summary
        script_service = ScriptService(db)

        # Build insight-like dict for script generation
        insight_data = {
            "summary": source.video_summary or transcript_text[:300],
            "key_points": [],
            "hook": f"This from {source.channel_name or 'this video'} is incredible!",
            "transcript_text": transcript_text[:1500],
            "start_time": request.trim_start or 0,
            "end_time": request.trim_end or (source.duration_seconds or 60),
        }

        clip_duration = (
            (request.trim_end - request.trim_start)
            if request.trim_start is not None and request.trim_end is not None
            else source.duration_seconds or 60
        )

        commentary_data = await script_service.generate_commentary_script(
            insight=insight_data,
            source_title=source.title or "Video",
            source_channel=source.channel_name or "Unknown",
            mode=request.commentary_style,
            clip_duration=clip_duration,
        )

        script = Script(
            article_id=article.id,
            raw_script=(
                f"[HOOK]\n{commentary_data['hook']}\n\n"
                + "\n".join(
                    f"[SCENE {s['scene_number']}]\n{s['text']}\n"
                    for s in commentary_data["scenes"]
                )
                + f"\n[CTA]\n{commentary_data['call_to_action']}"
            ),
            formatted_script=commentary_data["formatted_script"],
            scenes=commentary_data["scenes"],
            word_count=commentary_data["word_count"],
            estimated_duration=commentary_data["estimated_duration"],
            catchy_title=commentary_data["title_suggestion"],
            has_hook=True,
            has_cta=True,
            status="generated",
            script_status="pending",
            content_type=request.content_type,
            video_description=commentary_data.get("source_attribution", ""),
        )
        db.add(script)
        db.commit()
        db.refresh(script)

        # Step 6: Auto-approve and queue video generation
        if request.auto_approve:
            script.script_status = "approved"
            script.status = "approved"
            db.commit()

            background_tasks.add_task(
                _generate_mode_a_video_task, db, script.id, str(working_path)
            )

            return EditorGenerateResponse(
                status="generating",
                message="Video edited, script generated. Rendering started.",
                article_id=article.id,
                script_id=script.id,
                clip_path=str(working_path),
                clip_duration=clip_duration,
                redirect_to="/validation",
            )
        else:
            return EditorGenerateResponse(
                status="pending_review",
                message="Script generated. Review below and click Generate Video when ready.",
                article_id=article.id,
                script_id=script.id,
                clip_path=str(working_path),
                clip_duration=clip_duration,
                script_preview=commentary_data.get("formatted_script", script.raw_script),
                catchy_title=commentary_data.get("title_suggestion", ""),
                scenes=commentary_data.get("scenes", []),
                redirect_to="/scripts",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Editor generate failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Editor generate failed: {str(e)}"
        )


@router.post("/scripts/{script_id}/approve-and-render")
async def approve_and_render(
    script_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    # Editor settings passed from frontend
    trim_start: float = 0,
    trim_end: float = 60,
    strip_audio: bool = True,
    music_track: str = None,
    music_volume: float = 0.12,
):
    """
    Approve a pending script and start full video pipeline:
    1. Download the source video
    2. Apply trim/strip-audio/music edits
    3. Approve the script
    4. Start video rendering in background
    """
    from app.models import Script, Article, YouTubeSource
    from app.services.video_downloader_service import VideoDownloaderService
    from app.services.video_editor_service import VideoEditorService
    from pathlib import Path

    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    if script.script_status == "approved":
        return {"status": "already_approved", "message": "Script already approved"}

    article = db.query(Article).filter(Article.id == script.article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    source = db.query(YouTubeSource).filter(
        YouTubeSource.id == article.youtube_source_id
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="YouTube source not found")

    try:
        # Step 1: Download video if not already downloaded
        if not source.downloaded_path or not Path(source.downloaded_path).exists():
            logger.info(f"Downloading video for source {source.id}...")
            downloader = VideoDownloaderService()
            download_path, download_meta = downloader.download_video(source.youtube_url)
            source.downloaded_path = str(download_path)
            db.commit()

        working_path = Path(source.downloaded_path)

        # Step 2: Trim
        editor = VideoEditorService()
        if trim_start > 0 or trim_end < (source.duration_seconds or 9999):
            working_path = editor.trim_clip(working_path, trim_start, trim_end)

        # Step 3: Strip audio
        if strip_audio:
            working_path = editor.strip_audio(working_path)

        # Step 4: Overlay music
        if music_track:
            from app.services.background_music_service import BackgroundMusicService
            music_service = BackgroundMusicService()
            music_path = music_service.MUSIC_DIR / music_track
            if music_path.exists():
                working_path = editor.overlay_music(
                    working_path, music_path, music_volume
                )

        # Step 5: Update article with clip path
        article.clip_path = str(working_path)
        db.commit()

        # Step 6: Approve the script
        script.script_status = "approved"
        script.status = "approved"
        db.commit()

        # Step 7: Queue video generation
        background_tasks.add_task(
            _generate_mode_a_video_task, db, script.id, str(working_path)
        )

        return {
            "status": "generating",
            "message": "Script approved! Video downloading and rendering started.",
            "script_id": script.id,
            "article_id": script.article_id,
            "redirect_to": "/validation",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approve & render failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Approve & render failed: {str(e)}"
        )


# ═══════════════════════════════════════════════════════════════
# Legacy Phase 2.5 Trim Endpoint (preserved for backward compatibility)
# ═══════════════════════════════════════════════════════════════

@router.post("/sources/{source_id}/insights/{insight_index}/trim-and-generate", response_model=TrimAndGenerateResponse)
async def trim_and_generate_video(
    source_id: int,
    insight_index: int,
    request: TrimAndGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trim a clip from the YouTube video and generate a new video.
    
    Pipeline:
    1. Download the full insight segment
    2. Trim to user-specified start/end times
    3. Generate commentary script
    4. Queue TTS + video rendering in background
    """
    from app.services.clip_extractor_service import ClipExtractorService
    from app.services.script_service import ScriptService
    from app.models import Script, Article
    
    service = YouTubeTranscriptService(db)
    source = service.get_source(source_id)
    
    if not source:
        raise HTTPException(status_code=404, detail="YouTube source not found")
    
    if not source.insights or insight_index >= len(source.insights):
        raise HTTPException(status_code=400, detail=f"Invalid insight index: {insight_index}")
    
    insight = source.insights[insight_index]
    
    # Validate trim times
    if request.start_time >= request.end_time:
        raise HTTPException(status_code=400, detail="start_time must be less than end_time")
    
    trim_duration = request.end_time - request.start_time
    if trim_duration < 3:
        raise HTTPException(status_code=400, detail="Trimmed clip must be at least 3 seconds")
    if trim_duration > 120:
        raise HTTPException(status_code=400, detail="Trimmed clip must be under 120 seconds")
    
    try:
        # Step 1: Download clip using the user-specified trim times
        clip_service = ClipExtractorService()
        clip_path, clip_metadata = await clip_service.download_clip(
            youtube_url=source.youtube_url,
            video_id=source.youtube_video_id,
            start_time=request.start_time,
            end_time=request.end_time
        )
        
        actual_duration = clip_metadata.get('duration', trim_duration)
        
        # Step 2: Create article for the pipeline
        article = await service.create_article_from_insight(
            youtube_source_id=source_id,
            insight_index=insight_index,
            mode="A"
        )
        article.clip_path = str(clip_path)
        db.commit()
        
        # Step 3: Generate commentary script
        script_service = ScriptService(db)
        commentary_data = await script_service.generate_commentary_script(
            insight=insight,
            source_title=source.title or "YouTube Video",
            source_channel=source.channel_name or "Unknown Channel",
            mode=request.commentary_style,
            clip_duration=actual_duration
        )
        
        # Create Script record
        script = Script(
            article_id=article.id,
            raw_script=f"[HOOK]\n{commentary_data['hook']}\n\n" + 
                       "\n".join([f"[SCENE {s['scene_number']}]\n{s['text']}\n" for s in commentary_data['scenes']]) +
                       f"\n[CTA]\n{commentary_data['call_to_action']}",
            formatted_script=commentary_data['formatted_script'],
            scenes=commentary_data['scenes'],
            word_count=commentary_data['word_count'],
            estimated_duration=commentary_data['estimated_duration'],
            catchy_title=commentary_data['title_suggestion'],
            has_hook=True,
            has_cta=True,
            status="generated",
            script_status="pending",
            content_type="youtube_trim",
            video_description=commentary_data['source_attribution']
        )
        db.add(script)
        db.commit()
        db.refresh(script)
        
        # Step 4: Auto-approve and queue video generation
        if request.auto_approve:
            script.script_status = "approved"
            script.status = "approved"
            db.commit()
            
            background_tasks.add_task(
                _generate_mode_a_video_task,
                db,
                script.id,
                str(clip_path)
            )
            
            return TrimAndGenerateResponse(
                status="generating",
                message=f"Clip trimmed ({actual_duration:.1f}s), script generated. Video rendering started.",
                article_id=article.id,
                script_id=script.id,
                clip_path=str(clip_path),
                clip_duration=actual_duration,
                redirect_to="/validation"
            )
        else:
            return TrimAndGenerateResponse(
                status="pending_review",
                message=f"Clip trimmed ({actual_duration:.1f}s) and script generated. Ready for review.",
                article_id=article.id,
                script_id=script.id,
                clip_path=str(clip_path),
                clip_duration=actual_duration,
                redirect_to="/scripts"
            )
        
    except Exception as e:
        logger.error(f"Trim and generate failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Trim and generate failed: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# Background Tasks
# ═══════════════════════════════════════════════════════════════

async def _extract_transcript_task(db_session, source_id: int):
    """Background task to extract transcript after download."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        service = YouTubeTranscriptService(db)
        source = service.get_source(source_id)
        if source and not source.transcript:
            try:
                await service.extract_transcript(source.youtube_url)
                source.transcript_source = "youtube_captions"
                source.analysis_status = "transcript_ready"
                db.commit()
            except Exception:
                # YouTube captions not available; will need Whisper fallback later
                source.transcript_source = None
                source.analysis_status = "downloaded"
                db.commit()
    except Exception as e:
        logger.error(f"Transcript extraction failed for source {source_id}: {str(e)}")
    finally:
        db.close()


async def _fetch_metadata_task(db: Session, source_id: int):
    """Background task to fetch video metadata."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        service = YouTubeTranscriptService(db)
        await service.update_video_metadata(source_id)
    except Exception as e:
        logger.error(f"Failed to fetch metadata for source {source_id}: {str(e)}")
    finally:
        db.close()


async def _analyze_insights_task(db: Session, source_id: int):
    """Background task for insight analysis."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        service = YouTubeTranscriptService(db)
        await service.analyze_for_insights(source_id)
    except Exception as e:
        logger.error(f"Failed to analyze insights for source {source_id}: {str(e)}")
    finally:
        db.close()


async def _generate_mode_a_video_task(db: Session, script_id: int, clip_path: str):
    """
    Background task for Mode A video generation.
    
    Generates audio, then renders video with clip integration.
    """
    from app.database import SessionLocal
    from app.services.audio_service import AudioService
    from app.services.enhanced_video_service import EnhancedVideoCompositionService
    from app.models import Script, Video
    
    db = SessionLocal()
    try:
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            logger.error(f"Script {script_id} not found for Mode A video generation")
            return
        
        # Step 1: Generate audio for commentary
        logger.info(f"Mode A: Generating audio for script {script_id}")
        audio_service = AudioService(db)
        audio = await audio_service.generate_audio_from_script(
            script_id=script_id,
            tts_provider="google"
        )
        
        # Step 2: Create video task
        logger.info(f"Mode A: Creating video task for script {script_id}")
        video_service = EnhancedVideoCompositionService(db)
        video = video_service.create_video_task(
            script_id=script_id,
            audio_id=audio.id,
            background_style="scenes"
        )
        
        # Store clip path in video metadata for later use
        if video.render_settings:
            video.render_settings['clip_path'] = clip_path
            video.render_settings['mode'] = 'A'
        else:
            video.render_settings = {'clip_path': clip_path, 'mode': 'A'}
        
        db.commit()
        db.refresh(video)
        
        # Step 3: Render video
        logger.info(f"Mode A: Rendering video {video.id}")
        video_service.process_video(video.id)
        
        logger.info(f"Mode A: Video generation complete for script {script_id}")
        
    except Exception as e:
        logger.error(f"Mode A video generation failed for script {script_id}: {str(e)}")
    finally:
        db.close()

