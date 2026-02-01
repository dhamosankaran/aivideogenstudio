#!/usr/bin/env python3
"""
Full pipeline validation: Script → Google TTS → Video
"""
import requests
import time
import sys

BASE_URL = "http://localhost:8000/api"

def test_google_tts():
    """Test Google TTS with real API"""
    print("🔊 Testing Google TTS API...")
    
    # Get approved script
    resp = requests.get(f"{BASE_URL}/scripts", params={"status": "approved"})
    scripts = resp.json()
    if not scripts:
        print("❌ No approved scripts found")
        return False
    
    script_id = scripts[0]['id']
    print(f"✅ Using script ID: {script_id}")
    
    # Generate audio with Google TTS
    resp = requests.post(f"{BASE_URL}/audio/generate", json={
        "script_id": script_id,
        "tts_provider": "google",
        "voice": "en-US-Journey-F"
    })
    
    if resp.status_code != 201:
        print(f"❌ Audio generation failed: {resp.status_code}")
        print(resp.text)
        return False
    
    audio = resp.json()
    print(f"✅ Audio generated: ID {audio['id']}, Duration: {audio['duration']}s")
    
    # Trigger video render
    print("🎬 Rendering video...")
    resp = requests.post(f"{BASE_URL}/video/render", json={
        "script_id": script_id,
        "audio_id": audio['id'],
        "background_style": "gradient"
    })
    
    if resp.status_code != 200:
        print(f"❌ Video render failed: {resp.status_code}")
        print(resp.text)
        return False
    
    video = resp.json()
    video_id = video['id']
    print(f"✅ Video render started: ID {video_id}")
    
    # Poll for completion
    print("⏳ Waiting for render...")
    for i in range(60):  # 2 min timeout
        resp = requests.get(f"{BASE_URL}/video/{video_id}")
        video = resp.json()
        
        if video['status'] == 'completed':
            print(f"✅ VALIDATION SUCCESS!")
            print(f"   Video: {video['file_path']}")
            print(f"   Duration: {video['duration']}s")
            print(f"   Audio: Google TTS (Journey-F)")
            return True
        elif video['status'] == 'failed':
            print(f"❌ Video failed: {video.get('error_message')}")
            return False
        
        time.sleep(2)
    
    print("❌ Timeout waiting for video")
    return False

if __name__ == "__main__":
    success = test_google_tts()
    sys.exit(0 if success else 1)
