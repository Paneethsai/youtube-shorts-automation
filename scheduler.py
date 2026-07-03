import os
import sys
import time
import logging
import schedule
from datetime import datetime
from main import AutomationPipeline
import config

# Configure scheduler logging
log_filename = config.LOGS_DIR / "scheduler.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] Scheduler: %(message)s",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Scheduler")

def run_shorts_job():
    logger.info("Executing scheduled daily Shorts video creation job...")
    pipeline = AutomationPipeline()
    try:
        privacy = os.getenv("PRIVACY_STATUS", "public")
        # Upload using the configured privacy status
        success = pipeline.run_pipeline(privacy_status=privacy, format_type="short")
        if success:
            logger.info("Shorts job completed successfully.")
        else:
            logger.error("Shorts job failed.")
    except Exception as e:
        logger.critical(f"Shorts job crashed: {e}")

def run_long_job():
    logger.info("Executing scheduled daily Long-form video creation job...")
    pipeline = AutomationPipeline()
    try:
        privacy = os.getenv("PRIVACY_STATUS", "public")
        # Upload using the configured privacy status
        success = pipeline.run_pipeline(privacy_status=privacy, format_type="long")
        if success:
            logger.info("Long-form job completed successfully.")
        else:
            logger.error("Long-form job failed.")
    except Exception as e:
        logger.critical(f"Long-form job crashed: {e}")

def main():
    # Configure daily run times (24-hour format: "HH:MM")
    # You can customize these by setting environment variables
    shorts_time = os.getenv("SHORTS_TIME", "09:00")
    long_time = os.getenv("LONG_TIME", "15:00")
    
    logger.info("Starting YouTube Automation Scheduler daemon (Shorts + Long-form).")
    logger.info(f"Shorts scheduled for {shorts_time} daily.")
    logger.info(f"Long-form scheduled for {long_time} daily.")
    logger.info("Press Ctrl+C to terminate.")
    
    schedule.every().day.at(shorts_time).do(run_shorts_job)
    schedule.every().day.at(long_time).do(run_long_job)
    
    # Run once immediately on startup if --now is specified
    if "--now" in sys.argv:
        logger.info("Running initial pipeline check (generating both formats)...")
        run_shorts_job()
        run_long_job()
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(10) # check every 10 seconds
        except KeyboardInterrupt:
            logger.info("Scheduler daemon stopped by user request.")
            break
        except Exception as e:
            logger.error(f"Scheduler error in loop: {e}")
            time.sleep(30) # pause before retrying loop

if __name__ == "__main__":
    main()
