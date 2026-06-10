import os
import subprocess
import logging
from pathlib import Path
from gtts import gTTS
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoiceGenerator")

class VoiceGenerator:
    def __init__(self):
        self.piper_exe = config.PIPER_EXECUTABLE
        self.piper_model = config.PIPER_MODEL

    def is_piper_available(self) -> bool:
        """Checks if the Piper executable and model files are present."""
        # Check if the model exists
        if not Path(self.piper_model).exists():
            logger.warning(f"Piper voice model not found at {self.piper_model}. Fallback to gTTS will be used.")
            return False

        # Try running piper --help to see if executable works
        try:
            # On Windows, subprocess could search PATH or find it directly if it's absolute
            result = subprocess.run(
                [self.piper_exe, "-h"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return result.returncode in [0, 1]
        except Exception:
            logger.warning("Piper executable not found or not in PATH. Fallback to gTTS will be used.")
            return False

    def generate_voice_piper(self, text: str, output_path: str) -> bool:
        """Generates audio file using Piper TTS."""
        try:
            logger.info(f"Generating voice with Piper: '{text[:30]}...' -> {output_path}")
            # Run Piper via subprocess, writing the text directly to stdin
            cmd = [
                self.piper_exe,
                "--model", self.piper_model,
                "--output_file", output_path
            ]
            
            # Run without showing window on Windows
            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            
            result = subprocess.run(
                cmd,
                input=text.encode('utf-8'),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags
            )
            
            if result.returncode == 0 and Path(output_path).exists():
                logger.info("Piper voice generation successful.")
                return True
            else:
                logger.error(f"Piper error (Code {result.returncode}): {result.stderr.decode('utf-8')}")
                return False
        except Exception as e:
            logger.error(f"Error running Piper: {e}")
            return False

    def generate_voice_gtts(self, text: str, output_path: str) -> bool:
        """Generates audio file using Google Text-to-Speech (gTTS)."""
        try:
            logger.info(f"Generating voice with gTTS: '{text[:30]}...' -> {output_path}")
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(output_path)
            logger.info("gTTS voice generation successful.")
            return True
        except Exception as e:
            logger.error(f"Error running gTTS: {e}")
            return False

    def generate_segment_audios(self, segments: list, temp_dir: Path) -> list:
        """
        Generates individual audio files for each segment and returns updated segments
        with paths to the audio files and their durations.
        """
        updated_segments = []
        use_piper = self.is_piper_available()
        
        # Audio library like wave or ffprobe can be used to read duration.
        # But we can also get duration from FFmpeg metadata or a quick ffprobe run.
        for idx, segment in enumerate(segments):
            file_ext = "wav" if use_piper else "mp3"
            audio_path = temp_dir / f"segment_{idx}.{file_ext}"
            text = segment["text"]
            
            success = False
            if use_piper:
                success = self.generate_voice_piper(text, str(audio_path))
            
            # If Piper failed or is not available, fall back to gTTS
            if not success:
                # Force output path to .mp3 for gTTS
                audio_path = temp_dir / f"segment_{idx}.mp3"
                success = self.generate_voice_gtts(text, str(audio_path))
                
            if success:
                # Find duration using FFmpeg/ffprobe or fallback estimates
                duration = self.get_audio_duration(audio_path)
                updated_segments.append({
                    **segment,
                    "audio_path": str(audio_path),
                    "duration": duration
                })
            else:
                logger.error(f"Failed to generate audio for segment {idx}")
                
        return updated_segments

    def get_audio_duration(self, file_path: Path) -> float:
        """Retrieves duration of an audio file using ffprobe."""
        try:
            cmd = [
                "ffprobe", 
                "-v", "error", 
                "-show_entries", "format=duration", 
                "-of", "default=noprint_wrappers=1:nokey=1", 
                str(file_path)
            ]
            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                creationflags=creation_flags
            )
            if result.returncode == 0:
                return float(result.stdout.decode('utf-8').strip())
        except Exception as e:
            logger.warning(f"Failed to read audio duration using ffprobe: {e}. Estimating length based on word count.")
        
        # Fallback estimation: average reading speed is ~130 words per minute (2.16 words per second)
        # We can read file content and do word count
        try:
            # Simple estimation
            import wave
            if file_path.suffix == ".wav":
                with wave.open(str(file_path), 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    return frames / float(rate)
        except Exception:
            pass
            
        return 3.0 # absolute fallback minimum

if __name__ == "__main__":
    # Test execution
    vg = VoiceGenerator()
    test_temp = Path("temp")
    test_temp.mkdir(exist_ok=True)
    test_segments = [{"text": "Welcome back to the channel. Today we have something special."}]
    res = vg.generate_segment_audios(test_segments, test_temp)
    print("Generated Segments:", res)
