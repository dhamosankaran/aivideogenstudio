import os
import requests
import json
import base64
from dotenv import load_dotenv

def test_gemini_tts():
    # 1. Load environment variables
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    project_id = "938994850777"
    
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found in environment variables.")
        return

    print(f"✅ Found GOOGLE_API_KEY: {api_key[:4]}...{api_key[-4:]}")
    print(f"✅ Using Project ID: {project_id}")

    # 2. Define API Endpoint and Payload
    url = "https://texttospeech.googleapis.com/v1/text:synthesize"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key
    }
    
    payload = {
        "input": {
            "text": "Hello! This is a test of the Gemini TTS connectivity."
        },
        "voice": {
            "languageCode": "en-US",
            "name": "en-US-Journey-F"  # Using the default from the provider
        },
        "audioConfig": {
            "audioEncoding": "MP3"
        }
    }

    print("\nAttempting to connect to Google TTS API...")
    
    try:
        # 3. Make the request
        response = requests.post(url, json=payload, headers=headers)
        
        # 4. Handle response
        if response.status_code == 200:
            data = response.json()
            audio_content = data.get("audioContent")
            
            if audio_content:
                # Decode and save
                audio_bytes = base64.b64decode(audio_content)
                output_file = "test_gemini_tts_output.mp3"
                
                with open(output_file, "wb") as f:
                    f.write(audio_bytes)
                
                print(f"✅ Success! Audio saved to {output_file}")
                print(f"   Size: {len(audio_bytes)} bytes")
            else:
                print("❌ Error: Response 200 OK but no 'audioContent' found.")
                print("Response:", json.dumps(data, indent=2))
        else:
            print(f"❌ API Request Failed with status code: {response.status_code}")
            print("Response:", response.text)
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")

if __name__ == "__main__":
    test_gemini_tts()
