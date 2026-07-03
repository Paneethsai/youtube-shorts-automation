@echo off
title YouTube Automation Scheduler
echo Starting YouTube Automation Scheduler...
cd /d "C:\Users\PANEETH'S-HPBOOK\.gemini\antigravity\scratch\youtube_automation"
if exist venv\Scripts\activate.bat (
    echo Activating Virtual Environment...
    call venv\Scripts\activate.bat
)
python scheduler.py
pause
