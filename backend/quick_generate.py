#!/usr/bin/env python3
"""
Quick Production Video Generator

Directly generates videos from article IDs that are already analyzed.
"""

import sys
import time
import requests

BASE_URL = "http://localhost:8000/api"

# Use article IDs that we know are analyzed
ARTICLE_IDS = [2, 3, 4, 5]  # Skip ID 1 as it was used in E2E test

def generate_video_from_article(article_id):
    """Generate complete video from article ID"""
    print(f"\n{'='*60}")
    print(f"Generating video from article ID: {article_id}")
    print(f"{'='*60}")
    
    try:
        # Get article info
        resp = requests.get(f"{BASE_URL}/articles/{article_id}")
        resp.raise_for_status()
        article = resp.json()
        print(f"📰 Article: {article['title'][:60]}...")
        
        # Generate script
        print(f"📝 Generating script...")
        resp = requests.post(f"{BASE_URL}/scripts/generate", json={
            "article_id": article_id,
            "style": "engaging"
        })
        resp.raise_for_status()
        script = resp.json()
        print(f"   ✅ Script ID: {script['id']} ({script['word_count']} words)")
        
        # Auto-approve
        resp = requests.post(f"{BASE_URL}/scripts/{script['id']}/approve")
        resp.raise_for_status()
        
        time.sleep(2)  # Wait for commit
        
        # Generate audio
        print(f"🔊 Generating audio...")
        resp = requests.post(f"{BASE_URL}/audio/generate", json={
            "script_id": script['id'],
            "tts_provider": "google",
            "voice": "en-US-Journey-F"
        })
        resp.raise_for_status()
        audio = resp.json()
        print(f"   ✅ Audio ID: {audio['id']} ({audio['duration']:.1f}s, ${audio.get('generation_cost', 0):.4f})")
        
        # Render video
        print(f"🎬 Rendering video...")
        resp = requests.post(f"{BASE_URL}/video/render", json={
            "script_id": script['id'],
            "audio_id": audio['id'],
            "background_style": "gradient"
        })
        resp.raise_for_status()
        video = resp.json()
        
        # Poll for completion
        start_time = time.time()
        while True:
            resp = requests.get(f"{BASE_URL}/video/{video['id']}")
            video = resp.json()
            
            if video["status"] == "completed":
                render_time = time.time() - start_time
                print(f"   ✅ Video ID: {video['id']} ({video['duration']:.1f}s, rendered in {render_time:.1f}s)")
                print(f"   📁 File: {video['file_path']}")
                return video['id']
            
            elif video["status"] == "failed":
                print(f"   ❌ Failed: {video.get('error_message')}")
                return None
            
            time.sleep(2)
            
            if time.time() - start_time > 300:
                print(f"   ❌ Timeout")
                return None
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    num_videos = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    
    print("=" * 60)
    print(f"🚀 Quick Production Video Generation")
    print("=" * 60)
    
    success = []
    failed = []
    
    for article_id in ARTICLE_IDS[:num_videos]:
        video_id = generate_video_from_article(article_id)
        if video_id:
            success.append(video_id)
        else:
            failed.append(article_id)
    
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successful: {len(success)}")
    print(f"❌ Failed: {len(failed)}")
    print(f"\n🎬 View videos at: http://localhost:5173")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
