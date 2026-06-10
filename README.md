# 🎥 Automated YouTube Shorts Creator (Free & Open-Source)

A fully automated YouTube video creation and upload pipeline. The system monitors popular trends, writes engaging scripts, generates voiceovers, downloads matching stock footage, compiles them with subtitles and background music using FFmpeg, and automatically uploads the result daily to YouTube.

---

## 🛠️ Requirements & Installation

This system is completely free to run. It uses local open-source models/tools and free API tiers.

### Step 1: Install System Dependencies

#### 1. FFmpeg (Required for video compilation)
* **Windows (PowerShell - Administrator):**
  ```powershell
  winget install Gyan.FFmpeg
  ```
  *(Or download from [ffmpeg.org](https://ffmpeg.org/download.html) and add the `bin` folder to your Path environment variables)*
* **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt update && sudo apt install -y ffmpeg
  ```

#### 2. Piper TTS (Optional, for offline high-quality speech)
If you want to use local, offline voiceovers, install **Piper TTS**:
* Download the Piper executable for your platform from the [Piper Releases page](https://github.com/rhasspy/piper/releases).
* Download a voice model (e.g. `en_US-lessac-medium.onnx` and its matching `.onnx.json` config file) from the [Piper Voices repository](https://github.com/rhasspy/piper/blob/master/VOICES.md).
* Put both the Piper executable and model files into the `assets/` directory.
* *Note: If Piper is not detected, the system will automatically fall back to Google Text-to-Speech (`gTTS`), which is 100% free and online.*

---

### Step 2: Install Python Libraries

Initialize a virtual environment and install dependencies:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

---

## ⚙️ Configuration Setup

Create a `.env` file in the project root directory:

```env
# OpenRouter API Key (Required for writing scripts - gets free Gemini 2.5 Flash calls!)
OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY

# Pexels API Key (Free key from https://www.pexels.com/api/ - for download of stock footage)
PEXELS_API_KEY=YOUR_PEXELS_API_KEY

# Automation Niche (Optional, fallback topic if trends fail)
NICHE="interesting space facts"

# Video resolution config (Optional: default 1080x1920 for Shorts, 1920x1080 for standard landscape)
VIDEO_WIDTH=1080
VIDEO_HEIGHT=1920

# Run time for scheduler (24-hour format)
RUN_TIME="10:00"
```

---

## 🔑 YouTube API Credentials Setup

To upload videos automatically, you need a Google Cloud API credentials file.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Search for **YouTube Data API v3** in the API library and click **Enable**.
4. Go to **APIs & Services** -> **OAuth consent screen**:
   * Set User Type to **External**.
   * Fill out the app registration details.
   * Add the scope: `.../auth/youtube.upload`.
   * Add your own email as a **Test User** (required while in testing mode).
5. Go to **APIs & Services** -> **Credentials**:
   * Click **Create Credentials** -> **OAuth client ID**.
   * Select **Desktop App** as Application Type.
   * Click **Create**.
6. Download the OAuth Client JSON, rename it to `client_secrets.json`, and place it in the root folder of this project (`youtube_automation/`).

---

## 🚀 How to Run

### Manual Run
Create a video about current trending searches and upload it to YouTube:
```bash
python main.py
```

Create a video about a custom topic:
```bash
python main.py --topic "How black holes work" --privacy "unlisted"
```

### Daily Automated Scheduler
Run the daemon. It will check every day at the scheduled time (defined in `.env`), construct a trending video, and upload it as `private` or `unlisted` for your review:
```bash
python scheduler.py
```

---

## 📂 Assets
- Place copyright-free background music `.mp3` files inside `assets/music/` to automatically mix them into your videos at a lowered volume.
- Put any custom `.ttf` bold fonts inside `assets/fonts/` to use them for thumbnail text rendering.
