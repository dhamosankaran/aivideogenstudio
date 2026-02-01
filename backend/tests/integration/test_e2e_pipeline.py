
import pytest
import os
from datetime import datetime
from pathlib import Path

from app.models import Article, Feed
from app.services.script_service import ScriptService
from app.services.audio_service import AudioService
from app.services.enhanced_video_service import EnhancedVideoCompositionService

# Mark as integration test
pytestmark = pytest.mark.asyncio

async def test_full_video_generation_pipeline(db):
    """
    Test the full pipeline from Article -> Script -> Audio -> Video.
    We skip the RSS fetch step to avoid external dependencies, injecting a dummy article instead.
    """
    print("\n🚀 Starting E2E Integration Test...")

    # 1. SETUP: Create Dummy Feed & Article
    print("Step 1: Creating Dummy Dummy Data...")
    feed = Feed(name="Test Feed", url="http://test.com/rss", is_active=True)
    db.add(feed)
    db.commit()

    article = Article(
        feed_id=feed.id,
        title="Future of AI in 2026: What to Expect",
        url="http://test.com/ai-2026",
        description="Artificial Intelligence is evolving rapidly. Here are the key trends for 2026 including AGI and robotics.",
        content="Artificial Intelligence is evolving rapidly. Key trends include AGI, robotics, and personalized assistants.",
        published_at=datetime.utcnow(),
        # Pre-calculated analysis to skip LLM analysis step cost if needed, 
        # but we let ScriptService handle it to test that integration too if we want.
        # For this test, we assume ScriptService will generate the script.
        suggested_content_type="daily_update"
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    assert article.id is not None
    print(f"✅ Article created: ID {article.id}")

    # 2. GENERATE SCRIPT
    print("Step 2: Generating Script...")
    script_service = ScriptService(db)
    # Using 'engaging' style. This calls the LLM (Real Cost ~$0.01)
    script = await script_service.generate_script(article, style="engaging")
    
    assert script.id is not None
    assert script.status == "generated" # Or whatever default is, verified in service
    assert len(script.scenes) > 0
    print(f"✅ Script generated: ID {script.id} with {len(script.scenes)} scenes")

    # Approve script manually for the pipeline to proceed
    script.status = "approved"
    db.commit()

    # 3. GENERATE AUDIO
    print("Step 3: Generating Audio...")
    audio_service = AudioService(db)
    # Using 'google' or 'openai'. Google is cheaper/faster for tests usually, or use what's configured.
    # We'll use 'google' as it was used in manual tests.
    try:
        audio = await audio_service.generate_audio_from_script(
            script_id=script.id,
            tts_provider="google",
            voice="en-US-Neural2-H" 
        )
    except Exception as e:
        print(f"⚠️ Google TTS failed, trying generic fallback? Error: {e}")
        raise e

    assert audio.id is not None
    assert audio.status == "completed"
    assert os.path.exists(audio.file_path)
    print(f"✅ Audio generated: ID {audio.id} ({audio.duration:.1f}s)")

    # 4. GENERATE VIDEO
    print("Step 4: Generating Video...")
    video_service = EnhancedVideoCompositionService(db)
    
    # Create Task
    video_task = video_service.create_video_task(
        script_id=script.id,
        audio_id=audio.id,
        background_style="scenes" # Tests Pexels integration
    )
    assert video_task.id is not None
    
    # Process (Render)
    # This might take time (30-60s)
    video_service.process_video(video_task.id)
    
    # Refresh to check status
    db.refresh(video_task)
    
    assert video_task.status == "completed"
    assert video_task.file_path is not None
    assert os.path.exists(video_task.file_path)
    assert video_task.duration > 0
    
    print(f"✅ Video generated: ID {video_task.id}")
    print(f"   Path: {video_task.file_path}")
    print(f"   Size: {video_task.file_size / 1024 / 1024:.2f} MB")

    # 5. CLEANUP (Optional - files)
    # db fixture handles DB cleanup, but files remain in data/
    # We might leave them for manual inspection or delete them.
    # For now, leaving them is useful for debugging.
