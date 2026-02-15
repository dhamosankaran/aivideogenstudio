"""
Clear all book review records from the database for a fresh start.

Usage:
    cd backend
    python3 clear_book_data.py

This script removes all book-related records:
- Videos linked to book review articles
- Scripts linked to book review articles
- Articles with content_type 'book_review'
- BookSource records
- Cached images in data/images/book_reviews/
"""

import sys
import os
import shutil
from pathlib import Path

# Add parent dir to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import BookSource, Article, Script, Video


def clear_book_data():
    """Remove all book review records and cached images."""
    db = SessionLocal()
    
    try:
        # 1. Find all book review articles
        book_articles = db.query(Article).filter(
            Article.suggested_content_type == "book_review"
        ).all()
        
        article_ids = [a.id for a in book_articles]
        print(f"Found {len(article_ids)} book review articles")
        
        if article_ids:
            # 2. Delete videos linked to book review scripts
            scripts = db.query(Script).filter(Script.article_id.in_(article_ids)).all()
            script_ids = [s.id for s in scripts]
            
            if script_ids:
                video_count = db.query(Video).filter(Video.script_id.in_(script_ids)).delete(synchronize_session='fetch')
                print(f"  Deleted {video_count} videos")
            
            # 3. Delete scripts
            script_count = db.query(Script).filter(Script.article_id.in_(article_ids)).delete(synchronize_session='fetch')
            print(f"  Deleted {script_count} scripts")
            
            # 4. Delete articles
            article_count = db.query(Article).filter(Article.id.in_(article_ids)).delete(synchronize_session='fetch')
            print(f"  Deleted {article_count} articles")
        
        # 5. Delete all BookSource records
        book_count = db.query(BookSource).delete(synchronize_session='fetch')
        print(f"  Deleted {book_count} book sources")
        
        db.commit()
        print("✅ Database records cleared successfully")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error clearing database: {e}")
        raise
    finally:
        db.close()
    
    # 6. Clear cached images
    cache_dirs = [
        Path("data/images/book_reviews"),
        Path("data/images/serper_cache"),  # May contain stale book images
    ]
    
    for cache_dir in cache_dirs:
        if cache_dir.exists():
            file_count = len(list(cache_dir.glob("*.jpg"))) + len(list(cache_dir.glob("*.png")))
            if file_count > 0:
                for f in cache_dir.glob("*.jpg"):
                    f.unlink()
                for f in cache_dir.glob("*.png"):
                    f.unlink()
                print(f"  Cleared {file_count} cached images from {cache_dir}")
    
    # 7. Clear per-book project folders
    projects_dir = Path("data/projects")
    if projects_dir.exists():
        removed = 0
        for subdir in projects_dir.iterdir():
            if subdir.is_dir() and subdir.name[0].isdigit():
                # Looks like a book project folder (starts with numeric ID)
                shutil.rmtree(subdir)
                removed += 1
        if removed:
            print(f"  Removed {removed} book project folders from {projects_dir}")
    
    print("\n🎉 Book review data fully cleared. Ready for fresh generation!")


if __name__ == "__main__":
    confirm = input("This will DELETE all book review data (DB records + cached images). Continue? [y/N] ")
    if confirm.lower() == 'y':
        clear_book_data()
    else:
        print("Aborted.")
