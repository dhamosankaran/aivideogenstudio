"""
Whisper Service for Word-Level Audio Timing

Uses OpenAI's Whisper model to transcribe audio and extract word-level timestamps
for accurate subtitle synchronization.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import whisper
import json

logger = logging.getLogger(__name__)


class WhisperService:
    """Service for extracting word-level timing from audio files."""
    
    # Use 'small' model for 8GB RAM Macs (good balance of speed/accuracy)
    DEFAULT_MODEL = "small"
    CACHE_DIR = Path("data/whisper_cache")
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        """
        Initialize Whisper service.
        
        Args:
            model_name: Whisper model to use (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.model = None
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
    def _load_model(self):
        """Lazy load Whisper model (only when needed)."""
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            logger.info("Whisper model loaded successfully")
    
    def transcribe_audio(
        self, 
        audio_path: Path,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Transcribe audio and extract word-level timestamps.
        
        Args:
            audio_path: Path to audio file
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with transcription and word-level timing:
            {
                "text": "full transcription",
                "words": [
                    {"word": "hello", "start": 0.0, "end": 0.5},
                    {"word": "world", "start": 0.5, "end": 1.0}
                ],
                "segments": [...],  # Sentence-level segments
                "duration": 80.5
            }
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Check cache
        cache_key = f"{audio_path.stem}_{self.model_name}"
        cache_file = self.CACHE_DIR / f"{cache_key}.json"
        
        if use_cache and cache_file.exists():
            logger.info(f"Using cached transcription: {cache_file}")
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        # Load model if not already loaded
        self._load_model()
        
        # Transcribe with word-level timestamps
        logger.info(f"Transcribing audio: {audio_path}")
        result = self.model.transcribe(
            str(audio_path),
            word_timestamps=True,  # Enable word-level timing
            language="en"  # Assume English for AI news
        )
        
        # Extract word-level data
        words = []
        for segment in result.get("segments", []):
            for word_data in segment.get("words", []):
                words.append({
                    "word": word_data["word"].strip(),
                    "start": word_data["start"],
                    "end": word_data["end"]
                })
        
        # Build response
        timing_data = {
            "text": result["text"],
            "words": words,
            "segments": result.get("segments", []),
            "duration": result.get("segments", [{}])[-1].get("end", 0) if result.get("segments") else 0
        }
        
        # Cache results
        if use_cache:
            with open(cache_file, 'w') as f:
                json.dump(timing_data, f, indent=2)
            logger.info(f"Cached transcription: {cache_file}")
        
        logger.info(f"Transcription complete: {len(words)} words, {timing_data['duration']:.1f}s")
        return timing_data
    
    def get_word_timing(
        self,
        audio_path: Path,
        text: str
    ) -> List[Dict[str, Any]]:
        """
        Get word-level timing for specific text.
        
        Useful when you have the script text and need timing for those specific words.
        
        Args:
            audio_path: Path to audio file
            text: Text to get timing for
            
        Returns:
            List of word timing dictionaries
        """
        timing_data = self.transcribe_audio(audio_path)
        
        # Simple matching: return all words
        # TODO: Could add fuzzy matching if script text differs from transcription
        return timing_data["words"]
    
    def get_scene_timing(
        self,
        audio_path: Path,
        scenes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Get timing for each scene in a scene-based script.
        
        Args:
            audio_path: Path to audio file
            scenes: List of scene dictionaries with 'text' field
            
        Returns:
            Scenes with added timing information
        """
        timing_data = self.transcribe_audio(audio_path)
        all_words = timing_data["words"]
        
        # Simple approach: divide words evenly across scenes
        # TODO: Could use fuzzy matching to find exact scene boundaries
        total_words = len(all_words)
        total_scenes = len(scenes)
        
        if total_scenes == 0:
            return scenes
        
        words_per_scene = total_words // total_scenes
        
        enhanced_scenes = []
        word_index = 0
        
        for i, scene in enumerate(scenes):
            # Calculate word range for this scene
            start_idx = word_index
            if i == total_scenes - 1:
                # Last scene gets remaining words
                end_idx = total_words
            else:
                end_idx = start_idx + words_per_scene
            
            scene_words = all_words[start_idx:end_idx]
            
            if scene_words:
                scene_start = scene_words[0]["start"]
                scene_end = scene_words[-1]["end"]
                scene_duration = scene_end - scene_start
            else:
                scene_start = 0
                scene_end = 0
                scene_duration = 0
            
            enhanced_scene = {
                **scene,
                "start_time": scene_start,
                "end_time": scene_end,
                "duration": scene_duration,
                "words": scene_words
            }
            
            enhanced_scenes.append(enhanced_scene)
            word_index = end_idx
        
        return enhanced_scenes


# Convenience function for quick testing
def test_whisper(audio_file: str):
    """Test Whisper transcription on an audio file."""
    service = WhisperService()
    result = service.transcribe_audio(Path(audio_file))
    
    print(f"Transcription: {result['text'][:100]}...")
    print(f"Total words: {len(result['words'])}")
    print(f"Duration: {result['duration']:.1f}s")
    print(f"\nFirst 5 words:")
    for word_data in result['words'][:5]:
        print(f"  {word_data['start']:.2f}s - {word_data['end']:.2f}s: {word_data['word']}")
    
    return result


if __name__ == "__main__":
    # Test with Video 7 audio
    import sys
    if len(sys.argv) > 1:
        test_whisper(sys.argv[1])
    else:
        print("Usage: python whisper_service.py <audio_file>")
