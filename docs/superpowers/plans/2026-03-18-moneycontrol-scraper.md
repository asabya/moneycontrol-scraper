# Moneycontrol News Scraper — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a scraper that fetches news articles from moneycontrol.com, stores them in SQLite, and displays them in a Streamlit dashboard.

**Architecture:** Three modules — `scraper.py` (fetch + parse), `db.py` (SQLite CRUD), `app.py` (Streamlit UI). The scraper uses `cloudscraper` to bypass Cloudflare (with `playwright` fallback), parses with BeautifulSoup, and writes to SQLite. The dashboard reads from the same DB.

**Tech Stack:** Python 3, cloudscraper, playwright, beautifulsoup4, sqlite3 (stdlib), python-dateutil, streamlit, pandas, lxml

**Spec:** `docs/superpowers/specs/2026-03-18-moneycontrol-scraper-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `requirements.txt` | Python dependencies |
| `.gitignore` | Exclude data/, __pycache__/, .venv/, debug files |
| `db.py` | SQLite table creation, insert, query, dedup check |
| `scraper.py` | HTTP fetching, HTML parsing, CLI entry point |
| `app.py` | Streamlit dashboard with filters and table |
| `tests/test_db.py` | Tests for db module |
| `tests/test_scraper.py` | Tests for scraper parsing logic |
| `data/` | Directory for articles.db (created at runtime by db.py) |

---

### Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
cloudscraper>=1.2.71
beautifulsoup4>=4.12.0
python-dateutil>=2.8.0
streamlit>=1.30.0
pandas>=2.0.0
lxml>=4.9.0
playwright>=1.40.0
```

- [ ] **Step 2: Create .gitignore**

```
data/
__pycache__/
.venv/
*.pyc
.streamlit/
debug_*.html
```

- [ ] **Step 3: Create empty tests/__init__.py**

```python
```

- [ ] **Step 4: Create virtual env and install dependencies**

Run: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && pip install pytest && playwright install chromium`

- [ ] **Step 5: Commit**

```bash
git init
git add requirements.txt .gitignore tests/__init__.py
git commit -m "chore: project setup with dependencies and gitignore"
```

---

### Task 2: Database Module

**Files:**
- Create: `db.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Write failing tests for db module**

```python
# tests/test_db.py
import os
import sqlite3
import pytest
from db import init_db, insert_article, article_exists, query_articles, get_categories

TEST_DB = "data/test_articles.db"


@pytest.fixture(autouse=True)
def setup_teardown():
    """Create and destroy test database for each test."""
    os.makedirs("data", exist_ok=True)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_init_db_creates_table():
    init_db(TEST_DB)
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='articles'"
    )
    assert cursor.fetchone() is not None
    conn.close()


def test_insert_and_query():
    init_db(TEST_DB)
    article = {
        "title": "Test Article",
        "url": "https://example.com/test",
        "summary": "A test summary",
        "date": "2026-03-18",
        "author": "Test Author",
        "category": "business",
        "tags": "stock,market",
    }
    insert_article(TEST_DB, article)
    results = query_articles(TEST_DB)
    assert len(results) == 1
    assert results[0]["title"] == "Test Article"


def test_article_exists():
    init_db(TEST_DB)
    article = {
        "title": "Test",
        "url": "https://example.com/test",
        "summary": None,
        "date": "2026-03-18",
        "author": None,
        "category": "news",
        "tags": None,
    }
    insert_article(TEST_DB, article)
    assert article_exists(TEST_DB, "https://example.com/test") is True
    assert article_exists(TEST_DB, "https://example.com/other") is False


def test_duplicate_url_ignored():
    init_db(TEST_DB)
    article = {
        "title": "First",
        "url": "https://example.com/test",
        "summary": None,
        "date": "2026-03-18",
        "author": None,
        "category": "news",
        "tags": None,
    }
    insert_article(TEST_DB, article)
    article["title"] = "Second"
    insert_article(TEST_DB, article)
    results = query_articles(TEST_DB)
    assert len(results) == 1
    assert results[0]["title"] == "First"


def test_query_with_filters():
    init_db(TEST_DB)
    articles = [
        {
            "title": "Market Rally",
            "url": "https://example.com/1",
            "summary": "Markets went up",
            "date": "2026-03-18",
            "author": "A",
            "category": "markets",
            "tags": "nifty",
        },
        {
            "title": "Bank News",
            "url": "https://example.com/2",
            "summary": "Banking update",
            "date": "2026-03-17",
            "author": "B",
            "category": "banking",
            "tags": "rbi",
        },
    ]
    for a in articles:
        insert_article(TEST_DB, a)

    # Filter by category
    results = query_articles(TEST_DB, category="markets")
    assert len(results) == 1
    assert results[0]["title"] == "Market Rally"

    # Filter by keyword in title
    results = query_articles(TEST_DB, keyword="Bank")
    assert len(results) == 1
    assert results[0]["title"] == "Bank News"

    # Filter by keyword in summary
    results = query_articles(TEST_DB, keyword="went up")
    assert len(results) == 1
    assert results[0]["title"] == "Market Rally"

    # Filter by date range
    results = query_articles(TEST_DB, date_from="2026-03-18", date_to="2026-03-18")
    assert len(results) == 1
    assert results[0]["title"] == "Market Rally"


def test_get_categories():
    init_db(TEST_DB)
    articles = [
        {"title": "A", "url": "https://example.com/1", "summary": None, "date": "2026-03-18", "author": None, "category": "markets", "tags": None},
        {"title": "B", "url": "https://example.com/2", "summary": None, "date": "2026-03-18", "author": None, "category": "banking", "tags": None},
        {"title": "C", "url": "https://example.com/3", "summary": None, "date": "2026-03-18", "author": None, "category": "markets", "tags": None},
    ]
    for a in articles:
        insert_article(TEST_DB, a)
    cats = get_categories(TEST_DB)
    assert cats == ["banking", "markets"]  # sorted, deduplicated
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/test_db.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'db'`

