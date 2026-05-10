import sys
import random
import asyncio
from datetime import datetime

from dotenv import load_dotenv
from loguru import logger
from playwright.async_api import async_playwright, Page, Locator
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
logger.add("app.log", rotation="1 week")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


async def scrape_amazon(keyword: str) -> list[dict]:
    results: list[dict] = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=HEADLESS,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-features=IsolateOrigins,site-per-process",
                ],
            )

            context = await browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/New_York",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                },
            )

            page = await context.new_page()
            await stealth_async(page)

            # 1. warm up the session by visiting homepage first
            try:
                await page.goto(
                    "https://www.amazon.com/",
                    wait_until="domcontentloaded",
                    timeout=PAGE_TIMEOUT,
                )
                await asyncio.sleep(random.uniform(2, 4))
            except Exception as e:
                logger.warning(f"[amazon] homepage warmup failed: {e}")

            # 2. now hit the search URL
            url = AMAZON_BASE_URL + keyword.replace(" ", "+")
            logger.info(f"[amazon] searching: {keyword}")

            await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)

            # 3. check for bot wall before doing anything else
            if await _is_blocked(page):
                await page.screenshot(path="debug_amazon_blocked.png", full_page=True)
                logger.error(
                    "[amazon] blocked by bot detection — see debug_amazon_blocked.png"
                )
                await browser.close()
                return []

            # 4. wait for the results grid to actually render
            try:
                await page.wait_for_selector(
                    "div[data-component-type='s-search-result']",
                    timeout=15000,
                )
            except Exception:
                await page.screenshot(path="debug_amazon_no_results.png", full_page=True)
                logger.error(
                    "[amazon] no results selector found — see debug_amazon_no_results.png"
                )
                await browser.close()
                return []

            await page.screenshot(path="debug_amazon.png", full_page=True)

            # 5. scroll to trigger lazy-loaded cards + look human
            await _scroll_page(page)

            cards = await page.locator("div[data-component-type='s-search-result']").all()
            logger.info(f"[amazon] found {len(cards)} cards")

            for card in cards[:AMAZON_MAX_RESULTS]:
                try:
                    await asyncio.sleep(random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX))
                    product = await _parse_card(card, keyword)
                    if product:
                        results.append(product)
                except Exception as e:
                    logger.warning(f"[amazon] card parse failed: {e}")
                    continue

            await browser.close()

    except Exception as e:
        logger.error(f"[amazon] scrape failed: {e}")

    logger.info(f"[amazon] returning {len(results)} results")
    return results


async def _is_blocked(page: Page) -> bool:
    """Detect captcha / robot check / sorry pages."""
    if await page.locator("form[action='/errors/validateCaptcha']").count() > 0:
        return True

    title = (await page.title()) or ""
    if "Robot Check" in title or "Sorry!" in title:
        return True

    try:
        body_text = (await page.locator("body").inner_text(timeout=3000)) or ""
    except Exception:
        body_text = ""

    flags = [
        "Enter the characters you see below",
        "automated access",
        "we just need to make sure",
        "To discuss automated access",
    ]
    return any(f.lower() in body_text.lower() for f in flags)


async def _scroll_page(page: Page) -> None:
    """Slowly scroll the page to load lazy content and mimic a human."""
    for _ in range(4):
        await page.mouse.wheel(0, random.randint(800, 1400))
        await asyncio.sleep(random.uniform(0.5, 1.2))
    await page.evaluate("window.scrollTo(0, 0)")
    await asyncio.sleep(random.uniform(0.3, 0.8))


async def _parse_card(card: Locator, keyword: str) -> dict | None:
    asin = await card.get_attribute("data-asin") or ""

    # title
    title_el = card.locator("[data-cy='title-recipe'] h2 span").first
    title = (await title_el.text_content()) if await title_el.count() > 0 else ""

    # current price
    price_el = card.locator(".a-price .a-offscreen").first
    price_raw = (await price_el.text_content()) if await price_el.count() > 0 else ""
    price = _parse_price(price_raw)

    # original / list price (for discount calc)
    original_el = card.locator(".a-price.a-text-price .a-offscreen").first
    original_raw = (await original_el.text_content()) if await original_el.count() > 0 else ""
    original_price = _parse_price(original_raw) or price

    discount_pct = 0.0
    if original_price and price and original_price > price:
        discount_pct = round((original_price - price) /
                             original_price * 100, 2)

    # rating
    rating_el = card.locator(
        "i.a-icon-star-small .a-icon-alt, i.a-icon-star .a-icon-alt"
    ).first
    rating_raw = (await rating_el.text_content()) if await rating_el.count() > 0 else ""
    rating = _parse_rating(rating_raw)

    # review count
    review_el = card.locator(
        "[data-cy='reviews-block'] a span, .a-size-base.s-underline-text"
    ).first
    review_raw = (await review_el.text_content()) if await review_el.count() > 0 else ""
    review_count = _parse_review_count(review_raw)

    # product url
    url_el = card.locator("[data-cy='title-recipe'] a").first
    href = (await url_el.get_attribute("href")) if await url_el.count() > 0 else ""
    if href and href.startswith("/"):
        full_url = f"https://www.amazon.com{href}"
    else:
        full_url = href or ""

    if not asin or not title:
        return None

    return {
        "product_id": asin,
        "product_name": title.strip(),
        "price": price,
        "original_price": original_price,
        "discount_pct": discount_pct,
        "rating": rating,
        "review_count": review_count,
        "platform": "amazon",
        "currency": AMAZON_CURRENCY,
        "url": full_url,
        "keyword": keyword,
        "scraped_at": datetime.now().isoformat(),
    }


def _parse_price(raw: str) -> float:
    if not raw:
        return 0.0
    try:
        cleaned = (
            raw.replace("LKR", "")
            .replace("USD", "")
            .replace("$", "")
            .replace(",", "")
            .strip()
        )
        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0


def _parse_rating(raw: str) -> float:
    if not raw:
        return 0.0
    try:
        return float(raw.split(" ")[0])
    except (ValueError, AttributeError, IndexError):
        return 0.0


def _parse_review_count(raw: str) -> int:
    if not raw:
        return 0
    try:
        cleaned = raw.strip().strip("()").replace(",", "")
        if "K" in cleaned.upper():
            cleaned = cleaned.upper().replace("K", "")
            return int(float(cleaned) * 1000)
        if "M" in cleaned.upper():
            cleaned = cleaned.upper().replace("M", "")
            return int(float(cleaned) * 1_000_000)
        return int(float(cleaned))
    except (ValueError, AttributeError):
        return 0


if __name__ == "__main__":
    async def main():
        items = await scrape_amazon("wireless earbuds")
        logger.info(f"got {len(items)} items")
        for item in items[:5]:
            logger.info(item)

    asyncio.run(main())
