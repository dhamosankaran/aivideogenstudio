import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env before imports to ensure settings are correct
load_dotenv()

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

from app.services.book_service import BookService
from app.database import SessionLocal
from app.config import settings
from app.providers.google_tts_provider import GoogleTTSProvider

async def check_services():
    print("--- Google Services Check ---")
    
    # 1. Check API Keys
    google_api_key = settings.google_api_key
    books_key = os.getenv("GOOGLE_BOOKS_API_KEY")
    
    print(f"GOOGLE_API_KEY in settings: {'Found' if google_api_key else 'Missing'}")
    print(f"GOOGLE_BOOKS_API_KEY in env: {'Found' if books_key else 'Missing'}")
    
    key_to_use = books_key or google_api_key
    
    # 2. Check Google Books API
    print("\n[Testing Google Books API]")
    if key_to_use:
        try:
            db = SessionLocal()
            service = BookService(db, google_books_api_key=key_to_use)
            print(f"Using key: {key_to_use[:5]}...{key_to_use[-5:]}")
            
            # Search for "Atomic Habits" using Google Books (fallback)
            results = await service._search_google_books("Atomic Habits", limit=1)
            
            if results:
                print(f"✅ Google Books API Successful. Found: {results[0]['title']}")
            else:
                print("⚠️ Google Books API returned no results.")
        except Exception as e:
            print(f"❌ Google Books API Failed: {e}")
        finally:
            db.close()
    else:
        print("❌ No Google API Key found for Books API.")

    # 3. Check Google TTS API
    print("\n[Testing Google TTS API]")
    if google_api_key:
        try:
            tts = GoogleTTSProvider(api_key=google_api_key)
            print("Attempting to synthesize speech (expecting failure if API not enabled)...")
            await tts.synthesize_speech("Hello, this is a test.", "mp3")
            print("✅ Google TTS API Successful (Unexpected!)")
        except Exception as e:
            print(f"❌ Google TTS API Validation Failed: {e}")
            if "has not been used in project" in str(e) or "disabled" in str(e):
                print("   -> Confirmed: API is disabled or restricted.")
    else:
        print("Skipping Google TTS test (no key).")

if __name__ == "__main__":
    asyncio.run(check_services())
