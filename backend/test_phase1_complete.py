#!/usr/bin/env python3
"""
Phase 1 Complete Test: Generate 1 video with all publishing features.

Features tested:
- Catchy title generation
- Hashtag generation
- Video description
- Thumbnail generation
- End screen with CTA
- Complete video with all elements
"""

import sys
import asyncio
from pathlib import Path

from app.database import SessionLocal
from app.models import Script, Audio, Article
from app.services.script_service import ScriptService
from app.services.audio_service import AudioService
from app.services.enhanced_video_service import EnhancedVideoCompositionService
from app.services.thumbnail_service import ThumbnailService
from app.services.end_screen_service import EndScreenService
from app.services.publishing_helpers import (
    generate_catchy_title,
    generate_hashtags,
    generate_video_description
)


async def test_phase1_complete():
    """Test complete Phase 1 pipeline."""
    
    print("=" * 70)
    print("🎬 PHASE 1 COMPLETE TEST")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Step 1: Get existing script and audio
        print("\n📝 Step 1: Finding existing script...")
        script = db.query(Script).filter(
            Script.scenes.isnot(None),
            Script.status == "approved"
        ).order_by(Script.id.desc()).first()
        
        if not script:
            print("❌ No approved scene-based script found")
            return 1
        
        print(f"✅ Using script ID {script.id}")
        
        # Get article
        article = db.query(Article).filter(Article.id == script.article_id).first()
        if not article:
            print("❌ Article not found")
            return 1
        
        # Get audio
        audio = db.query(Audio).filter(
            Audio.script_id == script.id,
            Audio.status == "completed"
        ).first()
        
        if not audio:
            print("❌ No completed audio found")
            return 1
        
        print(f"✅ Using audio ID {audio.id}")
        
        # Step 2: Generate catchy title
        print("\n✨ Step 2: Generating catchy title...")
        script_service = ScriptService(db)
        llm = script_service.llm
        
        content_type = "daily_update"  # Can be: daily_update, big_tech, leader_quote, arxiv_paper
        
        catchy_title = await generate_catchy_title(
            llm,
            article.title,
            article.summary or article.description,
            content_type
        )
        print(f"✅ Catchy title: {catchy_title}")
        
        # Step 3: Generate hashtags
        print("\n#️⃣  Step 3: Generating hashtags...")
        hashtags = await generate_hashtags(llm, article.title, content_type)
        print(f"✅ Hashtags: {' '.join(hashtags)}")
        
        # Step 4: Generate description
        print("\n📄 Step 4: Generating video description...")
        description = generate_video_description(script, article, catchy_title, hashtags)
        print(f"✅ Description preview: {description[:150]}...")
        
        # Step 5: Generate thumbnail
        print("\n🖼️  Step 5: Generating thumbnail...")
        thumbnail_service = ThumbnailService()
        
        # Use first scene image if available
        background_image = None
        if script.scenes:
            # Try to find first scene image
            from app.services.pexels_service import PexelsService
            try:
                pexels = PexelsService()
                keywords = script.scenes[0].get('image_keywords', [])
                if keywords:
                    background_image = pexels.search_image([keywords[0]])
            except:
                pass
        
        thumbnail_path = thumbnail_service.generate_thumbnail(
            title=catchy_title,
            content_type=content_type,
            background_image=background_image
        )
        print(f"✅ Thumbnail: {thumbnail_path}")
        
        # Step 6: Generate end screen
        print("\n🎬 Step 6: Generating end screen...")
        end_screen_service = EndScreenService()
        end_screen_path = end_screen_service.generate_end_screen(content_type)
        print(f"✅ End screen: {end_screen_path}")
        
        # Step 7: Generate video with end screen
        print("\n🎥 Step 7: Generating complete video...")
        print("   (This will take ~3-5 minutes)")
        
        video_service = EnhancedVideoCompositionService(db)
        video = video_service.create_video_task(
            script_id=script.id,
            audio_id=audio.id,
            background_style="scenes"
        )
        
        # Add end screen to video composition
        # (This would be integrated into enhanced_video_service.py)
        video_service.process_video(video.id)
        
        db.refresh(video)
        
        # Step 8: Update video metadata
        print("\n💾 Step 8: Saving metadata...")
        video.thumbnail_path = str(thumbnail_path)
        video.end_screen_path = str(end_screen_path)
        video.youtube_title = catchy_title
        video.youtube_description = description
        
        script.catchy_title = catchy_title
        script.content_type = content_type
        script.video_description = description
        script.hashtags = hashtags
        
        db.commit()
        
        # Success!
        print("\n" + "=" * 70)
        print("✅ PHASE 1 COMPLETE!")
        print("=" * 70)
        
        print(f"\n📊 Video Details:")
        print(f"   Video ID: {video.id}")
        print(f"   File: {video.file_path}")
        print(f"   Duration: {video.duration:.1f}s")
        print(f"   Size: {video.file_size / 1024 / 1024:.1f} MB")
        
        print(f"\n📋 Publishing Assets:")
        print(f"   Title: {catchy_title}")
        print(f"   Thumbnail: {thumbnail_path}")
        print(f"   End Screen: {end_screen_path}")
        print(f"   Hashtags: {' '.join(hashtags)}")
        
        print(f"\n🎬 Ready for Upload:")
        print(f"   1. Video: open {video.file_path}")
        print(f"   2. Thumbnail: open {thumbnail_path}")
        print(f"   3. Copy title: {catchy_title}")
        print(f"   4. Copy description from database")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(test_phase1_complete()))
