from app.database import SessionLocal
from app.models import Video, Script

def inspect_db():
    db = SessionLocal()
    try:
        print("\n=== SCRIPTS ===")
        scripts = db.query(Script).all()
        for s in scripts:
            print(f"Script ID: {s.id} | Status: {s.status} | Title: {s.catchy_title or 'Untitled'}")

        print("\n=== VIDEOS ===")
        videos = db.query(Video).all()
        for v in videos:
            print(f"Video ID: {v.id} | Script ID: {v.script_id} | Status: {v.status}")
            
    finally:
        db.close()

if __name__ == "__main__":
    inspect_db()