- [ ] **Step 3: Implement db.py**

```python
# db.py
import os
import sqlite3
from datetime import datetime, timezone


DB_PATH = "data/articles.db"


def _get_conn(db_path):
    """Create a connection with row_factory set."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=DB_PATH):
    """Create the articles table if it doesn't exist."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            summary TEXT,
            date TEXT,
            author TEXT,
            category TEXT,
            tags TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def insert_article(db_path, article):
    """Insert an article, ignoring duplicates by URL."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        INSERT OR IGNORE INTO articles (title, url, summary, date, author, category, tags, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            article.get("title"),
            article.get("url"),
            article.get("summary"),
            article.get("date"),
            article.get("author"),
            article.get("category"),
            article.get("tags"),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def article_exists(db_path, url):
    """Check if an article URL already exists in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT 1 FROM articles WHERE url = ?", (url,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def query_articles(db_path=DB_PATH, keyword=None, category=None, date_from=None, date_to=None):
    """Query articles with optional filters. Returns list of dicts."""
    conn = _get_conn(db_path)

    query = "SELECT * FROM articles WHERE 1=1"
    params = []

    if keyword:
        query += " AND (title LIKE ? COLLATE NOCASE OR summary LIKE ? COLLATE NOCASE)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if category:
        query += " AND category = ?"
        params.append(category)
    if date_from:
        query += " AND date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date <= ?"
        params.append(date_to)

    query += " ORDER BY date DESC"

    cursor = conn.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_categories(db_path=DB_PATH):
    """Return distinct category values from the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT DISTINCT category FROM articles WHERE category IS NOT NULL ORDER BY category")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    return categories
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_db.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add db.py tests/test_db.py
git commit -m "feat: add SQLite database module with CRUD and filtering"
```

---

### Task 3: Scraper — HTML Parsing Logic

**Files:**
- Create: `scraper.py` (parsing functions only — no HTTP imports yet)
- Create: `tests/test_scraper.py`

This task implements the parsing functions with **placeholder** test HTML fixtures. The actual CSS selectors will be discovered and updated in Task 4 when we can inspect real moneycontrol HTML. The tests validate the parsing logic works with the expected structure.

- [ ] **Step 1: Write failing tests with placeholder HTML fixtures**

