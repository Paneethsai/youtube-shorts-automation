import logging
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

import config
from trend_finder import TrendFinder
from script_writer import ScriptWriter
from voice_generator import VoiceGenerator
from media_downloader import MediaDownloader
from subtitle_generator import SubtitleGenerator
from thumbnail_creator import ThumbnailCreator
from video_builder import VideoBuilder
from youtube_uploader import YoutubeUploader

# Set up logging
log_filename = config.LOGS_DIR / f"automation_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("YouTubeAutomation")

class AutomationPipeline:
    def __init__(self):
        self.trend_finder = TrendFinder()
        self.script_writer = ScriptWriter()
        self.voice_generator = VoiceGenerator()
        self.media_downloader = MediaDownloader()
        self.subtitle_generator = SubtitleGenerator()
        self.thumbnail_creator = ThumbnailCreator()
        self.video_builder = VideoBuilder()
        self.uploader = YoutubeUploader()

    def run_pipeline(self, target_topic: str = None, privacy_status: str = "private", format_type: str = "short") -> bool:
        """
        Runs the full video automation pipeline:
        Trend Discovery -> Script -> Voiceover -> Video Download -> Subtitles -> Thumbnail -> FFmpeg Render -> Upload.
        Supports format_type='short' (1080x1920) or 'long' (1920x1080).
        """
        # Configure aspect ratios dynamically
        if format_type == "long":
            self.video_builder.width = 1920
            self.video_builder.height = 1080
            self.media_downloader.width = 1920
            self.media_downloader.height = 1080
            self.thumbnail_creator.width = 1280
            self.thumbnail_creator.height = 720
        else:
            self.video_builder.width = 1080
            self.video_builder.height = 1920
            self.media_downloader.width = 1080
            self.media_downloader.height = 1920
            self.thumbnail_creator.width = 1080
            self.thumbnail_creator.height = 1920

        # Create a unique temporary directory for this run
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = config.TEMP_DIR / f"run_{run_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"--- Starting Automation Pipeline ({format_type.upper()} Format, Run ID: {run_id}) ---")
        logger.info(f"Temporary workspace: {temp_dir}")
        
        try:
            # Step 1: Trend Discovery
            if not target_topic:
                logger.info("Discovering trending topics...")
                trends = self.trend_finder.get_combined_trends()
                if trends:
                    # Select the top trend
                    selected_trend = trends[0]
                    target_topic = selected_trend["title"]
                    logger.info(f"Selected trend topic: '{target_topic}' (Source: {selected_trend['source']})")
                else:
                    target_topic = config.NICHE
                    logger.warning(f"No trends found. Falling back to default niche: '{target_topic}'")
            else:
                logger.info(f"Using user-defined topic: '{target_topic}'")

            # Step 2: Script Writing
            logger.info("Writing script and SEO metadata...")
            script = self.script_writer.generate_script(target_topic, format_type)
            logger.info(f"Generated Script Title: {script['title']}")
            
            # Step 3: Voice Generation
            logger.info("Generating voice narration for segments...")
            segments_with_audio = self.voice_generator.generate_segment_audios(script["segments"], temp_dir)
            if not segments_with_audio:
                raise ValueError("Voice generation failed.")

            # Step 4: Video Media Download
            logger.info("Downloading stock video footage...")
            segments_with_media = self.media_downloader.download_media_for_segments(segments_with_audio, temp_dir)
            if not segments_with_media:
                raise ValueError("Media downloading/generation failed.")

            # Step 5: Subtitle Captioning
            logger.info("Generating subtitles...")
            srt_path = temp_dir / "subtitles.srt"
            sub_success = self.subtitle_generator.generate_srt(segments_with_media, srt_path)
            if not sub_success:
                raise ValueError("Subtitle generation failed.")

            # Step 6: Thumbnail Generation
            logger.info("Creating thumbnail...")
            thumbnail_path = temp_dir / "thumbnail.jpg"
            # Try to use first video clip as thumbnail background frame if possible, or fall back to gradient
            first_clip = Path(segments_with_media[0]["video_path"]) if segments_with_media else None
            # Extract single frame as thumbnail image using FFmpeg
            first_frame_path = temp_dir / "first_frame.jpg"
            if first_clip and first_clip.exists():
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", "0.5",  # Seek 0.5s to avoid black frame
                    "-i", str(first_clip),
                    "-vframes", "1",
                    str(first_frame_path)
                ]
                creation_flags = os.name == 'nt'
                # Run frame extraction silently
                subprocess.run(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
            
            bg_image = first_frame_path if first_frame_path.exists() else None
            thumb_success = self.thumbnail_creator.generate_thumbnail(script["title"], bg_image, thumbnail_path)
            if not thumb_success:
                logger.warning("Thumbnail generation failed. Will upload without custom thumbnail.")

            # Step 7: Video Assembly & Subtitle Burn
            output_filename = f"video_{run_id}.mp4"
            output_video_path = config.OUTPUT_DIR / output_filename
            logger.info(f"Rendering final video to: {output_video_path}")
            
            build_success = self.video_builder.build_video(
                segments=segments_with_media,
                srt_path=str(srt_path),
                output_video_path=output_video_path,
                temp_dir=temp_dir
            )
            
            if not build_success or not output_video_path.exists():
                raise ValueError("FFmpeg video rendering failed.")
                
            logger.info(f"Video created successfully! File saved at: {output_video_path}")

            # Step 8: Upload to YouTube
            logger.info("Uploading video to YouTube...")
            seo = script["seo"]
            tags_str = ", ".join(seo["tags"])
            description = f"{seo['description']}\n\nTags: {tags_str}\nHashtags: {' '.join(seo['hashtags'])}"
            
            try:
                video_id = self.uploader.upload_video(
                    video_path=output_video_path,
                    title=seo["title"],
                    description=description,
                    tags=seo["tags"],
                    thumbnail_path=thumbnail_path if thumbnail_path.exists() else None,
                    privacy_status=privacy_status
                )
                if video_id:
                    logger.info(f"Successfully automated video upload! Video URL: https://youtu.be/{video_id}")
                else:
                    logger.warning("YouTube Upload completed, but no Video ID was returned.")
            except Exception as upload_err:
                logger.error(
                    f"\n------------------------------------------------------\n"
                    f"YOUTUBE UPLOAD SKIPPED OR FAILED: {upload_err}\n"
                    f"The video was generated successfully and saved locally!\n"
                    f"You can find it here: {output_video_path}\n"
                    f"Setup client_secrets.json to enable automatic uploads next time.\n"
                    f"------------------------------------------------------"
                )

            return True

        except Exception as e:
            logger.critical(f"Pipeline crashed during execution: {e}", exc_info=True)
            return False
            
        finally:
            # Clean up temp folder to conserve storage
            if temp_dir.exists():
                logger.info(f"Cleaning up temporary folder: {temp_dir}")
                try:
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_err:
                    logger.warning(f"Failed to delete temp directory: {cleanup_err}")
            logger.info("--- Pipeline Execution Finished ---")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="YouTube Daily Shorts & Long-form Automation System")
    parser.add_argument("--topic", type=str, default=None, help="Custom topic to write video script on")
    parser.add_argument("--privacy", type=str, default="private", choices=["private", "unlisted", "public"], help="YouTube video privacy status")
    parser.add_argument("--format", type=str, default="short", choices=["short", "long"], help="Video format: short (1080x1920) or long (1920x1080)")
    
    args = parser.parse_args()
    
    pipeline = AutomationPipeline()
    pipeline.run_pipeline(target_topic=args.topic, privacy_status=args.privacy, format_type=args.format)
