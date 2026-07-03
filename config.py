import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Directories configuration
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
TEMP_DIR = BASE_DIR / "temp"

# Sub-directories for assets
MUSIC_DIR = ASSETS_DIR / "music"
FONTS_DIR = ASSETS_DIR / "fonts"

# Auto-create directories
for folder in [ASSETS_DIR, OUTPUT_DIR, LOGS_DIR, TEMP_DIR, MUSIC_DIR, FONTS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Try to load OpenRouter API Key from ~/.claude/settings.json if not in .env
def get_openrouter_key():
    env_key = os.getenv("OPENROUTER_API_KEY")
    if env_key:
        return env_key
    
    # Try Claude Code settings path
    settings_path = Path.home() / ".claude" / "settings.json"
    if settings_path.exists():
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                token = data.get("env", {}).get("ANTHROPIC_AUTH_TOKEN")
                if token and token.startswith("sk-or-"):
                    return token
        except Exception:
            pass
    return ""

# API Credentials
OPENROUTER_API_KEY = get_openrouter_key()
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# YouTube Settings
YOUTUBE_CLIENT_SECRETS_FILE = BASE_DIR / "client_secrets.json"
YOUTUBE_CREDENTIALS_FILE = BASE_DIR / "youtube_credentials.json"

# PIPER TTS Path settings
# Users can place piper.exe / piper binary in assets or system path
PIPER_EXECUTABLE = os.getenv("PIPER_EXECUTABLE", "piper")
PIPER_MODEL = os.getenv("PIPER_MODEL", str(ASSETS_DIR / "en_US-lessac-medium.onnx"))

# Video Configuration
VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1080"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1920")) # Default: YouTube Shorts (Vertical 9:16)
VIDEO_FPS = int(os.getenv("VIDEO_FPS", "30"))

# Automation Niche (can be customized)
NICHES = [
    "Personal Finance & AI Tools (focused on Indian fintech apps, UPI, savings hacks)",
    "Indian Crisis & Collapse Stories (cost-of-living, unemployment, infrastructure issues)",
    "Volcano & Disaster Explainers (global + Indian floods, cyclones, earthquakes)",
    "Luxury Mansions & Castles Documentaries (Indian palaces, forts, heritage sites)",
    "Sleep & Relaxation Stories (mythology, Indian folk tales, calming narrations)",
    "Productivity & Study Tips (exam prep, UPSC/SSC/JEE hacks, student routines)",
    "Travel Guides & Localized Problem Stories (Indian cities, tourism + local challenges)",
    "Software Tutorials & Automation Tools (AI tools, coding tutorials, Indian tech context)",
    "YouTube Shorts (Indian facts, mini tutorials, trending cultural snippets)"
]
NICHE = os.getenv("NICHE", NICHES[0])

# OpenAI/OpenRouter model setup
# We will use google/gemini-2.5-flash which is free on OpenRouter
LLM_MODEL = os.getenv("LLM_MODEL", "google/gemini-2.5-flash")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
