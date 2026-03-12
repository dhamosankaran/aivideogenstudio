import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.services.whisper_service import WhisperService

def test_alignment():
    service = WhisperService()
    
    # Mock transcribe_audio
    service.transcribe_audio = MagicMock(return_value={
        "words": [
            {"word": "Welcome", "start": 0.0, "end": 0.5},
            {"word": "to", "start": 0.5, "end": 0.7},
            {"word": "the", "start": 0.7, "end": 0.9},
            {"word": "future", "start": 0.9, "end": 1.5},
            {"word": "of", "start": 1.5, "end": 1.7},
            {"word": "AI", "start": 1.7, "end": 2.2},
            {"word": "Today", "start": 2.5, "end": 3.0},
            {"word": "we", "start": 3.0, "end": 3.2},
            {"word": "look", "start": 3.2, "end": 3.5},
            {"word": "at", "start": 3.5, "end": 3.7},
            {"word": "Agentic", "start": 3.7, "end": 4.5},
            {"word": "Coding", "start": 4.5, "end": 5.2},
        ],
        "segments": []
    })
    
    scenes = [
        {"text": "Welcome to the future of AI."},
        {"text": "Today we look at Agentic Coding."}
    ]
    
    # Test alignment
    result = service.get_scene_timing(Path("fake.mp3"), scenes)
    
    for i, scene in enumerate(result):
        print(f"Scene {i+1}: {scene['start_time']:.2f}s - {scene['end_time']:.2f}s ({len(scene['words'])} words)")
        print(f"  Text: {scene['text']}")
        print(f"  Words: {' '.join([w['word'] for w in scene['words']])}")

    # Assertions
    assert len(result) == 2
    assert result[0]['words'][-1]['word'] == "AI"
    assert result[1]['words'][0]['word'] == "Today"
    assert result[0]['end_time'] == 2.2
    assert result[1]['start_time'] == 2.5
    print("\n✅ Alignment test passed!")

if __name__ == "__main__":
    try:
        test_alignment()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
