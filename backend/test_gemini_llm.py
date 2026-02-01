import os
import google.generativeai as genai
from dotenv import load_dotenv

def test_gemini_llm():
    # 1. Load environment variables
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY") # We use GOOGLE_API_KEY for both in this setup
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found in environment variables.")
        return

    print(f"✅ Found GOOGLE_API_KEY: {api_key[:4]}...{api_key[-4:]}")

    # 2. Configure Gemini
    genai.configure(api_key=api_key)
    
    # Using a standard model
    model_name = os.getenv("GEMINI_MODEL") or "gemini-1.5-flash"
    print(f"✅ Using Model: {model_name}")

    print("\nAttempting to connect to Gemini LLM API...")
    
    try:
        # 3. Create model and generate content
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say 'Gemini API connectivity test successful!'")
        
        # 4. Handle response
        if response and response.text:
            print(f"✅ Success! Gemini LLM responded: {response.text.strip()}")
        else:
            print("❌ Error: Received empty response from Gemini LLM.")
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")

if __name__ == "__main__":
    test_gemini_llm()