```python
# tests/test_scraper.py
"""Tests for scraper parsing logic.

NOTE: The HTML fixtures below are PLACEHOLDERS based on expected moneycontrol
structure. They MUST be updated in Task 4 after inspecting actual HTML from the site.
"""
import pytest
from scraper import parse_listing_page, parse_article_page


# Placeholder fixture — update after inspecting real moneycontrol HTML (Task 4)
LISTING_HTML = """
<html>
<body>
<div id="ca498">
  <li class="clearfix">
    <h2><a href="https://www.moneycontrol.com/news/business/article-1" title="Market Rally Continues">Market Rally Continues</a></h2>
    <p>Markets surged today on strong earnings.</p>
    <span class="article_schedule">
      <span>March 18, 2026 10:30 AM IST</span>
    </span>
  </li>
  <li class="clearfix">
    <h2><a href="https://www.moneycontrol.com/news/business/article-2" title="RBI Policy Update">RBI Policy Update</a></h2>
    <p>RBI keeps rates unchanged in latest meeting.</p>
    <span class="article_schedule">
      <span>March 17, 2026 02:00 PM IST</span>
    </span>
  </li>
</div>
</body>
</html>
"""

ARTICLE_HTML = """
<html>
<head>
  <meta name="author" content="John Doe" />
  <meta name="keywords" content="Nifty, Sensex, Markets" />
</head>
<body>
  <h1 class="article_title">Market Rally Continues</h1>
  <div class="article_author">
    <span>John Doe</span>
  </div>
  <div class="tags">
    <a href="/tag/nifty">Nifty</a>
    <a href="/tag/sensex">Sensex</a>
  </div>
</body>
</html>
"""


def test_parse_listing_page():
    articles = parse_listing_page(LISTING_HTML, "business")
    assert len(articles) == 2
    assert articles[0]["title"] == "Market Rally Continues"
    assert articles[0]["url"] == "https://www.moneycontrol.com/news/business/article-1"
    assert articles[0]["category"] == "business"
    assert articles[0]["summary"] == "Markets surged today on strong earnings."
    # Verify date was parsed to ISO format
    assert articles[0]["date"] == "2026-03-18"


def test_parse_listing_page_empty():
    articles = parse_listing_page("<html><body></body></html>", "news")
    assert articles == []


def test_parse_article_page():
    metadata = parse_article_page(ARTICLE_HTML)
    assert metadata["author"] == "John Doe"
    # Tags come from meta keywords as a full string
    assert metadata["tags"] == "Nifty, Sensex, Markets"


def test_parse_article_page_missing_metadata():
    metadata = parse_article_page("<html><head></head><body></body></html>")
    assert metadata["author"] is None
    assert metadata["tags"] is None


def test_parse_article_page_tags_from_links():
    """When meta keywords are absent, tags are extracted from .tags links."""
    html = """
    <html><head></head><body>
      <div class="tags">
        <a href="/tag/rbi">RBI</a>
        <a href="/tag/rates">Interest Rates</a>
      </div>
    </body></html>
    """
    metadata = parse_article_page(html)
    assert metadata["tags"] == "RBI, Interest Rates"
    assert metadata["author"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/test_scraper.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scraper'`

- [ ] **Step 3: Implement parsing functions in scraper.py**

Only include imports needed for parsing — HTTP/CLI imports are added in Task 4.

