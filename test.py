import sys
import asyncio
from dotenv import load_dotenv
from loguru import logger

from database.storage import init_db, save_results, load_results
from scrapers.amazon_scraper import scrape_amazon
from scrapers.daraz_scraper import scrape_daraz
from scrapers.normalizer import normalize_results

load_dotenv()
logger.add(sys.stderr, format="{time:HH:mm:ss} | {level} | {message}")


async def test_pipeline(keyword: str):
    logger.info(f"=== PIPELINE TEST: {keyword} ===")

    # step 1 — init database
    init_db()
    logger.info("database ready")

    # step 2 — scrape
    amazon_raw = await scrape_amazon(keyword)
    # daraz_raw = await scrape_daraz(keyword)

    logger.info(f"amazon raw: {len(amazon_raw)}")

    # step 3 — normalize
    all_raw = amazon_raw  # + daraz_raw
    clean = normalize_results(all_raw)

    logger.info(f"normalized: {len(clean)} records")

    # step 4 — save
    save_results(clean)

    # step 5 — load back and verify
    df = load_results(keyword)
    logger.info(f"loaded from db: {len(df)} records")
    print(df[["platform", "product_name", "price", "currency"]].to_string())


if __name__ == "__main__":
    asyncio.run(test_pipeline("laptop"))
