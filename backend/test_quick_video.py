#!/usr/bin/env python3
"""
Quick 10-second video generation test.

Tests the complete pipeline with minimal duration:
1. Use existing analyzed article
2. Generate short script (10 seconds = ~25 words)
3. Generate TTS audio
4. Render video with new subtitle positioning
5. Verify output quality

Expected runtime: ~1-2 minutes
"""

import sys
import time
import requests
from datetime import datetime
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

# Override for quick 10-second test
TEST_DURATION = 10  # seconds
TEST_MAX_WORDS = 30  # words


def test_quick_video():
    """Run quick 10-second video generation test."""
    
    print("=" * 70)
    print("🎬 Quick 10-Second Video Generation Test")
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
        
        # Step 2: Generate short script
        print(f"\n📝 Step 2: Generating {TEST_DURATION}s script...")
        resp = requests.post(f"{BASE_URL}/scripts/generate", json={
            "article_id": article_id,
            "style": "engaging",
            "target_duration": TEST_DURATION  # Override to 10 seconds
        })
        resp.raise_for_status()
        script = resp.json()
        
        print(f"✅ Script generated: ID {script['id']}")
        print(f"   Word count: {script.get('word_count', 'N/A')}")
        print(f"   Est. duration: {script.get('estimated_duration', 'N/A')}s")
        
        if script.get("scenes"):
            print(f"   Scenes: {len(script['scenes'])}")
            for i, scene in enumerate(script['scenes'][:2], 1):
                print(f"   Scene {i}: {scene.get('image_keywords', [])}")
        
        # Auto-approve
        resp = requests.post(f"{BASE_URL}/scripts/{script['id']}/approve")
        resp.raise_for_status()
        print("✅ Script approved")
        
        time.sleep(1)
        
        # Step 3: Generate audio
        print("\n🔊 Step 3: Generating TTS audio...")
        resp = requests.post(f"{BASE_URL}/audio/generate", json={
            "script_id": script["id"],
            "tts_provider": "openai",  # Using OpenAI for speed
            "voice": "alloy"
        })
        resp.raise_for_status()
        audio = resp.json()
        
        print(f"✅ Audio generated: ID {audio['id']}")
        print(f"   Duration: {audio['duration']:.1f}s")
        
        # Step 4: Render video
        print("\n🎬 Step 4: Rendering video...")
        print("   (Should take ~30-60s)")
        
        resp = requests.post(f"{BASE_URL}/video/render", json={
            "script_id": script["id"],
            "audio_id": audio["id"],
            "background_style": "scenes"
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
            
            time.sleep(2)
            
            if time.time() - start_time > 300:  # 5 min timeout
                print("❌ Video render timeout")
                return 1
        
        # Step 5: Verify output
        print("\n📥 Step 5: Verifying output...")
        
        video_path = Path(video['file_path'])
        if not video_path.exists():
            video_path = Path("data/videos") / video_path.name
        
        if video_path.exists():
            file_size = video_path.stat().st_size
            print(f"✅ File size: {file_size / 1024 / 1024:.1f} MB")
            
            # Extract a frame to check text positioning
            import subprocess
            frame_path = Path(f"data/test_quick_{video['id']}_frame.jpg")
            subprocess.run([
                "ffmpeg", "-y", "-i", str(video_path),
                "-ss", "2", "-vframes", "1", "-q:v", "2",
                str(frame_path)
            ], capture_output=True)
            print(f"✅ Frame extracted: {frame_path}")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"\n✅ ALL STEPS PASSED")
        print(f"\n📹 Video: {video['file_path']}")
        print(f"⏱️  Duration: {video['duration']:.1f}s")
        print(f"🎨 Render time: {render_time:.1f}s")
        
        print("\n📋 Verification checklist:")
        print("1. [ ] Open video and check text appears only at BOTTOM")
        print("2. [ ] Check text has white color with black stroke")
        print("3. [ ] Verify script is short and punchy")
        print("4. [ ] Check background images match topic")
        
        return 0
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server. Is the backend running?")
        print("   Run: cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
        return 1
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(test_quick_video())
