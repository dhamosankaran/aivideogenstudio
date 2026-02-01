#!/usr/bin/env python3
"""
Direct NotebookLM-Style Video Test (bypasses API)

Uses database and services directly to test the complete pipeline.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

from app.database import SessionLocal
from app.models import Article, Script, Audio, Video
from app.services.script_service import ScriptService
from app.services.audio_service import AudioService
from app.services.enhanced_video_service import EnhancedVideoCompositionService


async def test_notebooklm_direct():
    """Run NotebookLM-style video generation test using services directly."""
    
    print("=" * 70)
    print("🎬 NotebookLM-Style Video - Direct Test")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Step 1: Get analyzed article
        print("\n📰 Step 1: Finding analyzed article...")
        article = db.query(Article).filter(Article.analyzed_at.isnot(None)).first()
        
        if not article:
            print("❌ No analyzed articles found")
            return 1
        
        print(f"✅ Using article ID {article.id}: {article.title[:60]}...")
        
        # Step 2: Generate scene-based script
        print("\n📝 Step 2: Generating scene-based script...")
        script_service = ScriptService(db)
        script = await script_service.generate_script(
            article=article,
            style="engaging",
            target_duration=90
        )
        
        print(f"✅ Script generated: ID {script.id}")
        if script.scenes:
            print(f"   Scenes: {len(script.scenes)}")
            for i, scene in enumerate(script.scenes[:2], 1):
                print(f"   Scene {i}: {scene.get('image_keywords', [])}")
        else:
            print("   ⚠️ No scenes found (using legacy format)")
        
        # Auto-approve
        script_service.approve_script(script.id)
        print("✅ Script approved")
        
        # Step 3: Generate audio
        print("\n🔊 Step 3: Generating TTS audio...")
        audio_service = AudioService(db)
        audio = await audio_service.generate_audio_from_script(
            script_id=script.id,
            tts_provider="google",
            voice="en-US-Journey-F"
        )
        
        print(f"✅ Audio generated: ID {audio.id}")
        print(f"   Duration: {audio.duration:.1f}s")
        print(f"   Cost: ${audio.generation_cost:.4f}")
        
        # Step 4: Render video
        print("\n🎬 Step 4: Rendering NotebookLM-style video...")
        print("   (This will take ~30-60s)")
        
        video_service = EnhancedVideoCompositionService(db)
        video = video_service.create_video_task(
            script_id=script.id,
            audio_id=audio.id,
            background_style="scenes"
        )
        
        print(f"✅ Video task created: ID {video.id}")
        print("⏳ Processing video...")
        
        # Process synchronously
        video_service.process_video(video.id)
        
        # Refresh to get updated status
        db.refresh(video)
        
        if video.status == "completed":
            print(f"✅ Video completed!")
            print(f"   Duration: {video.duration:.1f}s")
            print(f"   File: {video.file_path}")
            print(f"   Size: {video.file_size / 1024 / 1024:.1f} MB")
        else:
            print(f"❌ Video failed: {video.error_message}")
            return 1
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        total_cost = script.generation_cost + audio.generation_cost
        
        print(f"\n✅ ALL STEPS PASSED")
        print(f"\n💰 Total Cost: ${total_cost:.4f}")
        print(f"🎬 Video: {video.file_path}")
        print(f"⏱️  Processing Time: {video.processing_time:.1f}s")
        
        print("\n📋 Next Steps:")
        print("1. Watch the video to verify quality")
        print(f"   open {video.file_path}")
        print("2. Check subtitle sync (should be perfect)")
        print("3. Verify images match scene content")
        print("4. Confirm transitions are smooth")
        
        print("\n🎉 NotebookLM-style video generation is working!")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(test_notebooklm_direct()))
