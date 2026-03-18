# Moneycontrol News Scraper

Scrapes news articles from [moneycontrol.com](https://www.moneycontrol.com), stores them in a local SQLite database, and displays them in a Streamlit dashboard.

## Features

- Scrapes 12 news sections: business, economy, companies, markets, banking, crypto, IPO, mutual funds, personal finance, startup, real estate, and general news
- Extracts title, URL, summary, date, author, and tags for each article
- Deduplicates articles by URL across runs
- Cloudflare bypass with `cloudscraper` + `playwright` headless browser fallback
- Streamlit dashboard with search, category filter, and date range picker

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
uv sync
uv run playwright install chromium
```

## Usage

### Scrape articles

```bash
# Scrape all sections
uv run python scraper.py

# Scrape a single category
uv run python scraper.py --category business
```

Available categories: `news`, `business`, `economy`, `companies`, `mutual-funds`, `personal-finance`, `ipo`, `startup`, `real-estate`, `markets`, `banking`, `crypto`

### Launch dashboard

```bash
uv run streamlit run app.py
```

### Run tests

```bash
uv run pytest tests/ -v
```

## Project Structure

```
├── scraper.py       # News scraper with cloudscraper/playwright
├── db.py            # SQLite storage (CRUD, filtering, dedup)
├── app.py           # Streamlit dashboard
├── pyproject.toml   # Dependencies and project config
└── tests/
    ├── test_db.py
    └── test_scraper.py
```
