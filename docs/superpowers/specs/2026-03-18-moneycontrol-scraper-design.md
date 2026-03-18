# Moneycontrol News Scraper — Design Spec

## Overview

A Python-based scraper that fetches news articles from moneycontrol.com, stores them in a local SQLite database, and displays them in a Streamlit dashboard with search and filtering.

## Architecture

```
moneycontrol-scraper/
├── scraper.py          # Fetches & parses news articles
├── db.py               # SQLite helpers (create, insert, query)
├── app.py              # Streamlit dashboard
├── requirements.txt    # Dependencies
├── .gitignore          # Excludes data/, __pycache__/, .venv/
└── data/
    └── articles.db     # SQLite database (created at runtime)
```

Three modules, each with one responsibility. The scraper writes to the DB, the dashboard reads from it.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Target Sections

Category is derived from the source URL, not parsed from HTML.

| Category | URL | Category Value |
|----------|-----|----------------|
| News (general) | `https://www.moneycontrol.com/news/` | `news` |
| Business | `https://www.moneycontrol.com/news/business/` | `business` |
| Economy | `https://www.moneycontrol.com/news/business/economy/` | `economy` |
| Companies | `https://www.moneycontrol.com/news/business/companies/` | `companies` |
| Mutual Funds | `https://www.moneycontrol.com/news/business/mutual-funds/` | `mutual-funds` |
| Personal Finance | `https://www.moneycontrol.com/news/business/personal-finance/` | `personal-finance` |
| IPO | `https://www.moneycontrol.com/news/business/ipo/` | `ipo` |
| Startup | `https://www.moneycontrol.com/news/business/startup/` | `startup` |
| Real Estate | `https://www.moneycontrol.com/news/business/real-estate/` | `real-estate` |
| Markets | `https://www.moneycontrol.com/news/business/markets/` | `markets` |
| Banking | `https://www.moneycontrol.com/personal-finance/banking/` | `banking` |
| Cryptocurrency | `https://www.moneycontrol.com/news/business/cryptocurrency/` | `crypto` |

Note: Market data pages (`/stocksmarketsindia/`, `/markets/indian-indices/`) are excluded — they are data dashboards, not news listings. The actual markets news lives at `/news/business/markets/`.

## Data Model

Single `articles` table in SQLite:

| Column     | Type    | Notes                          |
|------------|---------|--------------------------------|
| id         | INTEGER | Primary key, auto-increment    |
| title      | TEXT    | Article headline               |
| url        | TEXT    | Unique constraint, dedup key   |
| summary    | TEXT    | Excerpt from listing page (nullable) |
| date       | TEXT    | Publication date (ISO format)  |
| author     | TEXT    | Author name (nullable)         |
| category   | TEXT    | Derived from source URL (see mapping above) |
| tags       | TEXT    | Comma-separated related topics (nullable) |
| created_at | TEXT    | Timestamp when scraped         |

URL serves as the unique key to prevent duplicate articles across runs.

Tags are stored as comma-separated text. This limits query precision (LIKE-based matching) but is acceptable for this scale.

## Scraper Design

### Flow
1. Parse CLI arguments (optional `--category` filter)
2. Iterate through target section URLs (filtered if `--category` specified)
3. Fetch each news listing page, parse article links, titles, summaries, and dates
4. For each article URL, check if it already exists in the DB (skip if so)
5. Fetch individual article pages to extract author and tags from metadata
6. Insert into SQLite
7. Log summary of new articles added per category

### Anti-Bot Handling

Moneycontrol uses Cloudflare protection. Strategy:

- **Primary:** Use `cloudscraper` library which handles Cloudflare JS challenges automatically
- **Session reuse:** Use a single `cloudscraper.create_scraper()` session for all requests (connection pooling + consistent TLS fingerprint)
- **Fallback:** If `cloudscraper` fails, fall back to `playwright` headless browser

### Technical Details
- **HTTP client:** `cloudscraper` (Cloudflare bypass) with `playwright` fallback
- **HTML parsing:** `beautifulsoup4`
- **Rate limiting:** 1-2 second random delay between requests
- **Logging:** Python `logging` module, INFO to console
- **Retry logic:** 3 retries with exponential backoff for 5xx and timeout errors; skip on 403/404
- **Date parsing:** Use `python-dateutil` for flexible parsing of moneycontrol's date formats (e.g., "March 18, 2026 10:30 AM IST", relative dates). Store as ISO 8601.
- **Deduplication:** Check URL existence in DB before fetching article detail page
- **CLI:** `python scraper.py [--category <name>]` via `argparse`

## Dashboard Design (Streamlit)

### Layout
1. **Title/header** at top
2. **Search bar** — filters articles by keyword in title and summary
3. **Category dropdown** — populated dynamically from DB categories
4. **Date range picker** — filter by publication date
5. **Results table** — displays matching articles, sorted by date descending (newest first)

### Table Columns
- Title (with clickable link to original article URL)
- Summary
- Category
- Author
- Date
- Tags

### Invocation
`streamlit run app.py`

## Dependencies

- `cloudscraper` — HTTP client with Cloudflare bypass
- `beautifulsoup4` — HTML parsing
- `python-dateutil` — Flexible date parsing
- `streamlit` — Dashboard UI
- `pandas` — Data handling for Streamlit table
- `playwright` — Headless browser fallback (optional)

## Risks

- **Anti-bot escalation:** Moneycontrol may upgrade protections beyond what `cloudscraper` handles. `playwright` fallback mitigates this but is slower.
- **HTML structure changes:** Scraper depends on specific CSS selectors which may change without notice.
- **Rate limiting/IP blocking:** Aggressive scraping may trigger blocks. The 1-2s delay mitigates this.

## Non-Goals

- No scheduled/automated scraping
- No full article body text storage (summary from listing page only)
- No sentiment analysis or NLP
- No pagination beyond the first listing page (initial version)
