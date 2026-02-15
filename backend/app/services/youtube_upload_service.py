"""
YouTube Upload Service.

Handles uploading completed videos to YouTube via the Data API v3.
Supports:
- Public Short uploads with SEO metadata
- Category injection (Education = 27)
- Tags, title, and description from the validation page
"""

import os
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

# YouTube API constants
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
YOUTUBE_CATEGORY_EDUCATION = "27"
DEFAULT_PRIVACY = "private"  # Safe zone: upload as private first


class YouTubeUploadService:
    """Service for uploading videos to YouTube via Data API v3."""

    def __init__(self):
        """Initialize with OAuth2 credentials."""
        self._youtube = None

    def _get_authenticated_service(self):
        """
        Build an authenticated YouTube API client.
        
        Uses a stored OAuth2 refresh token from data/youtube_oauth.json.
        If no token exists, raises an error directing to the auth flow.
        """
        if self._youtube is not None:
            return self._youtube

        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
        except ImportError:
            raise RuntimeError(
                "YouTube upload requires google-api-python-client and google-auth. "
                "Install with: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
            )

        token_path = Path("data/youtube_oauth.json")
        if not token_path.exists():
            raise FileNotFoundError(
                f"YouTube OAuth token not found at {token_path}. "
                "Run 'python -m app.services.youtube_upload_service --auth' to authenticate."
            )

        creds = Credentials.from_authorized_user_file(str(token_path))

        # Refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Persist refreshed token
            token_path.write_text(creds.to_json())
            logger.info("Refreshed YouTube OAuth token.")

        self._youtube = build(
            YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
            credentials=creds
        )
        return self._youtube

    def upload_video(
        self,
        file_path: str,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        category_id: str = YOUTUBE_CATEGORY_EDUCATION,
        privacy_status: str = DEFAULT_PRIVACY,
        is_short: bool = True,
    ) -> dict:
        """
        Upload a video to YouTube.
        
        Args:
            file_path: Absolute path to the video file
            title: YouTube title (max 100 chars)
            description: YouTube description (max 5000 chars)
            tags: List of search tags
            category_id: YouTube category ID (default: 27 = Education)
            privacy_status: "private", "unlisted", or "public"
            is_short: Whether to tag as a YouTube Short
            
        Returns:
            dict with youtube_video_id, youtube_url, and status
        """
        from googleapiclient.http import MediaFileUpload

        youtube = self._get_authenticated_service()

        video_path = Path(file_path)
        if not video_path.exists():
            # Try relative to backend
            video_path = Path.cwd() / file_path
            if not video_path.exists():
                raise FileNotFoundError(f"Video file not found: {file_path}")

        # Ensure #Shorts hashtag is in description for YouTube Shorts detection
        if is_short and "#Shorts" not in description:
            description = description.rstrip() + "\n\n#Shorts"

        # Build the video resource body
        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags or [],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        logger.info(f"Uploading to YouTube: '{title[:50]}...' ({privacy_status})")

        # Create the media upload object
        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True,
            chunksize=10 * 1024 * 1024,  # 10 MB chunks
        )

        # Execute the upload
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                logger.info(f"Upload progress: {progress}%")

        video_id = response["id"]
        youtube_url = f"https://youtube.com/shorts/{video_id}"

        logger.info(f"✅ Upload complete: {youtube_url}")

        return {
            "youtube_video_id": video_id,
            "youtube_url": youtube_url,
            "privacy_status": privacy_status,
            "status": "uploaded",
        }


def run_oauth_flow():
    """
    Interactive OAuth2 flow to obtain YouTube upload credentials.
    
    Requires:
    - A Google Cloud project with YouTube Data API v3 enabled
    - OAuth 2.0 Client ID credentials (Desktop app type)
    - Client secrets saved to data/client_secret.json
    
    Usage:
        python -m app.services.youtube_upload_service --auth
    """
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Install google-auth-oauthlib: pip install google-auth-oauthlib")
        return

    client_secrets_path = Path("data/client_secret.json")
    if not client_secrets_path.exists():
        print(
            "❌ client_secret.json not found!\n\n"
            "Steps to create:\n"
            "1. Go to https://console.cloud.google.com/apis/credentials\n"
            "2. Create an OAuth 2.0 Client ID (Desktop application)\n"
            "3. Download the JSON and save as: data/client_secret.json\n"
            "4. Enable 'YouTube Data API v3' in your project\n"
            "5. Re-run this command"
        )
        return

    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly",
    ]

    flow = InstalledAppFlow.from_client_secrets_file(
        str(client_secrets_path), scopes=SCOPES
    )
    credentials = flow.run_local_server(port=8090, prompt="consent")

    token_path = Path("data/youtube_oauth.json")
    token_path.write_text(credentials.to_json())
    print(f"✅ YouTube OAuth token saved to {token_path}")
    print("You can now use 'Approve & Publish' in the app!")


if __name__ == "__main__":
    import sys
    if "--auth" in sys.argv:
        run_oauth_flow()
    else:
        print("Usage: python -m app.services.youtube_upload_service --auth")
