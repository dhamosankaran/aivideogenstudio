"""
Migration: Add youtube_tags column to videos table.

Run from backend directory:
    python3 migrations/add_youtube_tags.py
"""

import sqlite3
import sys
import os
from pathlib import Path

# Resolve DB path
DB_PATH = Path("data/app.db")

def migrate():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}. Skipping migration (it will be created with the column).")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(videos)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "youtube_tags" in columns:
        print("✅ Column 'youtube_tags' already exists. No migration needed.")
        conn.close()
        return
    
    # Add the column
    cursor.execute("ALTER TABLE videos ADD COLUMN youtube_tags TEXT")
    conn.commit()
    
    print("✅ Added 'youtube_tags' column to 'videos' table successfully.")
    
    # Verify
    cursor.execute("PRAGMA table_info(videos)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "youtube_tags" in columns, "Migration verification failed!"
    print(f"   Verified: {len(columns)} columns in videos table.")
    
    conn.close()


if __name__ == "__main__":
    migrate()
