"""
Migration: Add description column to youtube_sources table.
"""

import sqlite3
import sys
from pathlib import Path


def migrate():
    db_path = Path(__file__).parent.parent / "data" / "app.db"
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(youtube_sources)")
    columns = [col[1] for col in cursor.fetchall()]

    if "description" not in columns:
        cursor.execute("ALTER TABLE youtube_sources ADD COLUMN description TEXT")
        conn.commit()
        print("✓ Added 'description' column to youtube_sources table")
    else:
        print("→ 'description' column already exists, skipping")

    conn.close()


if __name__ == "__main__":
    migrate()
