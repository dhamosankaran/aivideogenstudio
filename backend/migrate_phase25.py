"""
Migration script for Phase 2.5 Enhancement.

Adds new columns to support YouTube Shorts enhancement:
- YouTubeSource.video_summary
- YouTubeSource.summary_generated_at
- Article.creation_mode
- Article.clip_path

Run with: python migrate_phase25.py
"""

import sqlite3
from pathlib import Path


def migrate():
    """Add Phase 2.5 columns to the database."""
    
    # Find database file - use the correct path from config
    db_path = Path(__file__).parent / "data" / "app.db"
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return False
    
    print(f"Migrating database: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    migrations = [
        # YouTubeSource columns
        ("youtube_sources", "video_summary", "TEXT"),
        ("youtube_sources", "summary_generated_at", "DATETIME"),
        
        # Article columns
        ("articles", "creation_mode", "VARCHAR(10)"),
        ("articles", "clip_path", "VARCHAR(500)"),
    ]
    
    for table, column, col_type in migrations:
        try:
            # Check if column exists first
            cursor.execute(f"PRAGMA table_info({table})")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            if column in existing_columns:
                print(f"  ✓ {table}.{column} already exists")
            else:
                # Add the column
                sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
                cursor.execute(sql)
                print(f"  + Added {table}.{column}")
                
        except sqlite3.OperationalError as e:
            print(f"  ✗ Error with {table}.{column}: {e}")
    
    conn.commit()
    conn.close()
    
    print("\nMigration complete!")
    return True


if __name__ == "__main__":
    migrate()
