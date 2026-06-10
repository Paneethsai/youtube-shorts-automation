import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SubtitleGenerator")

class SubtitleGenerator:
    def format_srt_time(self, seconds: float) -> str:
        """Formats duration in seconds into SRT time format HH:MM:SS,mmm."""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        if millis == 1000:
            millis = 0
            secs += 1
            if secs == 60:
                secs = 0
                mins += 1
                if mins == 60:
                    mins = 0
                    hrs += 1
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    def split_text_into_chunks(self, text: str, max_words: int = 3) -> list:
        """Splits a string into chunks of maximum `max_words` words."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), max_words):
            chunks.append(" ".join(words[i:i + max_words]))
        return chunks

    def generate_srt(self, segments: list, srt_output_path: Path) -> bool:
        """
        Generates a synchronized SRT subtitle file from segments.
        Calculates time codes by proportionally distributing segment durations
        across small word chunks.
        """
        try:
            logger.info(f"Generating subtitles file: {srt_output_path}")
            srt_index = 1
            current_start_time = 0.0
            
            with open(srt_output_path, "w", encoding="utf-8") as srt_file:
                for segment in segments:
                    text = segment["text"]
                    duration = segment["duration"]
                    
                    # Split text into small digestible chunks (perfect for Shorts)
                    chunks = self.split_text_into_chunks(text, max_words=3)
                    
                    # Calculate total character count to distribute time proportionally
                    # (Character count is a better proxy for pronunciation length than word count)
                    total_chars = sum(len(c) for c in chunks)
                    if total_chars == 0:
                        current_start_time += duration
                        continue
                    
                    segment_elapsed = 0.0
                    for chunk in chunks:
                        chunk_len = len(chunk)
                        # Proportional duration
                        chunk_duration = (chunk_len / total_chars) * duration
                        
                        start_time = current_start_time + segment_elapsed
                        end_time = start_time + chunk_duration
                        
                        # Format SRT time codes
                        start_str = self.format_srt_time(start_time)
                        end_str = self.format_srt_time(end_time)
                        
                        # Write SRT block
                        srt_file.write(f"{srt_index}\n")
                        srt_file.write(f"{start_str} --> {end_str}\n")
                        srt_file.write(f"{chunk.upper()}\n\n") # Uppercase captions are popular
                        
                        srt_index += 1
                        segment_elapsed += chunk_duration
                        
                    # Increment start time for the next segment
                    current_start_time += duration
                    
            logger.info("Subtitle file generated successfully.")
            return True
        except Exception as e:
            logger.error(f"Error generating subtitles: {e}")
            return False

if __name__ == "__main__":
    # Test subtitle generator
    sg = SubtitleGenerator()
    test_segments = [
        {"text": "Did you know that honey never spoils?", "duration": 3.5},
        {"text": "Archeologists found edible pots of honey in Egyptian tombs.", "duration": 4.5}
    ]
    test_output = Path("temp") / "test_subs.srt"
    test_output.parent.mkdir(exist_ok=True)
    sg.generate_srt(test_segments, test_output)
    
    with open(test_output, "r") as f:
        print(f.read())
