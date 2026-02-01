#!/usr/bin/env python3
"""
Generate Production Videos

Generates videos from the top analyzed articles.
This script:
1. Finds top analyzed articles
2. Generates scripts for them
3. Generates audio (Google TTS)
4. Renders videos
5. Reports results

Usage:
    python generate_production_videos.py [num_videos]
    
Example:
    python generate_production_videos.py 5  # Generate 5 videos
"""

import sys
import time
import requests
from datetime import datetime
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

def get_top_articles(limit=10):
    """Get top analyzed articles"""
    print(f"🔍 Fetching top {limit} analyzed articles...")
    
    resp = requests.get(f"{BASE_URL}/articles", params={"limit": limit})
    resp.raise_for_status()
    articles = resp.json()
    
    # Filter for analyzed articles
    analyzed = [a for a in articles if a.get("analyzed_at")]
    
    print(f"   Found {len(analyzed)} analyzed articles")
    return analyzed

def generate_script(article_id, article_title):
    """Generate script for article"""
    print(f"\n📝 Generating script for: {article_title[:60]}...")
    
    try:
        resp = requests.post(f"{BASE_URL}/scripts/generate", json={
            "article_id": article_id,
            "style": "engaging"
        })
        resp.raise_for_status()
        script = resp.json()
        
        # Auto-approve
        resp = requests.post(f"{BASE_URL}/scripts/{script['id']}/approve")
        resp.raise_for_status()
        
        print(f"   ✅ Script ID: {script['id']} ({script['word_count']} words, {script['estimated_duration']:.1f}s)")
        return script["id"]
        
    except Exception as e:
        print(f"   ❌ Script generation failed: {e}")
        return None

def generate_audio(script_id):
    """Generate TTS audio"""
    print(f"   🔊 Generating audio...")
    
    try:
        resp = requests.post(f"{BASE_URL}/audio/generate", json={
            "script_id": script_id,
            "tts_provider": "google",
            "voice": "en-US-Journey-F"
        })
        resp.raise_for_status()
        audio = resp.json()
        
        print(f"   ✅ Audio ID: {audio['id']} ({audio['duration']:.1f}s, ${audio.get('generation_cost', 0):.4f})")
        return audio["id"]
        
    except Exception as e:
        print(f"   ❌ Audio generation failed: {e}")
        return None

def render_video(script_id, audio_id):
    """Render video"""
    print(f"   🎬 Rendering video...")
    
    try:
        resp = requests.post(f"{BASE_URL}/video/render", json={
            "script_id": script_id,
            "audio_id": audio_id,
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
                return video["id"]
            
            elif video["status"] == "failed":
                print(f"   ❌ Video render failed: {video.get('error_message')}")
                return None
            
            time.sleep(2)
            
            if time.time() - start_time > 300:
                print(f"   ❌ Video render timeout")
                return None
                
    except Exception as e:
        print(f"   ❌ Video rendering failed: {e}")
        return None

def generate_videos(num_videos=5):
    """Generate multiple production videos"""
    print("=" * 60)
    print(f"🚀 Generating {num_videos} Production Videos")
    print("=" * 60)
    
    articles = get_top_articles(limit=num_videos * 2)  # Get extra in case some fail
    
    if not articles:
        print("❌ No analyzed articles found. Run article analysis first.")
        return 1
    
    results = {
        "success": [],
        "failed": []
    }
    
    for i, article in enumerate(articles[:num_videos], 1):
        print(f"\n{'='*60}")
        print(f"Video {i}/{num_videos}")
        print(f"{'='*60}")
        
        article_id = article["id"]
        article_title = article["title"]
        
        # Generate script
        script_id = generate_script(article_id, article_title)
        if not script_id:
            results["failed"].append(article_title)
            continue
        
        # Wait for script to commit
        time.sleep(2)
        
        # Generate audio
        audio_id = generate_audio(script_id)
        if not audio_id:
            results["failed"].append(article_title)
            continue
        
        # Render video
        video_id = render_video(script_id, audio_id)
        if not video_id:
            results["failed"].append(article_title)
            continue
        
        results["success"].append({
            "title": article_title,
            "video_id": video_id
        })
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 PRODUCTION VIDEO GENERATION SUMMARY")
    print("=" * 60)
    
    print(f"\n✅ Successful: {len(results['success'])}")
    for item in results["success"]:
        print(f"   - Video {item['video_id']}: {item['title'][:60]}...")
    
    if results["failed"]:
        print(f"\n❌ Failed: {len(results['failed'])}")
        for title in results["failed"]:
            print(f"   - {title[:60]}...")
    
    print(f"\n🎬 View videos at: http://localhost:5173")
    print(f"📊 API docs: http://localhost:8000/docs")
    
    return 0 if results["success"] else 1

def main():
    num_videos = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    
    try:
        return generate_videos(num_videos)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
