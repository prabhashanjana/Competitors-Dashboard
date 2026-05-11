# 🏆 Competitors Dashboard

A market price intelligence tool for shop owners and e-commerce sellers.
Search any product and instantly compare prices across Amazon and Daraz —
understand where the market stands, track competitors, and make smarter pricing decisions.

---

## What It Does

- Search any product by name across Amazon and Daraz simultaneously
- Compare prices, ratings, and discounts side by side
- Track price history over time for specific products
- Identify the best deals and lowest prices in the market
- Store all results locally for historical analysis

---

## Who It Is For

- Shop owners who want to price competitively
- E-commerce sellers researching the market before listing
- Buyers looking for the best deal across platforms

---

## Tech Stack

| Layer | Technology |
|---|---|
| Scraping (Amazon) | Playwright (browser automation) |
| Scraping (Daraz) | httpx (direct API) |
| Data Storage | SQLite |
| Dashboard | Streamlit |
| Data Processing | pandas |
| Logging | loguru |

---

## Architecture
User Input (keyword)
↓
Amazon Scraper (Playwright) + Daraz Scraper (httpx API)
↓
Normalizer (clean + validate)
↓
SQLite Database (store with timestamp)
↓
Streamlit Dashboard (display + analyze)

---

## Project Structure

competitors-dashboard/
├── main.py                  # Entry point — orchestrates everything
├── config.py                # Constants and settings
├── scrapers/
│   ├── amazon_scraper.py    # Playwright-based Amazon scraper
│   ├── daraz_scraper.py     # API-based Daraz scraper
│   └── normalizer.py        # Data cleaning and validation
├── database/
│   └── storage.py           # SQLite read/write operations
└── dashboard/
└── components.py        # Streamlit UI components

---

## Setup

```bash
# Clone the repository
git clone https://github.com/prabhashanjana/competitors-dashboard.git
cd competitors-dashboard

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run the dashboard
streamlit run main.py
```

---

## How To Use

1. Type a product name in the search bar
2. Click **Scrape Fresh** to fetch live data from Amazon and Daraz
3. View the market overview, price comparison table, and best deals
4. Search the same keyword again later to build price history
5. Select a specific product to see its price trend over time

---

## Key Design Decisions

**Why Playwright for Amazon, httpx for Daraz?**
Amazon has no clean public API — browser automation is required.
Daraz exposes a JSON API endpoint — direct HTTP request is faster and more reliable.

**Why SQLite?**
Simple, zero-setup, sufficient for V1. All data persists locally with timestamps,
enabling price history tracking without any external database service.

**Why native currencies?**
Amazon prices are in USD, Daraz in LKR. Converting introduces exchange rate risk.
Showing native currencies gives the most accurate picture for decision making.

---

## Built By

**Prabhashanjana De Alwis**
[![GitHub](https://img.shields.io/badge/GitHub-prabhashanjana-181717?style=flat&logo=github)](https://github.com/prabhashanjana)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Prabhashanjana-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/prabhashanjana)