```python
# scraper.py
"""Moneycontrol news article scraper."""

import logging

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Section URL -> category mapping
SECTIONS = {
    "https://www.moneycontrol.com/news/": "news",
    "https://www.moneycontrol.com/news/business/": "business",
    "https://www.moneycontrol.com/news/business/economy/": "economy",
    "https://www.moneycontrol.com/news/business/companies/": "companies",
    "https://www.moneycontrol.com/news/business/mutual-funds/": "mutual-funds",
    "https://www.moneycontrol.com/news/business/personal-finance/": "personal-finance",
    "https://www.moneycontrol.com/news/business/ipo/": "ipo",
    "https://www.moneycontrol.com/news/business/startup/": "startup",
    "https://www.moneycontrol.com/news/business/real-estate/": "real-estate",
    "https://www.moneycontrol.com/news/business/markets/": "markets",
    "https://www.moneycontrol.com/personal-finance/banking/": "banking",
    "https://www.moneycontrol.com/news/business/cryptocurrency/": "crypto",
}


def parse_listing_page(html, category):
    """Parse a news listing page and return a list of article dicts.

    Each dict has: title, url, summary, date, category.
    Selectors target moneycontrol's listing page structure.
    NOTE: Selectors are placeholders — update after inspecting real HTML.
    """
    soup = BeautifulSoup(html, "lxml")
    articles = []

    # Try known container selectors, fall back to broad match
    items = soup.select("li.clearfix")

    for item in items:
        link_tag = item.select_one("h2 a")
        if not link_tag:
            continue

        title = link_tag.get("title") or link_tag.get_text(strip=True)
        url = link_tag.get("href", "")
        if not url or not title:
            continue

        # Make URL absolute if relative
        if url.startswith("/"):
            url = "https://www.moneycontrol.com" + url

        # Summary: first <p> tag in the item
        summary_tag = item.select_one("p")
        summary = summary_tag.get_text(strip=True) if summary_tag else None

        # Date: inside .article_schedule span
        date = None
        date_tag = item.select_one(".article_schedule span")
        if date_tag:
            try:
                date_text = date_tag.get_text(strip=True)
                parsed_date = dateparser.parse(date_text, fuzzy=True)
                if parsed_date:
                    date = parsed_date.strftime("%Y-%m-%d")
            except (ValueError, OverflowError):
                pass

        articles.append({
            "title": title,
            "url": url,
            "summary": summary,
            "date": date,
            "category": category,
        })

    return articles


def parse_article_page(html):
    """Parse an individual article page for author and tags.

    Returns dict with 'author' and 'tags' keys.
    """
    soup = BeautifulSoup(html, "lxml")

    # Author: try meta tag first, then .article_author
    author = None
    meta_author = soup.select_one('meta[name="author"]')
    if meta_author:
        author = meta_author.get("content")
    else:
        author_tag = soup.select_one(".article_author span")
        if author_tag:
            author = author_tag.get_text(strip=True)

    # Tags: from meta keywords or .tags links
    tags = None
    meta_keywords = soup.select_one('meta[name="keywords"]')
    if meta_keywords:
        tags = meta_keywords.get("content")
    else:
        tag_links = soup.select(".tags a")
        if tag_links:
            tags = ", ".join(t.get_text(strip=True) for t in tag_links)

    return {"author": author, "tags": tags}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_scraper.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scraper.py tests/test_scraper.py
git commit -m "feat: add HTML parsing logic for listing and article pages"
```

---

### Task 4: Scraper — HTTP Fetching, Playwright Fallback, and CLI

**Files:**
- Modify: `scraper.py` (add fetch logic, playwright fallback, and main CLI)

This task adds the actual HTTP fetching with cloudscraper + playwright fallback, retry logic, rate limiting, and the CLI entry point. This is also where you **must** inspect actual moneycontrol HTML and update the selectors in `parse_listing_page()` and `parse_article_page()` and the test fixtures.

- [ ] **Step 1: Add fetch and main functions to scraper.py**

Append the following to `scraper.py` after the existing parsing functions:

