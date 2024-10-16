import subprocess
import sys
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG if you want more detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_script(script_name):
    """
    Runs a Python script and checks for errors.
    """
    logger.info(f"Starting script: {script_name}")
    try:
        # Remove stdout and stderr parameters to allow default behavior
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            text=True
        )
        logger.info(f"Completed script: {script_name}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing {script_name}: {e}")
        sys.exit(1)  # Exit the pipeline if a script fails

if __name__ == '__main__':
    # List of scripts to run in order
    scripts = [
        'autotrader_spider.py',       # Script 1: Scraper for all cars
        'car_extractor.py',           # Script 2: Extract cars
        'extract_description_spider.py', # Script 3: Scrape descriptions
        'car_notifier.py'             # Script 4: Notify users
    ]

    for script in scripts:
        run_script(script)
