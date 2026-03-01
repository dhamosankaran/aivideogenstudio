"""
Test script for Gemini Image Generation API (google-genai SDK).
Generates a book-themed image using gemini-3.1-flash-image-preview.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def test_gemini_image_gen():
    # 1. Load environment variables
    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found in environment variables.")
        print("   Set it in your .env file or export it: export GOOGLE_API_KEY=your_key")
        return False

    print(f"✅ Found GOOGLE_API_KEY: {api_key[:4]}...{api_key[-4:]}")

    # 2. Import the new google-genai SDK
    try:
        from google import genai
        from google.genai import types
        print("✅ google-genai SDK imported successfully")
    except ImportError:
        print("❌ Error: google-genai package not installed.")
        print("   Install it: pip install google-genai")
        return False

    try:
        from PIL import Image
        print("✅ Pillow (PIL) imported successfully")
    except ImportError:
        print("❌ Error: Pillow package not installed.")
        print("   Install it: pip install Pillow")
        return False

    # 3. Configure client
    client = genai.Client(api_key=api_key)
    model_name = "gemini-3.1-flash-image-preview"
    print(f"✅ Using Model: {model_name}")

    # 4. Set image generation parameters
    prompt = (
        "A cozy reading nook with warm golden lighting, "
        "an open hardcover book on a wooden table, "
        "a steaming cup of coffee beside it, "
        "bookshelves in the soft-focus background. "
        "Photorealistic, cinematic lighting, high quality."
    )
    aspect_ratio = "9:16"   # Vertical for YouTube Shorts
    resolution = "1K"        # As requested

    print(f"\n📝 Prompt: {prompt}")
    print(f"📐 Aspect Ratio: {aspect_ratio}")
    print(f"📏 Resolution: {resolution}")
    print("\n⏳ Generating image... (this may take 10-30 seconds)")

    try:
        # 5. Generate image
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE'],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=resolution
                ),
            )
        )

        # 6. Process response
        output_dir = Path("data")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "test_generated_image.png"

        text_response = None
        image_saved = False

        for part in response.parts:
            if part.text is not None:
                text_response = part.text
                print(f"\n💬 Text response: {text_response}")
            elif image := part.as_image():
                image.save(str(output_path))
                image_saved = True
                print(f"\n✅ Image saved to: {output_path}")
                # Read back with PIL to get dimensions
                pil_img = Image.open(str(output_path))
                print(f"   Dimensions: {pil_img.size[0]}x{pil_img.size[1]}")
                print(f"   Format: {pil_img.format or 'PNG'}")

        if not image_saved:
            print("\n⚠️  No image was returned in the response.")
            if text_response:
                print(f"   Model returned text only: {text_response}")
            else:
                print("   Response was empty.")
            return False

        print("\n🎉 SUCCESS! Gemini image generation test passed.")
        print(f"   Output: {output_path.resolve()}")
        return True

    except Exception as e:
        print(f"\n❌ Exception occurred: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_gemini_image_gen()
    sys.exit(0 if success else 1)
