from dotenv import load_dotenv
from loguru import logger
import sys

load_dotenv()
logger.add("app.log", rotation="1 week")

# --- Scraper Settings ---
HEADLESS = True
PAGE_TIMEOUT = 30000
SCRAPE_DELAY_MIN = 1.5
SCRAPE_DELAY_MAX = 3.5

# --- Amazon ---
AMAZON_BASE_URL = "https://www.amazon.com/s?k="
AMAZON_MAX_RESULTS = 10

# --- Daraz ---
DARAZ_BASE_URL = "https://www.daraz.lk/catalog/?q="
DARAZ_MAX_RESULTS = 10

# --- Database ---
DB_PATH = "competitors.db"

# --- Currency Labels ---
AMAZON_CURRENCY = "USD"
DARAZ_CURRENCY = "LKR"
