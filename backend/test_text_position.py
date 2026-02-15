#!/usr/bin/env python3
"""
Quick test for text overlay fix.

Creates a minimal video with subtitles to verify:
1. Text appears only at bottom (y=85%)
2. No duplicate text at top
3. Font and stroke look correct

Expected: Single word at bottom of frame, no duplicate.
"""

import sys
from pathlib import Path
from moviepy import (
    TextClip,
    ColorClip,
    CompositeVideoClip,
)

def test_text_position():
    """Create a test video to verify text positioning."""
    
    print("=" * 50)
    print("Testing Text Overlay Positioning")
    print("=" * 50)
    
    # Video dimensions (YouTube Shorts portrait)
    w, h = 1080, 1920
    duration = 3  # seconds
    
    # Create background
    bg_clip = ColorClip(size=(w, h), color=(31, 41, 55), duration=duration)
    
    # Calculate absolute Y position (same as in enhanced_video_service.py)
    y_position = int(h * 0.85)  # 1632 pixels from top
    print(f"Y position: {y_position}px (85% from top on {h}px height)")
    
    # Create test text clip with same styling as enhanced_video_service.py
    test_word = "TESTING"
    txt_clip = (
        TextClip(
            text=test_word,
            font_size=72,
            color='white',
            font='/System/Library/Fonts/Supplemental/Arial Bold.ttf',
            stroke_color='black',
            stroke_width=5,
            text_align='center'
        )
        .with_position(('center', y_position))  # Absolute pixel position
        .with_start(0)
        .with_duration(duration)
    )
    
    # Composite
    final = CompositeVideoClip([bg_clip, txt_clip], size=(w, h))
    final = final.with_duration(duration)
    
    # Output
    output_path = Path("data/test_text_position.mp4")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\nRendering test video to: {output_path}")
    final.write_videofile(
        str(output_path),
        fps=30,
        codec='libx264',
        audio=False,
        logger=None
    )
    
    print(f"\n✅ Test video created: {output_path}")
    print(f"   File size: {output_path.stat().st_size / 1024:.1f}KB")
    
    # Create a frame capture for easy verification
    print("\nExtracting frame for visual verification...")
    import subprocess
    frame_path = Path("data/test_text_position_frame.jpg")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(output_path),
        "-ss", "1", "-vframes", "1", "-q:v", "2",
        str(frame_path)
    ], capture_output=True)
    print(f"   Frame saved: {frame_path}")
    
    print("\n" + "=" * 50)
    print("VERIFICATION CHECKLIST:")
    print("=" * 50)
    print("Open data/test_text_position_frame.jpg and verify:")
    print("  [ ] Text 'TESTING' appears near BOTTOM of screen")
    print("  [ ] NO duplicate text at TOP of screen")
    print("  [ ] Text has white color with black stroke")
    print("  [ ] Text is centered horizontally")
    print("=" * 50)
    
    return output_path


if __name__ == "__main__":
    test_text_position()
