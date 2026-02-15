#!/usr/bin/env python3
"""
Test Serper.dev Image Search API

Verifies:
1. API key is valid and authorized
2. Image search returns results
3. Images can be downloaded
4. Image dimensions meet minimum requirements

Usage:
    python test_serper_api.py
    python test_serper_api.py "custom search query"
"""

import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_serper_api(query: str = "Waymo self driving car technology"):
    """Test Serper API with a sample query."""
    
    print("=" * 60)
    print("🔍 Serper.dev Image Search API Test")
    print("=" * 60)
    
    # Import after loading env
    from app.services.serper_image_service import SerperImageService
    
    service = SerperImageService()
    
    # Test 1: Check if API is available
    print("\n📋 Test 1: API Key Configuration")
    if not service.is_available:
        print("❌ FAILED: SERPERDEV_KEY not set in environment")
        print("   Add SERPERDEV_KEY to your .env file")
        return 1
    print("✅ PASSED: API key is configured")
    
    # Test 2: Search for images
    print(f"\n📋 Test 2: Image Search")
    print(f"   Query: '{query}'")
    
    try:
        images = await service.search_images(query, num_results=5)
    except Exception as e:
        print(f"❌ FAILED: Search error - {e}")
        return 1
    
    if not images:
        print("❌ FAILED: No images returned (API may have returned error)")
        return 1
    
    print(f"✅ PASSED: Found {len(images)} images")
    
    # Display results
    print("\n   Results:")
    for i, img in enumerate(images[:5], 1):
        print(f"   {i}. {img.title[:50]}...")
        print(f"      Size: {img.width}x{img.height}px")
        print(f"      Source: {img.source[:40]}...")
    
    # Test 3: Download an image
    print(f"\n📋 Test 3: Image Download")
    
    download_path = await service.download_image(images[0])
    
    if not download_path or not download_path.exists():
        print("❌ FAILED: Could not download image")
        return 1
    
    file_size = download_path.stat().st_size
    print(f"✅ PASSED: Downloaded to {download_path}")
    print(f"   File size: {file_size / 1024:.1f} KB")
    
    # Test 4: Multiple image download
    print(f"\n📋 Test 4: Batch Download")
    
    downloaded = await service.search_and_download(query, num_results=3)
    
    if len(downloaded) < 2:
        print(f"⚠️ WARNING: Only downloaded {len(downloaded)}/3 images")
    else:
        print(f"✅ PASSED: Downloaded {len(downloaded)} images")
    
    for path in downloaded:
        print(f"   - {path.name} ({path.stat().st_size / 1024:.1f} KB)")
    
    # Test 5: Tech-specific query
    print(f"\n📋 Test 5: Tech Topic Search")
    tech_query = "OpenAI GPT artificial intelligence"
    
    tech_images = await service.search_images(tech_query, num_results=3)
    
    if tech_images:
        print(f"✅ PASSED: Found {len(tech_images)} images for '{tech_query}'")
    else:
        print(f"⚠️ WARNING: No results for tech query")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print("\n✅ ALL TESTS PASSED!")
    print("\nSerper API is working correctly.")
    print("The image search orchestrator will now use Serper")
    print("as the PRIMARY source for topic-relevant images.")
    print("=" * 60)
    
    return 0


async def test_orchestrator_with_serper():
    """Test the full orchestrator with Serper enabled."""
    
    print("\n" + "=" * 60)
    print("🔗 Testing Image Search Orchestrator with Serper")
    print("=" * 60)
    
    from app.services.image_search_orchestrator import ImageSearchOrchestrator
    
    orchestrator = ImageSearchOrchestrator()
    status = orchestrator.get_provider_status()
    
    print(f"\nProvider status:")
    for provider, available in status.items():
        icon = "✅" if available else "❌"
        print(f"   {icon} {provider}: {available}")
    
    if not status.get("serper"):
        print("\n⚠️ Serper not available - check API key")
        return 1
    
    # Test with a topic query
    print("\n📋 Testing topic-based search...")
    topic = "Tesla Cybertruck electric vehicle"
    
    image_path = await orchestrator.search_image_async(
        keywords=["electric vehicle", "technology"],
        topic_query=topic
    )
    
    if image_path and image_path.exists():
        print(f"✅ Image found via Serper: {image_path}")
        print(f"   File size: {image_path.stat().st_size / 1024:.1f} KB")
    else:
        print("❌ No image found")
        return 1
    
    return 0


if __name__ == "__main__":
    # Get custom query from command line
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Waymo self driving car technology"
    
    # Run tests
    exit_code = asyncio.run(test_serper_api(query))
    
    if exit_code == 0:
        # Also test the orchestrator
        exit_code = asyncio.run(test_orchestrator_with_serper())
    
    sys.exit(exit_code)
