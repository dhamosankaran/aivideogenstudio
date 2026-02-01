from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

from app.models import Base, Feed, Article, Script, Audio
from app.database import get_db

# Connect to database
DB_URL = "sqlite:///./data/app.db"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    print("🌱 Seeding database with test data...")
    
    # 1. Create a Test Feed
    feed = session.query(Feed).filter_by(url="https://test.com/rss").first()
    if not feed:
        feed = Feed(
            name="Test Feed",
            url="https://test.com/rss",
            category="test",
            is_active=True
        )
        session.add(feed)
        session.commit()
        print(f"✅ Created feed: {feed.name}")
    else:
        print(f"ℹ️ Feed exists: {feed.name}")
        
    # 2. Create a Test Article
    article = session.query(Article).filter_by(url="https://test.com/article1").first()
    if not article:
        article = Article(
            feed_id=feed.id,
            title="AI Revolutionizes Video Generation",
            url="https://test.com/article1",
            content="Artificial Intelligence is changing how we create videos. New tools allow automatic script generation and text-to-speech synthesis.",
            published_at=datetime.utcnow(),
            recency_score=0.9,
            relevance_score=0.95,
            engagement_score=0.9,
            uniqueness_score=0.8,
            final_score=0.9,
            is_processed=True
        )
        session.add(article)
        session.commit()
        print(f"✅ Created article: {article.title}")
    else:
        print(f"ℹ️ Article exists: {article.title}")
        
    # 3. Create an Approved Script
    script = session.query(Script).filter_by(article_id=article.id).first()
    if not script:
        script = Script(
            article_id=article.id,
            raw_script="[HOOK] AI is changing everything. [BODY] New tools allow automatic video creation. It is amazing. [CTA] Subscribe for more.",
            formatted_script="AI is changing everything. New tools allow automatic video creation. It is amazing. Subscribe for more.",
            word_count=20,
            estimated_duration=8.0,
            style="engaging",
            status="approved",  # IMPORTANT: Must be approved for audio generation
            is_valid=True
        )
        session.add(script)
        session.commit()
        print(f"✅ Created approved script ID: {script.id}")
    else:
        print(f"ℹ️ Script exists ID: {script.id} (Status: {script.status})")
        # Ensure it's approved
        if script.status != "approved":
            script.status = "approved"
            session.commit()
            print("  - Updated script status to 'approved'")

    # 4. Verify Data State
    print("\n📊 Database State:")
    print(f"  - Feeds: {session.query(Feed).count()}")
    print(f"  - Articles: {session.query(Article).count()}")
    print(f"  - Scripts: {session.query(Script).count()}")
    
    current_audio = session.query(Audio).count()
    print(f"  - Audio Files: {current_audio}")
    
    print(f"\n🚀 Ready to test. Use Script ID: {script.id}")

except Exception as e:
    print(f"❌ Error: {e}")
    session.rollback()
finally:
    session.close()
