"""
Migration: Add Phase 3 columns to youtube_sources table.

Adds: platform, downloaded_path, transcript_source, transcript_segments, scene_summaries.

Run with:
    cd backend && python -m app.migrations.add_phase3_columns
"""

import sqlite3
import sys
from pathlib import Path


DB_PATH = Path("data/app.db")


def migrate():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}. Skipping migration.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Get existing columns
    cursor.execute("PRAGMA table_info(youtube_sources)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    new_columns = [
        ("platform", "TEXT DEFAULT 'youtube'"),
        ("downloaded_path", "TEXT"),
        ("transcript_source", "TEXT"),
        ("transcript_segments", "TEXT"),  # JSON stored as text in SQLite
        ("scene_summaries", "TEXT"),  # JSON stored as text in SQLite
    ]

    added = []
    for col_name, col_type in new_columns:
        if col_name not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE youtube_sources ADD COLUMN {col_name} {col_type}")
                added.append(col_name)
                print(f"  ✅ Added column: {col_name}")
            except sqlite3.OperationalError as e:
                print(f"  ⚠️  Could not add {col_name}: {e}")
        else:
            print(f"  ⏭️  Column already exists: {col_name}")

    conn.commit()
    conn.close()

    if added:
        print(f"\n✅ Migration complete. Added {len(added)} columns: {', '.join(added)}")
    else:
        print("\n✅ All columns already exist. No migration needed.")


if __name__ == "__main__":
    print("Running Phase 3 migration...")
    migrate()
