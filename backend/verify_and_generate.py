#!/usr/bin/env python3
"""
Pre-flight check and video generation with proper verification.
"""

import sys
import asyncio
from pathlib import Path

from app.database import SessionLocal
from app.models import Script, Audio
from app.services.whisper_service import WhisperService
from app.services.pexels_service import PexelsService
from app.services.enhanced_video_service import EnhancedVideoCompositionService


async def verify_and_generate():
    """Verify all components before generating video."""
    
    print("=" * 70)
    print("🔍 PRE-FLIGHT CHECKS")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Check 1: Find script with scenes
        print("\n✓ Checking for scene-based script...")
        script = db.query(Script).filter(
            Script.scenes.isnot(None),
            Script.status == "approved"
        ).order_by(Script.id.desc()).first()
        
        if not script:
            print("❌ No approved scene-based script found")
            return 1
        
        print(f"✅ Script ID {script.id}: {len(script.scenes)} scenes")
        for i, scene in enumerate(script.scenes[:2], 1):
            print(f"   Scene {i}: {scene.get('image_keywords', [])}")
        
        # Check 2: Find audio for this script
        print("\n✓ Checking for audio...")
        audio = db.query(Audio).filter(
            Audio.script_id == script.id,
            Audio.status == "completed"
        ).first()
        
        if not audio:
            print("❌ No completed audio found for this script")
            return 1
        
        audio_path = Path(audio.file_path)
        if not audio_path.exists():
            print(f"❌ Audio file not found: {audio_path}")
            return 1
        
        print(f"✅ Audio ID {audio.id}: {audio.duration:.1f}s ({audio_path})")
        
        # Check 3: Test Whisper
        print("\n✓ Testing Whisper word-level timing...")
        whisper = WhisperService()
        timing_data = whisper.transcribe_audio(audio_path)
        
        print(f"✅ Whisper: {len(timing_data['words'])} words, {timing_data['duration']:.1f}s")
        print(f"   First 3 words:")
        for w in timing_data['words'][:3]:
            print(f"     {w['start']:.2f}-{w['end']:.2f}s: {w['word']}")
        
        # Check 4: Test Pexels
        print("\n✓ Testing Pexels image service...")
        try:
            pexels = PexelsService()
            test_keywords = script.scenes[0].get('image_keywords', ['technology'])
            test_image = pexels.search_image(test_keywords)
            if test_image:
                print(f"✅ Pexels: Image downloaded ({test_image})")
            else:
                print("⚠️  Pexels: No image found (will use gradient)")
        except Exception as e:
            print(f"⚠️  Pexels: {e} (will use gradient)")
        
        # Check 5: Verify scene timing
        print("\n✓ Mapping scenes to audio timing...")
        scenes_with_timing = whisper.get_scene_timing(audio_path, script.scenes)
        
        print(f"✅ Scene timing:")
        for scene in scenes_with_timing:
            print(f"   Scene {scene['scene_number']}: {scene['start_time']:.1f}s - {scene['end_time']:.1f}s ({scene['duration']:.1f}s)")
        
        # All checks passed!
        print("\n" + "=" * 70)
        print("✅ ALL PRE-FLIGHT CHECKS PASSED")
        print("=" * 70)
        
        # Generate video
        print("\n🎬 Generating video...")
        video_service = EnhancedVideoCompositionService(db)
        video = video_service.create_video_task(
            script_id=script.id,
            audio_id=audio.id,
            background_style="scenes"
        )
        
        print(f"✅ Video task created: ID {video.id}")
        print("⏳ Processing (this will take ~2 minutes)...")
        
        video_service.process_video(video.id)
        
        db.refresh(video)
        
        if video.status == "completed":
            print(f"\n✅ VIDEO COMPLETE!")
            print(f"   File: {video.file_path}")
            print(f"   Duration: {video.duration:.1f}s")
            print(f"   Size: {video.file_size / 1024 / 1024:.1f} MB")
            print(f"   Processing time: {video.processing_time:.1f}s")
            print(f"\n🎬 Open video: open {video.file_path}")
            return 0
        else:
            print(f"\n❌ Video failed: {video.error_message}")
            return 1
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(verify_and_generate()))
