"""
Audio service for TTS generation and management.

Handles:
- Generating audio from approved scripts using TTS providers
- Saving audio files to disk
- Extracting audio metadata (duration, file size)
- Cost tracking
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from sqlalchemy.orm import Session
from pydub import AudioSegment
from io import BytesIO

from app.models import Audio, Script
from app.services.provider_factory import ProviderFactory
from app.services.base_provider import TTSProvider
from app.config import settings



class AudioService:
    """Service for audio generation and management."""
    
    # Audio storage directory (relative to backend/)
    AUDIO_DIR = Path("data/audio")
    
    def __init__(self, db: Session):
        """Initialize audio service."""
        self.db = db
        
        # Ensure audio directory exists
        self.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    async def generate_audio_from_script(
        self,
        script_id: int,
        voice: Optional[str] = None,
        tts_provider: str = "openai"
    ) -> Audio:
        """
        Generate audio from an approved script.
        
        Args:
            script_id: ID of the script to generate audio from
            voice: Optional voice ID (uses provider default if not specified)
            tts_provider_name: TTS provider to use (default: openai)
            
        Returns:
            Audio object with metadata
            
        Raises:
            ValueError: If script not found or not approved
            Exception: If TTS generation fails
        """
        # Get script from database
        script = self.db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise ValueError(f"Script with ID {script_id} not found")
        
        # Validate script is approved
        if script.status != "approved":
            raise ValueError(
                f"Script must be approved before generating audio. "
                f"Current status: {script.status}"
            )
        
        # Create Audio record in database (pending status)
        audio = Audio(
            script_id=script_id,
            file_path="",  # Will be set after generation
            tts_provider=tts_provider,
            voice=voice or "alloy",
            status="pending"
        )
        self.db.add(audio)
        self.db.commit()
        self.db.refresh(audio)
        
        try:
            # Get TTS provider using factory
            tts_provider_enum = TTSProvider(tts_provider)
            tts_provider = ProviderFactory.create_tts_provider(
                provider=tts_provider_enum,
                voice=voice
            )

            
            # Store model info
            audio.tts_model = getattr(tts_provider, "model", None)
            
            # Use formatted_script for TTS (cleaned of section markers)
            text_to_synthesize = script.formatted_script or script.raw_script
            
            # Generate audio bytes
            audio_bytes = await tts_provider.synthesize_speech(
                text=text_to_synthesize,
                output_format="mp3"
            )
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audio_{audio.id}_{timestamp}.mp3"
            file_path = self.AUDIO_DIR / filename
            
            # Save audio file to disk
            with open(file_path, "wb") as f:
                f.write(audio_bytes)
            
            # Extract audio metadata using pydub
            try:
                audio_segment = AudioSegment.from_file(BytesIO(audio_bytes), format="mp3")
                duration_seconds = len(audio_segment) / 1000.0  # pydub uses milliseconds
            except Exception as e:
                print(f"Warning: Could not extract duration from audio file: {e}")
                # Fallback to estimation based on word count
                duration_seconds = self.estimate_audio_duration(
                    self.db.query(Script.word_count).filter(Script.id == script_id).scalar() or 0
                )
            
            file_size = len(audio_bytes)
            
            # Calculate cost
            char_count = len(text_to_synthesize)
            generation_cost = tts_provider.estimate_cost(char_count)
            
            # Update audio record
            audio.file_path = str(file_path)
            audio.duration = duration_seconds
            audio.file_size = file_size
            audio.generation_cost = generation_cost
            audio.status = "completed"
            audio.completed_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(audio)
            
            return audio
            
        except Exception as e:
            # Update audio record with error
            audio.status = "failed"
            audio.error_message = str(e)
            self.db.commit()
            raise Exception(f"Failed to generate audio: {str(e)}")
    
    def get_audio_by_id(self, audio_id: int) -> Optional[Audio]:
        """
        Get audio by ID.
        
        Args:
            audio_id: Audio ID
            
        Returns:
            Audio object or None if not found
        """
        return self.db.query(Audio).filter(Audio.id == audio_id).first()
    
    def list_audio(
        self,
        script_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Audio]:
        """
        List audio files with optional filters.
        
        Args:
            script_id: Filter by script ID
            status: Filter by status (pending, completed, failed)
            limit: Maximum number of results
            
        Returns:
            List of Audio objects
        """
        query = self.db.query(Audio)
        
        if script_id:
            query = query.filter(Audio.script_id == script_id)
        
        if status:
            query = query.filter(Audio.status == status)
        
        return query.order_by(Audio.created_at.desc()).limit(limit).all()
    
    def get_audio_file_path(self, audio_id: int) -> Optional[Path]:
        """
        Get absolute file path for an audio file.
        
        Args:
            audio_id: Audio ID
            
        Returns:
            Absolute Path object or None if not found
            
        Raises:
            FileNotFoundError: If audio exists in DB but file is missing
        """
        audio = self.get_audio_by_id(audio_id)
        if not audio:
            return None
        
        # Convert relative path to absolute
        abs_path = Path.cwd() / audio.file_path
        
        if not abs_path.exists():
            raise FileNotFoundError(
                f"Audio file not found at: {abs_path}. "
                f"Database path: {audio.file_path}"
            )
        
        return abs_path
    
    def delete_audio(self, audio_id: int) -> bool:
        """
        Delete audio record and file.
        
        Args:
            audio_id: Audio ID
            
        Returns:
            True if deleted, False if not found
        """
        audio = self.get_audio_by_id(audio_id)
        if not audio:
            return False
        
        # Delete file from disk if it exists
        try:
            file_path = Path.cwd() / audio.file_path
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            print(f"Warning: Failed to delete audio file: {e}")
        
        # Delete from database
        self.db.delete(audio)
        self.db.commit()
        
        return True
    
    def estimate_audio_duration(self, word_count: int) -> float:
        """
        Estimate audio duration from word count.
        
        Args:
            word_count: Number of words in script
            
        Returns:
            Estimated duration in seconds
        """
        # Average speaking rate: 2.5 words per second
        WORDS_PER_SECOND = 2.5
        return word_count / WORDS_PER_SECOND