```python
import argparse
import time
import random

import cloudscraper

from db import init_db, insert_article, article_exists, DB_PATH


def create_session():
    """Create a cloudscraper session."""
    return cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "darwin", "mobile": False}
    )


def fetch_with_playwright(url):
    """Fallback: fetch a URL using playwright headless browser."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        logger.error(f"Playwright fallback failed for {url}: {e}")
        return None


def fetch_page(session, url, retries=3):
    """Fetch a URL with retry logic. Falls back to playwright on persistent failure."""
    for attempt in range(retries):
        try:
            response = session.get(url, timeout=15)
            if response.status_code == 200:
                return response.text
            elif response.status_code in (500, 502, 503, 504):
                logger.warning(f"Server error {response.status_code} for {url}, retry {attempt + 1}/{retries}")
                time.sleep(2 ** attempt)
                continue
            elif response.status_code == 403:
                logger.warning(f"HTTP 403 for {url}, trying playwright fallback")
                return fetch_with_playwright(url)
            else:
                logger.warning(f"HTTP {response.status_code} for {url}, skipping")
                return None
        except Exception as e:
            logger.warning(f"Request failed for {url}: {e}, retry {attempt + 1}/{retries}")
            time.sleep(2 ** attempt)

    # All cloudscraper retries exhausted — try playwright as last resort
    logger.info(f"Cloudscraper retries exhausted for {url}, trying playwright fallback")
    return fetch_with_playwright(url)


def scrape_section(session, section_url, category, db_path):
    """Scrape a single section: fetch listing, parse articles, fetch details, store."""
    logger.info(f"Scraping section: {category} ({section_url})")

    html = fetch_page(session, section_url)
    if not html:
        logger.warning(f"Could not fetch listing page for {category}")
        return 0

    articles = parse_listing_page(html, category)
    logger.info(f"Found {len(articles)} articles in {category}")

    new_count = 0
    for article in articles:
        if article_exists(db_path, article["url"]):
            continue

        # Fetch article detail page for author/tags
        time.sleep(random.uniform(1, 2))
        detail_html = fetch_page(session, article["url"])
        if detail_html:
            metadata = parse_article_page(detail_html)
            article["author"] = metadata["author"]
            article["tags"] = metadata["tags"]
        else:
            article["author"] = None
            article["tags"] = None

        insert_article(db_path, article)
        new_count += 1
        logger.info(f"  Saved: {article['title'][:60]}")

    return new_count


def main():
    parser = argparse.ArgumentParser(description="Scrape news articles from moneycontrol.com")
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help=f"Scrape only this category. Options: {', '.join(SECTIONS.values())}",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=DB_PATH,
        help="Path to SQLite database file",
    )
    args = parser.parse_args()

    init_db(args.db)
    session = create_session()

    sections_to_scrape = SECTIONS
    if args.category:
        sections_to_scrape = {
            url: cat for url, cat in SECTIONS.items() if cat == args.category
        }
        if not sections_to_scrape:
            logger.error(f"Unknown category: {args.category}")
            logger.info(f"Available: {', '.join(SECTIONS.values())}")
            return

    total_new = 0
    for section_url, category in sections_to_scrape.items():
        count = scrape_section(session, section_url, category, args.db)
        total_new += count
        time.sleep(random.uniform(1, 2))  # Delay between sections

    logger.info(f"Done. {total_new} new articles saved.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Discover actual HTML structure (REQUIRED)**

Fetch a real moneycontrol page and save for inspection:

```bash
source .venv/bin/activate && python -c "
import cloudscraper
s = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'darwin', 'mobile': False})
r = s.get('https://www.moneycontrol.com/news/business/')
with open('debug_listing.html', 'w') as f:
    f.write(r.text)
print(f'Status: {r.status_code}, Length: {len(r.text)}')
"
```

If cloudscraper returns a 403 or challenge page, try the playwright fallback:

```bash
source .venv/bin/activate && python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.moneycontrol.com/news/business/', wait_until='domcontentloaded')
    html = page.content()
    browser.close()
    with open('debug_listing.html', 'w') as f:
        f.write(html)
    print(f'Length: {len(html)}')
"
```

Open `debug_listing.html` in a browser and inspect the DOM to find:
1. The container element for the article list
2. Individual article item selector
3. Title/link selector within each item
4. Summary/excerpt selector
5. Date selector and format

Then do the same for an individual article page (`debug_article.html`) to find author and tags selectors.

- [ ] **Step 3: Update selectors in scraper.py and test fixtures**

Based on the actual HTML inspection, update:
- `parse_listing_page()` CSS selectors in `scraper.py`
- `parse_article_page()` CSS selectors in `scraper.py`
- `LISTING_HTML` fixture in `tests/test_scraper.py`
- `ARTICLE_HTML` fixture in `tests/test_scraper.py`
- Test assertions if the structure differs from expectations

- [ ] **Step 4: Run tests to verify parsing still works with updated fixtures**

Run: `source .venv/bin/activate && python -m pytest tests/test_scraper.py -v`
Expected: All tests PASS with updated fixtures

- [ ] **Step 5: Test manually with a single category**

Run: `source .venv/bin/activate && python scraper.py --category business`

Expected: Log output showing articles being fetched and saved.

- [ ] **Step 6: Run full scrape to verify end-to-end**

Run: `source .venv/bin/activate && python scraper.py`

Expected: Articles from all sections saved to `data/articles.db`.

- [ ] **Step 7: Commit**

```bash
git add scraper.py tests/test_scraper.py
git commit -m "feat: add HTTP fetching with cloudscraper/playwright fallback and CLI"
```

---

### Task 5: Streamlit Dashboard

**Files:**
- Create: `app.py`

- [ ] **Step 1: Create app.py**

```python
# app.py
"""Streamlit dashboard for browsing scraped moneycontrol articles."""

