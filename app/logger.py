import logging
import os

logger = logging.getLogger("noaa_dashboard")
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(filename)s - %(message)s')

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

if not os.getenv("RENDER"):
    LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(LOG_DIR, exist_ok=True)
    LOG_FILE = os.path.join(LOG_DIR, 'dashboard.log')

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

logger = logging.getLogger("noaa_dashboard")