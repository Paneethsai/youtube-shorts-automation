import os
import pickle
import logging
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("YoutubeUploader")

# Tell Google libraries to allow local HTTP redirect URI in testing
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

class YoutubeUploader:
    def __init__(self):
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        self.client_secrets_file = config.YOUTUBE_CLIENT_SECRETS_FILE
        self.credentials_file = config.YOUTUBE_CREDENTIALS_FILE

    def get_authenticated_service(self):
        """Authenticates user via OAuth2 and returns the YouTube API service object."""
        creds = None
        
        # Load cached credentials if they exist
        if self.credentials_file.exists():
            try:
                with open(self.credentials_file, "rb") as token:
                    creds = pickle.load(token)
            except Exception as e:
                logger.warning(f"Failed to load cached credentials: {e}. Re-authenticating.")
                
        # If credentials are not valid/present, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("Refreshing expired YouTube OAuth credentials...")
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}. Running full auth flow.")
                    creds = None
            
            if not creds:
                if not self.client_secrets_file.exists():
                    logger.critical(
                        f"\n=======================================================\n"
                        f"CRITICAL ERROR: '{self.client_secrets_file.name}' not found!\n"
                        f"To enable YouTube uploads, follow these steps:\n"
                        f"1. Go to Google Cloud Console (https://console.cloud.google.com/)\n"
                        f"2. Create a project and enable 'YouTube Data API v3'.\n"
                        f"3. Go to 'APIs & Services' -> 'Credentials'.\n"
                        f"4. Create an 'OAuth 2.0 Client ID' (Desktop App).\n"
                        f"5. Download the JSON, rename it to 'client_secrets.json', and place it in: {self.client_secrets_file.parent}\n"
                        f"=======================================================\n"
                    )
                    raise FileNotFoundError(f"Missing {self.client_secrets_file.name}")
                
                logger.info("Starting local OAuth consent screen login flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.client_secrets_file), self.scopes
                )
                creds = flow.run_local_server(port=0)
                
            # Save the credentials for next run
            with open(self.credentials_file, "wb") as token:
                pickle.dump(creds, token)
                logger.info(f"YouTube credentials saved to {self.credentials_file}")
                
        return build("youtube", "v3", credentials=creds)

    def upload_video(self, video_path: Path, title: str, description: str, tags: list, thumbnail_path: Path = None, privacy_status: str = "private") -> str:
        """
        Uploads a video to YouTube with metadata and a thumbnail image.
        Returns the uploaded video ID.
        """
        try:
            logger.info(f"Authenticating YouTube service...")
            youtube = self.get_authenticated_service()
            
            body = {
                "snippet": {
                    "title": title[:100],  # Title limit is 100 characters
                    "description": description[:5000],  # Description limit is 5000 characters
                    "tags": tags,
                    "categoryId": "27"  # '27' represents Education
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False
                }
            }
            
            logger.info(f"Initiating upload for video: {video_path}")
            media = MediaFileUpload(
                str(video_path), 
                mimetype="video/mp4", 
                resumable=True, 
                chunksize=256 * 1024 # 256KB chunks
            )
            
            request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Uploaded progress: {int(status.progress() * 100)}%")
                    
            video_id = response.get("id")
            logger.info(f"Video uploaded successfully! Video ID: {video_id}")
            
            # Upload thumbnail if provided
            if thumbnail_path and thumbnail_path.exists() and video_id:
                self.upload_thumbnail(youtube, video_id, thumbnail_path)
                
            return video_id
            
        except Exception as e:
            logger.error(f"Failed to upload video to YouTube: {e}")
            return ""

    def upload_thumbnail(self, youtube_service, video_id: str, thumbnail_path: Path):
        """Uploads a thumbnail image and associates it with the video ID."""
        try:
            logger.info(f"Uploading thumbnail: {thumbnail_path} for video {video_id}")
            media = MediaFileUpload(str(thumbnail_path), mimetype="image/jpeg")
            youtube_service.thumbnails().set(
                videoId=video_id,
                media_body=media
            ).execute()
            logger.info("Thumbnail uploaded successfully.")
        except Exception as e:
            logger.error(f"Failed to set custom thumbnail: {e}")

if __name__ == "__main__":
    # Test client logic
    pass
