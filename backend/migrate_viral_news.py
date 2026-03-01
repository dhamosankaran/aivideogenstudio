"""
Migration script for Viral News feature.

Creates the viral_news_sources table and adds viral_news_source_id FK to articles.
"""

import sqlite3
import os
import sys

# Canonical database — single source of truth for the entire application
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "app.db")


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ── 1. Create viral_news_sources table ──

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS viral_news_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url VARCHAR UNIQUE NOT NULL,
            title VARCHAR NOT NULL,
            source_name VARCHAR,
            published_at DATETIME,
            description TEXT,
            content_preview TEXT,
            image_url VARCHAR,
            news_category VARCHAR,
            virality_score FLOAT,
            virality_reasons JSON,
            suggested_angles JSON,
            key_facts JSON,
            target_audience VARCHAR,
            emotional_hook VARCHAR,
            analysis_status VARCHAR DEFAULT 'pending',
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            analyzed_at DATETIME
        )
    """)
    print("✅ Created viral_news_sources table")

    # ── 2. Add FK column to articles ──

    # Check if column already exists
    cursor.execute("PRAGMA table_info(articles)")
    columns = [col[1] for col in cursor.fetchall()]

    if "viral_news_source_id" not in columns:
        cursor.execute(
            "ALTER TABLE articles ADD COLUMN viral_news_source_id INTEGER REFERENCES viral_news_sources(id)"
        )
        print("✅ Added viral_news_source_id column to articles table")
    else:
        print("ℹ️  viral_news_source_id column already exists")

    # ── 3. Create index for fast lookups ──

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS ix_viral_news_sources_original_url ON viral_news_sources(original_url)"
    )
    print("✅ Created index on viral_news_sources.original_url")

    conn.commit()
    conn.close()
    print("\n🎉 Viral News migration complete!")


if __name__ == "__main__":
    migrate()
