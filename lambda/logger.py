import logging
import os
from datetime import datetime

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Create log directory if needed
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Log file name based on date
log_filename = os.path.join(LOG_DIR, f"scraper_{datetime.now().strftime('%Y%m%d')}.log")

# Formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# File handler (append mode)
file_handler = logging.FileHandler(log_filename, mode='a')
file_handler.setFormatter(formatter)

# Setup logger
logger = logging.getLogger("extractor")
logger.setLevel(LOG_LEVEL)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Optional: disable propagation to avoid duplicate logs in root logger
logger.propagate = False
