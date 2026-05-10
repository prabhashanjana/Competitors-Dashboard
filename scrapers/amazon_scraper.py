import sys
import random
import asyncio
from datetime import datetime

from dotenv import load_dotenv
from loguru import logger
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

from config import (
    HEADLESS,
    PAGE_TIMEOUT,
    SCRAPE_DELAY_MIN,
    SCRAPE_DELAY_MAX,
    AMAZON_BASE_URL,
    AMAZON_MAX_RESULTS,
    AMAZON_CURRENCY,
)

load_dotenv()
logger.add(sys.stderr, format="{time:HH:mm:ss} | {level} | {message}")


async def scrape_amazon(keyword: str) -> list[dict]:
    results = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            page = await browser.new_page()
            await stealth_async(page)

            url = AMAZON_BASE_URL + keyword.replace(" ", "+")
            logger.info(f"[amazon] searching: {keyword}")

            await page.goto(url, wait_until="networkidle", timeout=PAGE_TIMEOUT)
            await page.screenshot(path="debug_amazon.png")

            cards = await page.locator(
                "div[data-component-type='s-search-result']"
            ).all()

            logger.info(f"[amazon] found {len(cards)} cards")

            for card in cards[:AMAZON_MAX_RESULTS]:
                try:
                    await asyncio.sleep(
                        random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX)
                    )

                    asin = await card.get_attribute("data-asin") or ""

                    title_el = card.locator("[data-cy='title-recipe'] h2 span")
                    title = await title_el.text_content() if await title_el.count() > 0 else ""

                    price_el = card.locator(".a-price .a-offscreen").first
                    price_raw = await price_el.text_content() if await price_el.count() > 0 else ""
                    price = _parse_price(price_raw)

                    rating_el = card.locator(".a-icon-alt").first
                    rating_raw = await rating_el.text_content() if await rating_el.count() > 0 else ""
                    rating = _parse_rating(rating_raw)

                    review_el = card.locator(
                        ".a-size-mini.s-underline-text").first
                    review_raw = await review_el.text_content() if await review_el.count() > 0 else ""
                    review_count = _parse_review_count(review_raw)

                    url_el = card.locator("[data-cy='title-recipe'] a").first
                    href = await url_el.get_attribute("href") if await url_el.count() > 0 else ""
                    full_url = f"https://www.amazon.com{href}" if href else ""

                    if not asin or not title:
                        continue

                    results.append({
                        "product_id":     asin,
                        "product_name":   title.strip(),
                        "price":          price,
                        "original_price": price,
                        "discount_pct":   0.0,
                        "rating":         rating,
                        "review_count":   review_count,
                        "platform":       "amazon",
                        "currency":       AMAZON_CURRENCY,
                        "url":            full_url,
                        "keyword":        keyword,
                        "scraped_at":     datetime.now().isoformat(),
                    })

                except Exception as e:
                    logger.warning(f"[amazon] card parse failed: {e}")
                    continue

            await browser.close()

    except Exception as e:
        logger.warning(f"[amazon] scrape failed: {e}")

    logger.info(f"[amazon] returning {len(results)} results")
    return results


def _parse_price(raw: str) -> float:
    try:
        cleaned = raw.replace("LKR", "").replace("USD", "")\
                     .replace("$", "").replace(",", "").strip()
        return float(cleaned)
    except Exception:
        return 0.0


def _parse_rating(raw: str) -> float:
    try:
        return float(raw.split(" ")[0])
    except Exception:
        return 0.0


def _parse_review_count(raw: str) -> int:
    try:
        cleaned = raw.strip().strip("()")
        cleaned = cleaned.replace(",", "").replace("K", "000")
        return int(cleaned)
    except Exception:
        return 0
