#!/usr/bin/env python3
"""
Test Elon Musk Short Generation
"""

import sys
import asyncio
import logging
from app.database import SessionLocal
from app.services.news_api_service import NewsAPIService
from app.services.script_service import ScriptService
from app.services.enhanced_video_service import EnhancedVideoCompositionService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_elon_short():
    print("=" * 70)
    print("🚀 TESTING ELON MUSK SHORT GENERATION")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Step 1: Search for Elon Musk articles
        print("\n🔍 Step 1: Searching NewsAPI for 'Elon Musk'...")
        news_service = NewsAPIService()
        # Search specifically for Elon Musk content
        results = news_service.search_articles(
            query='"Elon Musk" OR "Tesla" OR "SpaceX"',
            language="en",
            sort_by="relevancy",
            page_size=10
        )
        
        if not results['articles']:
            print("❌ No articles found!")
            return 1
            
        print(f"✅ Found {results['total_results']} articles")
        
        # Step 2: Import the top article
        print("\n📥 Step 2: Importing top article...")
        top_article = results['articles'][0]
        print(f"   Title: {top_article['title']}")
        print(f"   Source: {top_article['source']['name']}")
        
        import_stats = news_service.import_articles_to_db([top_article], db, source_name="NewsAPI")
        
        # Get the imported article from DB
        from app.models import Article
        article = db.query(Article).filter(Article.title == top_article['title']).first()
        
        if not article:
            print("❌ Failed to retrieve imported article")
            return 1
            
        print(f"✅ Article imported (ID: {article.id})")
        
        # Step 3: Generate Script (Big Tech style)
        print("\n📝 Step 3: Generating 'Big Tech' script (45-60s)...")
        script_service = ScriptService(db)
        
        # Generate script using existing service method
        script = await script_service.generate_script(
            article=article,
            style="engaging",  # Will use big_tech prompt flavor
            target_duration=50 # Perfect for Shorts
        )
        
        if not script:
            print("❌ Script generation failed")
            return 1
            
        print(f"✅ Script generated (ID: {script.id})")
        
        # Manually approve the script (simulating UI approval)
        script.status = "approved"
        # Set content type to big_tech for styling
        script.content_type = "big_tech" 
        db.commit()
        
        print("\n👀 Script Preview:")
        print("-" * 30)
        # Parse scenes if stored as string, though usually JSON
        import json
        scenes = script.scenes
        if isinstance(scenes, str):
            scenes = json.loads(scenes)
            
        if scenes:
            print(f"DEBUG: scenes type: {type(scenes)}")
            if isinstance(scenes, list) and len(scenes) > 0:
                print(f"DEBUG: first scene: {scenes[0]}")
            
            for i, scene in enumerate(scenes[:3]):
                if not isinstance(scene, dict):
                    print(f"Scene {i+1}: (Invalid scene format: {scene})")
                    continue
                    
                narration = scene.get('narration')
                if narration:
                    print(f"Scene {i+1}: {narration[:50]}...")
                else:
                    print(f"Scene {i+1}: (No narration found)")
        print("-" * 30)
        
        # Step 4: Generate Video
        print("\n🎥 Step 4: Generating Video (this takes 2-3 mins)...")
        
        # Note: In the real app, we'd use script_service.generate_video_from_script
        # but here we'll use enhanced_video_service directly to have more control/visibility
        # mimicking the background task
        
        # First generate the TTS audio using the script service helper or directly calling audio service
        # Let's use the provided method which does both audio + video
        result = await script_service.generate_video_from_script(script.id)
        
        if result['status'] != 'success':
            print(f"❌ Video generation failed: {result.get('error')}")
            return 1
            
        video_id = result['video_id']
        print(f"✅ Video output generated (ID: {video_id})")
        
        # Get the video object
        from app.models import Video
        video = db.query(Video).filter(Video.id == video_id).first()
        
        print("\n" + "=" * 70)
        print("🎉 SUCCESS! ELON SHORT GENERATED")
        print("=" * 70)
        print(f"📂 File: {video.file_path}")
        print(f"⏱️ Duration: {video.duration}s")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(asyncio.run(generate_elon_short()))
