from dotenv import load_dotenv
from loguru import logger
import sqlite3
import pandas as pd
import sys

from config import DB_PATH

load_dotenv()
logger.add("app.log", rotation="1 week")


def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id      TEXT,
            product_name    TEXT,
            price           REAL,
            original_price  REAL,
            discount_pct    REAL,
            rating          REAL,
            review_count    INTEGER,
            platform        TEXT,
            currency        TEXT,
            url             TEXT,
            keyword         TEXT,
            scraped_at      TEXT
        )
    """)
        conn.commit()
        conn.close()
        logger.info("[storage] database initialized")
    except Exception as e:
        logger.warning(f"[storage] init_db failed: {e}")


def save_results(records: list[dict]):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.executemany("""
        INSERT INTO products (
            product_id, product_name, price, original_price, discount_pct,
            rating, review_count, platform, currency, url, keyword, scraped_at
        ) VALUES (
            :product_id, :product_name, :price, :original_price, :discount_pct,
            :rating, :review_count, :platform, :currency, :url, :keyword, :scraped_at
        )
    """, records)
        conn.commit()
        conn.close()
        logger.info(f"[storage] saved {len(records)} records")
    except Exception as e:
        logger.warning(f"[storage] save_results failed: {e}")


def load_results(keyword: str) -> pd.DataFrame:
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            "SELECT * FROM products WHERE keyword = ? ORDER BY scraped_at DESC",
            conn,
            params=(keyword,)
        )
        conn.close()
        logger.info(
            f"[storage] loaded {len(df)} records for keyword: {keyword}")
        return df
    except Exception as e:
        logger.warning(f"[storage] load_results failed: {e}")
        return pd.DataFrame()
