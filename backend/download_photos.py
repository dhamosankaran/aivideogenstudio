#!/usr/bin/env python3
"""
Download Photos for Script Scenes

This script downloads photos from Unsplash for each scene in a generated script.
It uses the image keywords from the scene to find relevant visuals.

Usage:
    python download_photos.py [script_id]
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from app.database import SessionLocal
from app.models import Script
from app.services.unsplash_service import UnsplashService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_directories(script_id: int) -> Path:
    """Create download directory for the script."""
    base_dir = Path(__file__).parent / "assets" / "downloads" / str(script_id)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir

def list_scripts(limit: int = 5):
    """List recent scripts."""
    db = SessionLocal()
    try:
        scripts = db.query(Script).order_by(Script.created_at.desc()).limit(limit).all()
        if not scripts:
            print("No scripts found in database.")
            return

        print(f"\nRecent Scripts:")
        print(f"{'ID':<5} | {'Date':<20} | {'Status':<10} | {'Title'}")
        print("-" * 60)
        for s in scripts:
            title = s.catchy_title or (s.article.title[:40] + "..." if s.article else "Untitled")
            print(f"{s.id:<5} | {s.created_at.strftime('%Y-%m-%d %H:%M'):<20} | {s.status:<10} | {title}")
        print("-" * 60)
    finally:
        db.close()

def download_for_script(script_id: int):
    """Download photos for a specific script."""
    db = SessionLocal()
    unsplash = UnsplashService()
    
    try:
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            logger.error(f"Script {script_id} not found.")
            return

        logger.info(f"Processing Script {script.id}: {script.catchy_title or 'Untitled'}")
        
        # Determine scenes
        scenes = script.scenes
        if not scenes:
            logger.warning("No structured scenes found. Checking raw script...")
            # Fallback parsing logic could go here, but for now we assume structured scenes
            logger.error("Script does not have structured scene data.")
            return

        output_dir = setup_directories(script_id)
        logger.info(f"Downloading to: {output_dir}")

        success_count = 0
        
        for i, scene in enumerate(scenes, 1):
            scene_num = scene.get("scene_number", i)
            keywords = scene.get("image_keywords", [])
            visual_cues = scene.get("visual_cues", "")
            
            # Construct search query
            # Prioritize keywords, fallback to visual cues
            query = " ".join(keywords[:3]) if keywords else visual_cues
            
            logger.info(f"Scene {scene_num}: Searching for '{query}'...")
            
            photos = unsplash.search_photos(query, orientation="landscape", per_page=1)
            
            if photos:
                photo = photos[0]
                photo_id = photo["id"]
                download_url = photo["links"]["download_location"]
                
                # Construct filename
                filename = f"scene_{scene_num:02d}_{photo_id}.jpg"
                filepath = output_dir / filename
                
                # Check if already exists
                if filepath.exists():
                    logger.info(f"   - Already downloaded: {filename}")
                    success_count += 1
                    continue
                
                # Retrieve actual download URL (Unsplash API flow)
                # Note: The search result gives a 'download_location' which we must hit to track the download
                # and get the actual URL.
                
                # For `UnsplashService.download_photo`, we usually need the direct URL. 
                # The 'urls' object in the photo response has direct links for display, 
                # but for download tracking compliance we should fetch from download_location if possible,
                # OR use the 'full'/'regular' url and hit the tracking endpoint separately.
                
                # Let's use the 'regular' URL for quality/size balance and hit tracking separately.
                image_url = photo["urls"]["regular"]
                
                logger.info(f"   - Downloading image...")
                if unsplash.download_photo(image_url, str(filepath)):
                    logger.info(f"   - Saved: {filename}")
                    unsplash.track_download(download_url)
                    success_count += 1
                else:
                    logger.error(f"   - Download failed.")
            else:
                logger.warning(f"   - No photos found for '{query}'")

        print(f"\nSummary: Downloaded {success_count}/{len(scenes)} photos.")
        print(f"Output Directory: {output_dir}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download photos for script scenes")
    parser.add_argument("script_id", nargs="?", type=int, help="ID of the script to process")
    args = parser.parse_args()

    if args.script_id:
        download_for_script(args.script_id)
    else:
        list_scripts()
        print("\nUsage: python download_photos.py <script_id>")
