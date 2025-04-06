import logging
import os
from datetime import datetime

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
ENV_MODE = os.getenv("ENV_MODE", "PROD").upper()

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# Console handler (stdout)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Setup logger
logger = logging.getLogger(os.getenv("LOGGER_NAME", "extractor"))
logger.setLevel(LOG_LEVEL)
logger.addHandler(console_handler)

# Optional: File logging only for dev
if ENV_MODE == "DEV":
    LOG_DIR = "logs"
    os.makedirs(LOG_DIR, exist_ok=True)
    log_filename = os.path.join(LOG_DIR, f"scraper_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_filename, mode='a')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

logger.propagate = False
