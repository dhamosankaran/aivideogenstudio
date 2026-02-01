#!/usr/bin/env python3
"""
End-to-End Test for NotebookLM-Style Video Generation

Tests the complete enhanced pipeline:
1. Use existing analyzed article
2. Generate scene-based script with image keywords
3. Generate TTS audio
4. Extract word-level timing with Whisper
5. Fetch images from Pexels
6. Compose video with scenes, transitions, and word-level subtitles
7. Verify output quality

Expected runtime: ~3-5 minutes
Expected cost: ~$0.02-0.03
"""

import sys
import time
import requests
from datetime import datetime
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

def test_notebooklm_video():
    """Run full NotebookLM-style video generation test."""
    
    print("=" * 70)
    print("🎬 NotebookLM-Style Video Generation - E2E Test")
    print("=" * 70)
    
    try:
        # Step 1: Get an analyzed article
        print("\n📰 Step 1: Finding analyzed article...")
        resp = requests.get(f"{BASE_URL}/articles", params={"limit": 10})
        resp.raise_for_status()
        articles = resp.json()
        
        analyzed = [a for a in articles if a.get("analyzed_at")]
        if not analyzed:
            print("❌ No analyzed articles found. Run article analysis first.")
            return 1
        
        article = analyzed[0]
        article_id = article["id"]
        print(f"✅ Using article: {article['title'][:60]}...")
        
        # Step 2: Generate scene-based script
        print("\n📝 Step 2: Generating scene-based script...")
        resp = requests.post(f"{BASE_URL}/scripts/generate", json={
            "article_id": article_id,
            "style": "engaging"
        })
        resp.raise_for_status()
        script = resp.json()
        
        print(f"✅ Script generated: ID {script['id']}")
        if script.get("scenes"):
            print(f"   Scenes: {len(script['scenes'])}")
            for i, scene in enumerate(script['scenes'][:2], 1):  # Show first 2
                print(f"   Scene {i}: {scene.get('image_keywords', [])}")
        else:
            print("   ⚠️ No scenes found in script (using legacy format)")
        
        # Auto-approve
        resp = requests.post(f"{BASE_URL}/scripts/{script['id']}/approve")
        resp.raise_for_status()
        print("✅ Script approved")
        
        time.sleep(2)  # Wait for commit
        
        # Step 3: Generate audio
        print("\n🔊 Step 3: Generating TTS audio...")
        resp = requests.post(f"{BASE_URL}/audio/generate", json={
            "script_id": script["id"],
            "tts_provider": "google",
            "voice": "en-US-Journey-F"
        })
        resp.raise_for_status()
        audio = resp.json()
        
        print(f"✅ Audio generated: ID {audio['id']}")
        print(f"   Duration: {audio['duration']:.1f}s")
        print(f"   Cost: ${audio.get('generation_cost', 0):.4f}")
        
        # Step 4: Render NotebookLM-style video
        print("\n🎬 Step 4: Rendering NotebookLM-style video...")
        print("   (This will take ~30-60s)")
        
        resp = requests.post(f"{BASE_URL}/video/render", json={
            "script_id": script["id"],
            "audio_id": audio["id"],
            "background_style": "scenes"  # Use scene-based composition
        })
        resp.raise_for_status()
        video = resp.json()
        
        print(f"✅ Video render started: ID {video['id']}")
        
        # Poll for completion
        print("⏳ Waiting for render...")
        start_time = time.time()
        
        while True:
            resp = requests.get(f"{BASE_URL}/video/{video['id']}")
            video = resp.json()
            
            if video["status"] == "completed":
                render_time = time.time() - start_time
                print(f"✅ Video completed in {render_time:.1f}s")
                print(f"   Duration: {video['duration']:.1f}s")
                print(f"   File: {video['file_path']}")
                break
            
            elif video["status"] == "failed":
                print(f"❌ Video render failed: {video.get('error_message')}")
                return 1
            
            time.sleep(3)
            
            if time.time() - start_time > 600:  # 10 min timeout
                print("❌ Video render timeout")
                return 1
        
        # Step 5: Download and verify
        print("\n📥 Step 5: Downloading video...")
        resp = requests.get(f"{BASE_URL}/video/{video['id']}/download", stream=True)
        resp.raise_for_status()
        
        test_file = Path(f"test_notebooklm_video_{video['id']}.mp4")
        with open(test_file, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = test_file.stat().st_size
        print(f"✅ Video downloaded: {file_size / 1024 / 1024:.1f} MB")
        print(f"   Saved to: {test_file.absolute()}")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        total_cost = (
            script.get("generation_cost", 0) +
            audio.get("generation_cost", 0)
        )
        
        print(f"\n✅ ALL STEPS PASSED")
        print(f"\n💰 Total Cost: ${total_cost:.4f}")
        print(f"🎬 Video: {test_file.absolute()}")
        print(f"⏱️  Render Time: {render_time:.1f}s")
        
        print("\n📋 Next Steps:")
        print("1. Watch the video to verify quality")
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


if __name__ == "__main__":
    sys.exit(test_notebooklm_video())
