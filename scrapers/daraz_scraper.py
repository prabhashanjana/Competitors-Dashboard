import sys
from datetime import datetime

import httpx
from dotenv import load_dotenv
from loguru import logger

from config import (
    DARAZ_MAX_RESULTS,
    DARAZ_CURRENCY,
)

load_dotenv()
logger.add(sys.stderr, format="{time:HH:mm:ss} | {level} | {message}")

DARAZ_API_URL = "https://www.daraz.lk/catalog/?ajax=true&isFirstRequest=true&page=1&q="

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.daraz.lk",
}


async def scrape_daraz(keyword: str) -> list[dict]:
    results = []

    try:
        url = DARAZ_API_URL + keyword.replace(" ", "+")
        logger.info(f"[daraz] searching: {keyword}")

        async with httpx.AsyncClient(headers=HEADERS, timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        items = data.get("mods", {}).get("listItems", [])
        logger.info(f"[daraz] found {len(items)} items")

        for item in items[:DARAZ_MAX_RESULTS]:
            try:
                product_id = str(item.get("itemId", ""))
                name = item.get("name", "").strip()
                price = _parse_price(item.get("price", "0"))
                orig_price = _parse_price(item.get("originalPrice", "0"))
                discount = _parse_discount(item.get("discount", ""))
                rating = _parse_rating(item.get("ratingScore", "0"))
                review_count = int(item.get("review", 0) or 0)
                item_url = "https:" + item.get("itemUrl", "")

                if not product_id or not name:
                    continue

                results.append({
                    "product_id":     product_id,
                    "product_name":   name,
                    "price":          price,
                    "original_price": orig_price,
                    "discount_pct":   discount,
                    "rating":         rating,
                    "review_count":   review_count,
                    "platform":       "daraz",
                    "currency":       DARAZ_CURRENCY,
                    "url":            item_url,
                    "keyword":        keyword,
                    "scraped_at":     datetime.now().isoformat(),
                })

            except Exception as e:
                logger.warning(f"[daraz] item parse failed: {e}")
                continue

    except Exception as e:
        logger.warning(f"[daraz] scrape failed: {e}")

    logger.info(f"[daraz] returning {len(results)} results")
    return results


def _parse_price(raw) -> float:
    try:
        return float(str(raw).replace(",", "").strip())
    except Exception:
        return 0.0


def _parse_discount(raw: str) -> float:
    try:
        return float(raw.replace("% Off", "").strip())
    except Exception:
        return 0.0


def _parse_rating(raw) -> float:
    try:
        return round(float(str(raw)), 1)
    except Exception:
        return 0.0
