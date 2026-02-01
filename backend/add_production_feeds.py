#!/usr/bin/env python3
"""
Add Production RSS Feeds

Adds curated AI news RSS feeds for production video generation.
"""

import requests
import sys

BASE_URL = "http://localhost:8000/api"

PRODUCTION_FEEDS = [
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "description": "Latest AI news from TechCrunch"
    },
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
        "description": "AI coverage from The Verge"
    },
    {
        "name": "MIT Technology Review AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
        "description": "In-depth AI analysis from MIT"
    },
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
        "description": "AI business and startup news"
    },
    {
        "name": "Ars Technica AI",
        "url": "https://arstechnica.com/tag/artificial-intelligence/feed/",
        "description": "Technical AI coverage"
    }
]

def add_feeds():
    """Add production feeds to database"""
    print("🔍 Checking existing feeds...")
    
    # Get existing feeds
    resp = requests.get(f"{BASE_URL}/feeds")
    resp.raise_for_status()
    existing_feeds = resp.json()
    existing_urls = {feed["url"] for feed in existing_feeds}
    
    print(f"   Found {len(existing_feeds)} existing feeds")
    
    # Add new feeds
    added = 0
    skipped = 0
    
    for feed_data in PRODUCTION_FEEDS:
        if feed_data["url"] in existing_urls:
            print(f"⏭️  Skipping: {feed_data['name']} (already exists)")
            skipped += 1
            continue
        
        print(f"➕ Adding: {feed_data['name']}")
        resp = requests.post(f"{BASE_URL}/feeds", json={
            "url": feed_data["url"],
            "name": feed_data["name"]
        })
        
        if resp.status_code == 200:
            feed = resp.json()
            print(f"   ✅ Added feed ID: {feed['id']}")
            added += 1
        else:
            print(f"   ❌ Failed: {resp.status_code} - {resp.text}")
    
    print(f"\n📊 Summary:")
    print(f"   Added: {added}")
    print(f"   Skipped: {skipped}")
    print(f"   Total feeds: {len(existing_feeds) + added}")
    
    return added

def fetch_all_feeds():
    """Trigger fetch for all feeds"""
    print("\n🔄 Fetching articles from all feeds...")
    
    resp = requests.get(f"{BASE_URL}/feeds")
    feeds = resp.json()
    
    for feed in feeds:
        print(f"   Fetching: {feed['name']}...")
        try:
            resp = requests.post(f"{BASE_URL}/feeds/{feed['id']}/fetch")
            resp.raise_for_status()
            print(f"   ✅ Fetched")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    print("\n✅ All feeds fetched")

def main():
    print("=" * 60)
    print("🚀 Adding Production RSS Feeds")
    print("=" * 60)
    
    try:
        added = add_feeds()
        
        if added > 0:
            fetch_all_feeds()
        
        print("\n✅ Production feeds ready!")
        print("\nNext steps:")
        print("1. Run: curl -X POST http://localhost:8000/api/articles/analyze")
        print("2. Check dashboard: http://localhost:5173")
        print("3. Generate videos from analyzed articles")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
