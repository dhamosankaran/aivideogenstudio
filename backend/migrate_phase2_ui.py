"""
Database migration script to add Phase 2 UI fields.

Adds columns for:
- Content curation (Article model)
- Script review (Script model)
- Video validation (Video model)
"""

import sqlite3
from pathlib import Path
import os

# Database path - go up one level from backend to project root
BACKEND_DIR = Path(__file__).parent
PROJECT_ROOT = BACKEND_DIR.parent
DB_PATH = PROJECT_ROOT / "backend" / "data" / "app.db"


def migrate():
    """Run database migration."""
    print("🔄 Starting database migration...")
    print(f"📁 Database: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Article table - Content curation fields
        print("\n📝 Adding content curation fields to articles table...")
        
        try:
            cursor.execute("""
                ALTER TABLE articles 
                ADD COLUMN suggested_content_type VARCHAR
            """)
            print("  ✅ Added suggested_content_type")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("  ⏭️  suggested_content_type already exists")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE articles 
                ADD COLUMN selected_at TIMESTAMP
            """)
            print("  ✅ Added selected_at")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("  ⏭️  selected_at already exists")
            else:
                raise
        
        # Script table - Publishing metadata (Phase 1)
        print("\n📝 Adding publishing metadata to scripts table...")
        
        for column, col_type in [
            ("catchy_title", "VARCHAR"),
            ("content_type", "VARCHAR"),
            ("video_description", "TEXT"),
            ("hashtags", "JSON")
        ]:
            try:
                cursor.execute(f"""
                    ALTER TABLE scripts 
                    ADD COLUMN {column} {col_type}
                """)
                print(f"  ✅ Added {column}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"  ⏭️  {column} already exists")
                else:
                    raise
        
        # Script table - Review fields (Phase 2)
        print("\n📝 Adding script review fields to scripts table...")
        
        for column, col_type in [
            ("script_status", "VARCHAR"),
            ("reviewed_at", "TIMESTAMP"),
            ("rejection_reason", "TEXT")
        ]:
            try:
                cursor.execute(f"""
                    ALTER TABLE scripts 
                    ADD COLUMN {column} {col_type}
                """)
                print(f"  ✅ Added {column}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"  ⏭️  {column} already exists")
                else:
                    raise
        
        # Video table - Publishing metadata (Phase 1)
        print("\n📝 Adding publishing metadata to videos table...")
        
        for column, col_type in [
            ("thumbnail_path", "VARCHAR"),
            ("end_screen_path", "VARCHAR"),
            ("youtube_title", "VARCHAR"),
            ("youtube_description", "TEXT")
        ]:
            try:
                cursor.execute(f"""
                    ALTER TABLE videos 
                    ADD COLUMN {column} {col_type}
                """)
                print(f"  ✅ Added {column}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"  ⏭️  {column} already exists")
                else:
                    raise
        
        # Video table - Validation fields (Phase 2)
        print("\n📝 Adding video validation fields to videos table...")
        
        for column, col_type in [
            ("validation_status", "VARCHAR"),
            ("approved_at", "TIMESTAMP"),
            ("rejection_reason", "TEXT"),
            ("uploaded_to_youtube", "BOOLEAN"),
            ("youtube_url", "VARCHAR"),
            ("youtube_video_id", "VARCHAR")
        ]:
            try:
                cursor.execute(f"""
                    ALTER TABLE videos 
                    ADD COLUMN {column} {col_type}
                """)
                print(f"  ✅ Added {column}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"  ⏭️  {column} already exists")
                else:
                    raise
        
        # Set default values for existing records
        print("\n📝 Setting default values for existing records...")
        
        cursor.execute("""
            UPDATE scripts 
            SET content_type = 'daily_update', 
                script_status = 'pending'
            WHERE content_type IS NULL
        """)
        print(f"  ✅ Updated {cursor.rowcount} scripts with default content_type and script_status")
        
        cursor.execute("""
            UPDATE videos 
            SET validation_status = 'pending',
                uploaded_to_youtube = 0
            WHERE validation_status IS NULL
        """)
        print(f"  ✅ Updated {cursor.rowcount} videos with default validation_status")
        
        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
