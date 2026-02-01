
import sys
import os
import asyncio
import logging

# Add app to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.services.script_service import ScriptService, process_video_background_task
from app.models import Script

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_video_generation_flow():
    db = SessionLocal()
    try:
        # 1. Find an approved script or create one
        script = db.query(Script).filter(Script.status == "approved").first()
        if not script:
            # Try to find a generated script and approve it
            script = db.query(Script).filter(Script.status == "generated").first()
            if script:
                service = ScriptService(db)
                service.approve_script(script.id)
                print(f"Approved script {script.id}")
            else:
                print("No suitable script found")
                return

        print(f"Testing video generation for script {script.id}")
        
        # 2. Run the background task logic synchronously
        # We call the service method directly to see exceptions
        service = ScriptService(db)
        
        print("Starting asyncio loop...")
        try:
             asyncio.run(service.generate_video_from_script(script.id))
             print("Video generation successful")
        except Exception as e:
            print(f"Video generation failed: {e}")
            import traceback
            traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    test_video_generation_flow()
