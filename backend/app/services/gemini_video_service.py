import os
import time
import json
import logging
from pathlib import Path

import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiVideoService:
    """Service for interacting with Gemini Video API capabilities."""
    
    def __init__(self):
        """Initialize with Gemini client."""
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found in environment")
        
        genai.configure(api_key=self.api_key)
        
        # gemini-2.5-flash supports multimodal inputs including video and audio
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        logger.info("✓ Gemini Video Service initialized (using gemini-2.5-flash)")

    def generate_captions(self, video_path: Path, video_title: str = None, channel_name: str = None) -> list:
        """
        Uploads a video to Gemini and generates timestamped captions.
        
        Args:
            video_path: Path to the video file
            video_title: Optional title of the video for the generative prompt
            channel_name: Optional channel name of the video for the generative prompt
            
        Returns:
            A list of segment dictionaries: [{'text': str, 'start': float, 'end': float}]
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        logger.info(f"Uploading {video_path.name} to Gemini...")
        video_file = genai.upload_file(path=str(video_path))
        
        try:
            # Wait for processing if necessary
            # The File API might take a moment to process the video completely
            logger.info(f"Video uploaded as {video_file.uri}. Waiting for processing...")
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
                
            if video_file.state.name == "FAILED":
                raise Exception("Video processing failed on Gemini's servers.")
                
            context_addon = ""
            if video_title or channel_name:
                context_addon = f"\nFor context, the video is titled '{video_title or 'Unknown'}' and is by '{channel_name or 'Unknown'}'. Please incorporate this specific product/subject appropriately into the hook."

            prompt = '''
            Please analyze this video and generate a cohesive, engaging 1-minute voiceover script describing what happens.''' + context_addon + '''
            We want a high-quality summary script (roughly 1-minute long when read aloud, even if the video is longer) structured with:
            1. A Hook: Begin with an engaging hook that mentions the company name, product description, or refers to the video's main title/subject.
            2. Body: Describe the key visual actions, events, and any important speech/audio concisely in a chronological narrative format. Combine visual and audio context.
            3. Conclusion: Wrap up nicely with a concluding thought or summary.
            
            Break this resulting script into small chronological segments (roughly 3-7 seconds each) matching the events in the video's timeline.
            Format your response EXACTLY as a JSON array of objects, with NO surrounding markdown formatting.
            Each object must have these exact keys:
            - "text": the transcription/script segment (hook, body, or conclusion)
            - "start": the start time in seconds (as a float/number)
            - "end": the end time in seconds (as a float/number)
            
            Example output format:
            [
                {"text": "Figure just launched their new Helix bot, and it's taking living room cleaning to the next level.", "start": 0.0, "end": 4.5},
                {"text": "Watch as the robot diligently wipes down the coffee table.", "start": 4.5, "end": 8.0}
            ]
            '''
            
            logger.info("Generating captions from video with Gemini...")
            response = self.model.generate_content(
                [video_file, prompt],
                generation_config={"response_mime_type": "application/json"}
            )
            
            try:
                captions = json.loads(response.text)
                return captions
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response from Gemini. Raw text: {response.text}")
                raise ValueError("Gemini returned invalid JSON for captions.")
                
        finally:
            # Cleanup: delete the file from Gemini servers to avoid clutter
            try:
                genai.delete_file(video_file.name)
                logger.info("Deleted temporary video file from Gemini.")
            except Exception as e:
                logger.warning(f"Failed to delete file from Gemini: {e}")
