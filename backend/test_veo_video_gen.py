"""
Test script for Veo 3.1 Video Generation API (google-genai SDK).
Generates a cinematic 8-second portrait video clip.

Usage:
    cd backend
    python test_veo_video_gen.py

Output:
    data/test_veo_output.mp4
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv


def test_veo_video_gen():
    # ── 1. Environment ────────────────────────────────────────────────
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ API key not found. Set GEMINI_API_KEY or GOOGLE_API_KEY in .env")
        return False

    print(f"✅ API key found: {api_key[:6]}...{api_key[-4:]}")

    # ── 2. SDK import ─────────────────────────────────────────────────
    try:
        from google import genai
        from google.genai import types
        print("✅ google-genai SDK imported")
    except ImportError:
        print("❌ google-genai not installed. Run: pip install google-genai")
        return False

    # ── 3. Client + config ───────────────────────────────────────────
    client = genai.Client(api_key=api_key)

    MODEL = "veo-3.1-generate-preview"
    ASPECT_RATIO = "9:16"       # Portrait for YouTube Shorts
    DURATION = 8                # seconds
    POLL_INTERVAL = 10          # seconds between polls
    MAX_WAIT = 300              # 5-minute hard timeout

    output_path = Path("data/test_veo_output.mp4")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    prompt = (
        "An open hardcover book resting on a wooden desk, warm golden-hour sunlight streaming "
        "through tall windows casting long shadows across the pages. "
        "Slow cinematic push-in toward the book, shallow depth of field. "
        "Rich amber tones, film grain, 24fps look. "
        "Vertical composition (9:16). No text, no watermarks, no people."
    )

    print(f"\n📽  Model       : {MODEL}")
    print(f"📐 Aspect ratio : {ASPECT_RATIO}")
    print(f"⏱  Duration    : {DURATION}s")
    print(f"📝 Prompt       : {prompt[:100]}...")
    print(f"💾 Output       : {output_path.resolve()}")
    print("\n⏳ Submitting generation request...")

    # ── 4. Submit ─────────────────────────────────────────────────────
    try:
        operation = client.models.generate_videos(
            model=MODEL,
            prompt=prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio=ASPECT_RATIO,
                duration_seconds=str(DURATION),
            ),
        )
        print("✅ Request accepted — polling for completion...")
    except Exception as e:
        print(f"❌ Failed to submit request: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ── 5. Poll ───────────────────────────────────────────────────────
    elapsed = 0
    while not operation.done:
        if elapsed >= MAX_WAIT:
            print(f"❌ Timed out after {MAX_WAIT}s")
            return False
        print(f"   [{elapsed:>3}s] Still generating...")
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        operation = client.operations.get(operation)

    print(f"✅ Generation complete! ({elapsed}s)")

    # ── 6. Download + save ────────────────────────────────────────────
    try:
        print(f"   Raw response: {operation.response}")
        generated_videos = operation.response.generated_videos
        if not generated_videos:
            print("❌ No videos in response (prompt may have been blocked — check raw response above)")
            return False

        video = generated_videos[0]
        client.files.download(file=video.video)
        video.video.save(str(output_path))

        if not output_path.exists():
            print("❌ File was not saved (path does not exist after save)")
            return False

        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"\n🎉 SUCCESS!")
        print(f"   Saved : {output_path.resolve()}")
        print(f"   Size  : {size_mb:.2f} MB")
        print(f"   Time  : {elapsed}s generation + download")
        return True

    except Exception as e:
        print(f"❌ Failed to download/save video: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_veo_video_gen()
    sys.exit(0 if success else 1)
