import logging
import os
import random
import subprocess
from pathlib import Path
import requests
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MediaDownloader")

class MediaDownloader:
    def __init__(self):
        self.api_key = config.PEXELS_API_KEY
        self.headers = {"Authorization": self.api_key} if self.api_key else {}
        self.width = config.VIDEO_WIDTH
        self.height = config.VIDEO_HEIGHT
        
    def download_url(self, url: str, dest_path: Path) -> bool:
        """Downloads a file from a URL to a local destination path."""
        try:
            logger.info(f"Downloading media from {url} to {dest_path}")
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code == 200:
                with open(dest_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return True
            else:
                logger.error(f"Download failed with status: {response.status_code}")
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
        return False

    def search_pexels_video(self, query: str) -> str:
        """Searches Pexels for a vertical or horizontal video matching the query."""
        if not self.api_key:
            logger.warning("Pexels API key not found. Skipping API search.")
            return ""
            
        orientation = "portrait" if self.height > self.width else "landscape"
        url = f"https://api.pexels.com/videos/search?query={requests.utils.quote(query)}&per_page=5&orientation={orientation}"
        
        try:
            logger.info(f"Searching Pexels for: '{query}' ({orientation})")
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                videos = data.get("videos", [])
                if videos:
                    # Pick a random video from top 3 to keep visuals diverse
                    selected_video = random.choice(videos[:3])
                    video_files = selected_video.get("video_files", [])
                    
                    # Sort files to prioritize HD/UHD and correct aspect ratio
                    matched_files = []
                    for vf in video_files:
                        if vf.get("file_type") == "video/mp4":
                            w = vf.get("width") or 0
                            h = vf.get("height") or 0
                            quality = (vf.get("quality") or "sd").lower()
                            
                            # Check if aspect ratio matches orientation
                            aspect_match = False
                            if orientation == "portrait" and h > w:
                                aspect_match = True
                            elif orientation == "landscape" and w > h:
                                aspect_match = True
                                
                            # Score the file:
                            # +10 points for matching aspect ratio
                            # +5 points for HD/UHD quality
                            # +3 points for height >= 720
                            score = 0
                            if aspect_match:
                                score += 10
                            if quality in ["hd", "uhd"]:
                                score += 5
                            if h >= 720 or w >= 1280:
                                score += 3
                            
                            matched_files.append((score, vf))
                    
                    if matched_files:
                        # Sort by score descending and return the link of the best one
                        matched_files.sort(key=lambda x: x[0], reverse=True)
                        best_file = matched_files[0][1]
                        return best_file.get("link", "")
            else:
                logger.error(f"Pexels search API failed: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Pexels API search error: {e}")
        return ""

    def generate_solid_color_video(self, duration: float, dest_path: Path) -> bool:
        """Generates a solid color video using FFmpeg as a offline fallback."""
        try:
            # Pick a random nice color (hex or name)
            colors = ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51", "#1d3557", "#457b9d", "#a8dadc", "#8d99ae"]
            color = random.choice(colors)
            logger.info(f"Generating solid color video fallback ({color}) for duration {duration}s -> {dest_path}")
            
            # FFmpeg solid color command
            # s=WxH, d=duration, color=hex
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c={color}:s={self.width}x{self.height}:d={duration}:r={config.VIDEO_FPS}",
                "-pix_fmt", "yuv420p",
                "-c:v", "libx264",
                str(dest_path)
            ]
            
            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creation_flags)
            return result.returncode == 0 and dest_path.exists()
        except Exception as e:
            logger.error(f"Error generating solid color video: {e}")
            return False

    def search_pexels_photo(self, query: str) -> str:
        """Searches Pexels for a photo matching the query."""
        if not self.api_key:
            return ""
        url = f"https://api.pexels.com/v1/search?query={requests.utils.quote(query)}&per_page=5"
        try:
            logger.info(f"Searching Pexels for photo: '{query}'")
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                photos = data.get("photos", [])
                if photos:
                    selected_photo = random.choice(photos[:3])
                    src = selected_photo.get("src", {})
                    return src.get("portrait") or src.get("large") or src.get("original") or ""
            else:
                logger.error(f"Pexels photo search failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Pexels photo API search error: {e}")
        return ""

    def download_media_for_segments(self, segments: list, temp_dir: Path) -> list:
        """
        Downloads matching stock video or photo for each segment, falling back to local solid color
        generation if downloads fail or API keys are missing.
        """
        updated_segments = []
        for idx, segment in enumerate(segments):
            keywords = segment.get("keywords", "")
            duration = segment.get("duration", 5.0)
            dest_video_path = temp_dir / f"clip_{idx}.mp4"
            
            # Clean and sanitize keyword search query
            kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
            search_query = kw_list[0] if kw_list else config.NICHE
            # Limit search query to 2 words max to keep searches on Pexels simple and successful
            words = search_query.split()
            if len(words) > 2:
                search_query = " ".join(words[:2])
            
            download_success = False
            video_url = ""
            is_image = False
            
            # 1. Try Pexels
            if self.api_key:
                # Try Video first
                video_url = self.search_pexels_video(search_query)
                if video_url:
                    download_success = self.download_url(video_url, dest_video_path)
                
                # Try Photo if Video search/download failed
                if not download_success:
                    photo_url = self.search_pexels_photo(search_query)
                    if photo_url:
                        dest_photo_path = temp_dir / f"clip_{idx}.jpg"
                        download_success = self.download_url(photo_url, dest_photo_path)
                        if download_success:
                            dest_video_path = dest_photo_path
                            is_image = True
            
            # 2. Offline Fallback
            if not download_success:
                logger.warning(f"Could not download stock footage for query '{search_query}'. Generating offline video clip.")
                generate_success = self.generate_solid_color_video(duration, dest_video_path)
                if not generate_success:
                    logger.critical(f"Failed to generate solid color fallback clip for segment {idx}")
                    continue
                    
            updated_segments.append({
                **segment,
                "video_path": str(dest_video_path),
                "is_image": is_image
            })
            
        return updated_segments

if __name__ == "__main__":
    # Test downloader
    dl = MediaDownloader()
    test_temp = Path("temp")
    test_temp.mkdir(exist_ok=True)
    # Test fallback generation
    dl.generate_solid_color_video(5.0, test_temp / "test_fallback.mp4")
    print("Generated test fallback video clip.")
