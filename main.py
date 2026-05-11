import sys
import asyncio

import streamlit as st
from dotenv import load_dotenv
from loguru import logger

from database.storage import init_db, save_results, load_results
from scrapers.amazon_scraper import scrape_amazon
from scrapers.daraz_scraper import scrape_daraz
from scrapers.normalizer import normalize_results
from dashboard.components import (
    render_search_bar,
    render_market_overview,
    render_comparison_table,
    render_price_distribution,
    render_best_deals,
    render_price_history,
)

load_dotenv()
logger.add(sys.stderr, format="{time:HH:mm:ss} | {level} | {message}")

st.set_page_config(
    page_title="Competitors Dashboard",
    page_icon="🏆",
    layout="wide"
)


def run_scrape(keyword: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _scrape():
        amazon_raw = await scrape_amazon(keyword)
        daraz_raw = await scrape_daraz(keyword)
        return amazon_raw, daraz_raw

    try:
        amazon_raw, daraz_raw = loop.run_until_complete(_scrape())
    finally:
        loop.close()

    all_raw = amazon_raw + daraz_raw
    clean = normalize_results(all_raw)
    save_results(clean)

    logger.info(f"[main] saved {len(clean)} records for: {keyword}")
    return len(amazon_raw), len(daraz_raw)


def main():
    init_db()

    keyword, searched = render_search_bar()

    if searched and keyword:
        with st.spinner(f"Searching for '{keyword}'..."):
            amazon_count, daraz_count = run_scrape(keyword)
        st.success(
            f"Found {amazon_count} Amazon results and "
            f"{daraz_count} Daraz results."
        )

    if keyword:
        df = load_results(keyword)

        if df.empty:
            st.info("No data yet. Click Search to start.")
        else:
            render_market_overview(df)
            st.divider()
            render_comparison_table(df)
            st.divider()

            col1, col2 = st.columns([3, 2])
            with col1:
                render_price_distribution(df)
            with col2:
                render_best_deals(df)

            st.divider()
            render_price_history(keyword)


if __name__ == "__main__":
    main()
