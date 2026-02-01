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
    ModeBGenerateResponse
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


# Background Tasks

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

