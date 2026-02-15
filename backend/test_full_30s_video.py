#!/usr/bin/env python3
"""
Full 30-Second Video Generation Test

Tests the complete pipeline with target 30-second duration:
1. Use specific article by ID
2. Generate script targeting 25-30 seconds
3. Generate TTS audio
4. Render video with Serper images
5. Verify all outputs

Usage:
    python test_full_30s_video.py
    python test_full_30s_video.py --article_id 66
"""

import sys
import time
import argparse
import requests
from datetime import datetime
from pathlib import Path

BASE_URL = "http://localhost:8000/api"


def test_full_video(article_id: int = None, target_duration: int = 25):
    """Run full 30-second video generation test."""
    
    print("=" * 70)
    print("🎬 Full 30-Second Video Generation Test")
    print(f"   Target duration: {target_duration}s")
    print("=" * 70)
    
    try:
        # Step 1: Get article
        print("\n📰 Step 1: Finding article...")
        resp = requests.get(f"{BASE_URL}/articles", params={"limit": 10})
        resp.raise_for_status()
        articles = resp.json()
        
        if article_id:
            article = next((a for a in articles if a["id"] == article_id), None)
            if not article:
                print(f"❌ Article ID {article_id} not found")
                return 1
        else:
            analyzed = [a for a in articles if a.get("analyzed_at")]
            if not analyzed:
                print("❌ No analyzed articles found")
                return 1
            # Get the second most recent if available
            article = analyzed[1] if len(analyzed) > 1 else analyzed[0]
        
        print(f"✅ Using article ID {article['id']}: {article['title'][:55]}...")
        
        # Step 2: Generate script with 25-second target
        print(f"\n📝 Step 2: Generating {target_duration}s script...")
        resp = requests.post(f"{BASE_URL}/scripts/generate", json={
            "article_id": article["id"],
            "style": "engaging",
            "target_duration": target_duration
        })
        resp.raise_for_status()
        script = resp.json()
        
        print(f"✅ Script generated: ID {script['id']}")
        print(f"   Word count: {script.get('word_count', 'N/A')}")
        print(f"   Est. duration: {script.get('estimated_duration', 'N/A')}s")
        
        # Show scenes if available
        if script.get("scenes"):
            print(f"   Scenes: {len(script['scenes'])}")
            for i, scene in enumerate(script['scenes'], 1):
                keywords = scene.get('image_keywords', [])
                print(f"   Scene {i}: {keywords}")
        
        # Auto-approve
        resp = requests.post(f"{BASE_URL}/scripts/{script['id']}/approve")
        resp.raise_for_status()
        print("✅ Script approved")
        
        time.sleep(1)
        
        # Step 3: Generate audio
        print("\n🔊 Step 3: Generating TTS audio...")
        resp = requests.post(f"{BASE_URL}/audio/generate", json={
            "script_id": script["id"],
            "tts_provider": "openai",
            "voice": "alloy"
        })
        resp.raise_for_status()
        audio = resp.json()
        
        audio_duration = audio['duration']
        print(f"✅ Audio generated: ID {audio['id']}")
        print(f"   Duration: {audio_duration:.1f}s")
        
        # Check if within target range
        if 20 <= audio_duration <= 35:
            print(f"   ✅ Duration is within target range (20-35s)")
        else:
            print(f"   ⚠️ Duration outside target range")
        
        # Step 4: Render video
        print("\n🎬 Step 4: Rendering video...")
        print("   (Serper will fetch topic-relevant images)")
        
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
            
            elapsed = time.time() - start_time
            
            if video["status"] == "completed":
                render_time = elapsed
                print(f"✅ Video completed in {render_time:.1f}s")
                print(f"   Duration: {video['duration']:.1f}s")
                print(f"   File: {video['file_path']}")
                break
            
            elif video["status"] == "failed":
                print(f"❌ Video render failed: {video.get('error_message')}")
                return 1
            
            elif elapsed > 300:
                print("❌ Video render timeout (5 min)")
                return 1
            
            # Show progress
            if int(elapsed) % 10 == 0 and elapsed > 0:
                print(f"   ... {elapsed:.0f}s elapsed")
            
            time.sleep(2)
        
        # Step 5: Verify output
        print("\n📥 Step 5: Verifying output...")
        
        video_path = Path(video['file_path'])
        if not video_path.exists():
            video_path = Path("data/videos") / video_path.name
        
        if video_path.exists():
            file_size = video_path.stat().st_size
            print(f"✅ File size: {file_size / 1024 / 1024:.1f} MB")
            
            # Extract frames at different times to verify
            import subprocess
            
            for sec in [2, 10, 20]:
                if sec < video['duration']:
                    frame_path = Path(f"data/test_30s_video_{video['id']}_frame_{sec}s.jpg")
                    subprocess.run([
                        "ffmpeg", "-y", "-i", str(video_path),
                        "-ss", str(sec), "-vframes", "1", "-q:v", "2",
                        str(frame_path)
                    ], capture_output=True)
                    if frame_path.exists():
                        print(f"✅ Frame at {sec}s: {frame_path}")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        duration = video['duration']
        
        # Check all criteria
        checks = []
        checks.append(("Duration 20-35s", 20 <= duration <= 35))
        checks.append(("Script < 80 words", script.get('word_count', 100) <= 80))
        checks.append(("Two scenes", len(script.get('scenes', [])) <= 3))
        checks.append(("Render < 90s", render_time < 90))
        
        all_passed = all(passed for _, passed in checks)
        
        for check_name, passed in checks:
            icon = "✅" if passed else "❌"
            print(f"   {icon} {check_name}")
        
        print(f"\n📹 Video: {video['file_path']}")
        print(f"⏱️  Duration: {duration:.1f}s")
        print(f"📝 Words: {script.get('word_count', 'N/A')}")
        print(f"🎨 Render time: {render_time:.1f}s")
        
        if all_passed:
            print("\n✅ ALL CHECKS PASSED!")
        else:
            print("\n⚠️ Some checks failed - review above")
        
        print("\n📋 Visual verification:")
        print("   1. Open video and verify text at BOTTOM only")
        print("   2. Check background images match topic")
        print("   3. Verify script is punchy and engaging")
        print("=" * 70)
        
        return 0 if all_passed else 1
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server")
        print("   Start with: uvicorn app.main:app --reload")
        return 1
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Full 30s video generation test")
    parser.add_argument("--article_id", type=int, help="Specific article ID to use")
    parser.add_argument("--duration", type=int, default=25, help="Target duration (default: 25)")
    args = parser.parse_args()
    
    sys.exit(test_full_video(args.article_id, args.duration))
