from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

DB_URL = "sqlite:///./data/app.db"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    print("Checking database state...")
    
    # Check feeds
    result = session.execute(text("SELECT count(*) FROM feeds"))
    feed_count = result.scalar()
    print(f"Feeds: {feed_count}")
    
    # Check articles
    result = session.execute(text("SELECT count(*) FROM articles"))
    article_count = result.scalar()
    print(f"Articles: {article_count}")
    
    # Check scripts
    result = session.execute(text("SELECT count(*) FROM scripts"))
    script_count = result.scalar()
    print(f"Scripts: {script_count}")
    
    # Check audio
    try:
        result = session.execute(text("SELECT count(*) FROM audio"))
        audio_count = result.scalar()
        print(f"Audio: {audio_count}")
    except Exception as e:
        print("Audio table might not exist yet")

finally:
    session.close()
