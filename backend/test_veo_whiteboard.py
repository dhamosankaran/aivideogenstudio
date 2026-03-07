"""
Test script: Can Veo 3.1 produce whiteboard animation style?

Tests two prompt strategies:
  A) Explicit whiteboard description (hand drawing on white canvas)
  B) Explainer video style (diagram-focused, minimal background)

Output files:
  data/test_veo_whiteboard_a.mp4
  data/test_veo_whiteboard_b.mp4

Usage:
    cd backend
    python test_veo_whiteboard.py
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv


PROMPTS = {
    "a_whiteboard": {
        "file": "data/test_veo_whiteboard_a.mp4",
        "label": "Strategy A — Explicit whiteboard hand-drawing",
        "prompt": (
            "Whiteboard animation style video. A hand holding a black marker draws on a clean pure white background. "
            "The hand sketches an open book with glowing pages, then draws upward arrows and stars bursting around it. "
            "Simple black outlines appear stroke by stroke, then colored fills appear. "
            "Fast drawing motion, satisfying reveal. "
            "Explainer video aesthetic, no real photography, illustrated style only. "
            "Vertical 9:16 composition. No text overlays, no watermarks."
        ),
    },
    "b_explainer": {
        "file": "data/test_veo_whiteboard_b.mp4",
        "label": "Strategy B — Flat illustration / explainer diagram",
        "prompt": (
            "2D flat illustration animation on a white background. "
            "Simple cartoon diagram of a lightbulb transforming into a brain, "
            "connected by flowing lines and colorful thought bubbles. "
            "Clean vector art style, bold outlines, vibrant colors. "
            "Smooth motion graphics animation, each element appears with a draw-on effect. "
            "Educational explainer video style. "
            "Vertical 9:16 composition. No people, no photography, no text overlays."
        ),
    },
}


def generate_video(client, types, prompt_key: str, config: dict) -> bool:
    MODEL = "veo-3.1-generate-preview"
    POLL_INTERVAL = 10
    MAX_WAIT = 300

    output_path = Path(config["file"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  {config['label']}")
    print(f"{'='*60}")
    print(f"  Output : {output_path.resolve()}")
    print(f"  Prompt : {config['prompt'][:120]}...")
    print()

    # Submit
    try:
        operation = client.models.generate_videos(
            model=MODEL,
            prompt=config["prompt"],
            config=types.GenerateVideosConfig(
                aspect_ratio="9:16",
                duration_seconds="8",
            ),
        )
        print("  ⏳ Request accepted — polling...")
    except Exception as e:
        print(f"  ❌ Submit failed: {type(e).__name__}: {e}")
        return False

    # Poll
    elapsed = 0
    while not operation.done:
        if elapsed >= MAX_WAIT:
            print(f"  ❌ Timed out after {MAX_WAIT}s")
            return False
        print(f"  [{elapsed:>3}s] Generating...")
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        operation = client.operations.get(operation)

    print(f"  ✅ Complete ({elapsed}s)")

    # Download
    try:
        generated_videos = operation.response.generated_videos
        if not generated_videos:
            print(f"  ❌ Empty response — prompt likely blocked or style unsupported")
            print(f"     Raw: {operation.response}")
            return False

        video = generated_videos[0]
        client.files.download(file=video.video)
        video.video.save(str(output_path))

        if not output_path.exists():
            print("  ❌ File not saved")
            return False

        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  🎉 Saved: {output_path.name} ({size_mb:.2f} MB)")
        return True

    except Exception as e:
        print(f"  ❌ Download failed: {type(e).__name__}: {e}")
        return False


def main():
    # ── Env + SDK ─────────────────────────────────────────────────────
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ API key not found. Set GEMINI_API_KEY or GOOGLE_API_KEY in .env")
        sys.exit(1)

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("❌ google-genai not installed. Run: pip install google-genai")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    print(f"✅ Client ready ({api_key[:6]}...{api_key[-4:]})")
    print(f"\nTesting {len(PROMPTS)} whiteboard prompt strategies...")

    # ── Run both prompts ──────────────────────────────────────────────
    results = {}
    for key, config in PROMPTS.items():
        results[key] = generate_video(client, types, key, config)

    # ── Summary ───────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  RESULTS SUMMARY")
    print(f"{'='*60}")
    for key, config in PROMPTS.items():
        status = "✅ SUCCESS" if results[key] else "❌ FAILED"
        print(f"  {status}  {config['label']}")

    any_success = any(results.values())
    if any_success:
        print("\n✅ Veo CAN produce whiteboard-style — Option A is viable!")
    else:
        print("\n⚠️  Veo could not produce whiteboard style — will need Option B (post-processing)")

    sys.exit(0 if any_success else 1)


if __name__ == "__main__":
    main()