import html as html_lib

import streamlit as st
import pandas as pd

from db import init_db, query_articles, get_categories, DB_PATH

st.set_page_config(page_title="Moneycontrol News", layout="wide")
st.title("Moneycontrol News Articles")

# Initialize DB (ensures table exists)
init_db()

# --- Sidebar Filters ---
st.sidebar.header("Filters")

# Search
keyword = st.sidebar.text_input("Search in title & summary")

# Category filter
categories = get_categories()
selected_category = st.sidebar.selectbox(
    "Category",
    options=["All"] + categories,
)

# Date range filter
col1, col2 = st.sidebar.columns(2)
date_from = col1.date_input("From", value=None)
date_to = col2.date_input("To", value=None)

# --- Query ---
filters = {}
if keyword:
    filters["keyword"] = keyword
if selected_category != "All":
    filters["category"] = selected_category
if date_from:
    filters["date_from"] = date_from.isoformat()
if date_to:
    filters["date_to"] = date_to.isoformat()

articles = query_articles(DB_PATH, **filters)

# --- Display ---
st.markdown(f"**{len(articles)}** articles found")

if articles:
    df = pd.DataFrame(articles)

    # Make title a clickable link — escape title to prevent XSS
    df["Title"] = df.apply(
        lambda row: f'<a href="{html_lib.escape(row["url"])}" target="_blank">{html_lib.escape(str(row["title"]))}</a>',
        axis=1,
    )

    # Select and rename columns for display
    display_df = df[["Title", "summary", "category", "author", "date", "tags"]].copy()
    display_df.columns = ["Title", "Summary", "Category", "Author", "Date", "Tags"]
    display_df = display_df.fillna("")

    # Render as HTML table for clickable links
    st.markdown(
        display_df.to_html(escape=False, index=False),
        unsafe_allow_html=True,
    )
else:
    st.info("No articles found. Run the scraper first: `python scraper.py`")
```

- [ ] **Step 2: Run the dashboard**

Run: `source .venv/bin/activate && streamlit run app.py`

Expected: Browser opens with the dashboard. If the scraper has been run, articles display in a table with clickable titles, category filter, search, and date pickers.

- [ ] **Step 3: Verify all filters work**

Test each filter:
- Type a keyword in search — table filters
- Select a category — table filters
- Pick a date range — table filters
- Combine filters — works together

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: add Streamlit dashboard with search, category, and date filters"
```

---

### Task 6: End-to-End Verification

- [ ] **Step 1: Clean slate test**

```bash
rm -f data/articles.db
source .venv/bin/activate && python scraper.py --category business
```

Expected: Articles scraped and saved.

- [ ] **Step 2: Verify DB contents**

```bash
source .venv/bin/activate && python -c "
from db import query_articles, DB_PATH, init_db
init_db()
articles = query_articles()
print(f'Total articles: {len(articles)}')
for a in articles[:3]:
    print(f'  - {a[\"title\"][:60]} ({a[\"category\"]}, {a[\"date\"]})')
"
```

- [ ] **Step 3: Launch dashboard and verify**

Run: `source .venv/bin/activate && streamlit run app.py`

Verify: Articles display, links work, filters work.

- [ ] **Step 4: Run all tests**

Run: `source .venv/bin/activate && python -m pytest tests/ -v`
Expected: All tests pass.

- [ ] **Step 5: Final commit**

```bash
git add db.py scraper.py app.py tests/
git commit -m "chore: end-to-end verification complete"
```
