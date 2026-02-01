"""
Audio API endpoints.

Provides endpoints for:
- Generating audio from approved scripts
- Retrieving audio metadata
- Downloading audio files
- Listing audio files
- Deleting audio files
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.services.audio_service import AudioService
from app.schemas_audio import (
    AudioGenerateRequest,
    AudioResponse,
    AudioListResponse
)


router = APIRouter()


@router.post("/generate", response_model=AudioResponse, status_code=201)
async def generate_audio(
    request: AudioGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generate audio from an approved script using TTS.
    
    The script must be in 'approved' status before audio can be generated.
    """
    audio_service = AudioService(db)
    
    try:
        audio = await audio_service.generate_audio_from_script(
            script_id=request.script_id,
            voice=request.voice,
            tts_provider=request.tts_provider
        )
        
        # Add download URL to response
        response = AudioResponse.model_validate(audio)
        response.download_url = f"/api/audio/{audio.id}/download"
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {str(e)}")


@router.get("/{audio_id}", response_model=AudioResponse)
def get_audio(
    audio_id: int,
    db: Session = Depends(get_db)
):
    """Get audio metadata by ID."""
    audio_service = AudioService(db)
    audio = audio_service.get_audio_by_id(audio_id)
    
    if not audio:
        raise HTTPException(status_code=404, detail="Audio not found")
    
    # Add download URL to response
    response = AudioResponse.model_validate(audio)
    response.download_url = f"/api/audio/{audio.id}/download"
    
    return response


@router.get("/{audio_id}/download")
def download_audio(
    audio_id: int,
    db: Session = Depends(get_db)
):
    """
    Download or stream audio file.
    
    Returns the audio file as an MP3 with appropriate headers for download/streaming.
    """
    audio_service = AudioService(db)
    
    try:
        file_path = audio_service.get_audio_file_path(audio_id)
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Audio not found")
        
        # Return file with appropriate headers
        return FileResponse(
            path=file_path,
            media_type="audio/mpeg",
            filename=file_path.name,
            headers={
                "Content-Disposition": f"attachment; filename={file_path.name}"
            }
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audio file: {str(e)}")


@router.get("", response_model=AudioListResponse)
def list_audio(
    script_id: Optional[int] = Query(None, description="Filter by script ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    List audio files with optional filters.
    
    - **script_id**: Filter audio files for a specific script
    - **status**: Filter by status (pending, completed, failed)
    - **limit**: Maximum number of results (1-100)
    """
    audio_service = AudioService(db)
    audio_list = audio_service.list_audio(
        script_id=script_id,
        status=status,
        limit=limit
    )
    
    # Add download URLs to responses
    audio_responses = []
    for audio in audio_list:
        response = AudioResponse.model_validate(audio)
        response.download_url = f"/api/audio/{audio.id}/download"
        audio_responses.append(response)
    
    return AudioListResponse(
        audio_files=audio_responses,
        total=len(audio_responses)
    )


@router.delete("/{audio_id}")
def delete_audio(
    audio_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete audio file and database record.
    
    This permanently deletes both the file from disk and the database record.
    """
    audio_service = AudioService(db)
    
    success = audio_service.delete_audio(audio_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Audio not found")
    
    return {"success": True, "message": f"Audio {audio_id} deleted successfully"}
