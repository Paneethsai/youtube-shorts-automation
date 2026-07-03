@echo off
title YouTube Shorts Instant Creator
echo Triggering YouTube Automation Pipeline...
cd /d "C:\Users\PANEETH'S-HPBOOK\.gemini\antigravity\scratch\youtube_automation"
if exist venv\Scripts\activate.bat (
    echo Activating Virtual Environment...
    call venv\Scripts\activate.bat
)
python main.py --format short --privacy public
pause
