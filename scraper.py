# scraper.py
"""Moneycontrol news article scraper."""

import argparse
import logging
import random
import time

import cloudscraper
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from db import init_db, insert_article, article_exists, DB_PATH

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
    Real moneycontrol structure: li.clearfix > a[href][title] > h2, li > p for summary.
    Date is not present on listing pages.
    """
    soup = BeautifulSoup(html, "lxml")
    articles = []

    items = soup.select("li.clearfix")

    for item in items:
        # Link wraps the h2: <a href="..." title="..."><h2>Title</h2></a>
        link_tag = item.select_one("a[href]")
        if not link_tag:
            continue

        # Only consider items that have an h2 inside the link (actual articles)
        h2_tag = link_tag.select_one("h2")
        if not h2_tag:
            continue

        title = link_tag.get("title") or h2_tag.get_text(strip=True)
        url = link_tag.get("href", "")
        if not url or not title:
            continue

        # Make URL absolute if relative
        if url.startswith("/"):
            url = "https://www.moneycontrol.com" + url

        # Summary: first <p> tag in the item (sibling of the <a>)
        summary_tag = item.select_one("p")
        summary = summary_tag.get_text(strip=True) if summary_tag else None
        # Skip empty summary paragraphs
        if summary == "":
            summary = None

        # Date: not present on listing pages, will be fetched from article page
        date = None

        articles.append({
            "title": title,
            "url": url,
            "summary": summary,
            "date": date,
            "category": category,
        })

    return articles


def parse_article_page(html):
    """Parse an individual article page for date, author and tags.

    Returns dict with 'date', 'author' and 'tags' keys.
    Real moneycontrol structure:
    - Date: .article_schedule span (e.g. "March 18, 2026")
    - Author: .article_author (direct text, e.g. "Broker Research")
    - Tags: meta[name="news_keywords"] or meta[name="Keywords"]
    """
    soup = BeautifulSoup(html, "lxml")

    # Date: inside .article_schedule span
    date = None
    date_tag = soup.select_one(".article_schedule span")
    if date_tag:
        try:
            date_text = date_tag.get_text(strip=True)
            parsed_date = dateparser.parse(date_text, fuzzy=True)
            if parsed_date:
                date = parsed_date.strftime("%Y-%m-%d")
        except (ValueError, OverflowError):
            pass

    # Author: try meta tag first, then .article_author (direct text)
    author = None
    meta_author = soup.select_one('meta[name="author"]')
    if meta_author:
        author = meta_author.get("content")
    else:
        author_tag = soup.select_one(".article_author")
        if author_tag:
            author = author_tag.get_text(strip=True)

    # Tags: from meta news_keywords, meta Keywords, or .tags links
    tags = None
    meta_keywords = soup.select_one('meta[name="news_keywords"]')
    if not meta_keywords:
        meta_keywords = soup.select_one('meta[name="Keywords"]')
    if meta_keywords:
        tags = meta_keywords.get("content")
    else:
        tag_links = soup.select(".tags a")
        if tag_links:
            tags = ", ".join(t.get_text(strip=True) for t in tag_links)

    return {"date": date, "author": author, "tags": tags}


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

        time.sleep(random.uniform(1, 2))
        detail_html = fetch_page(session, article["url"])
        if detail_html:
            metadata = parse_article_page(detail_html)
            article["date"] = metadata["date"]
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
        time.sleep(random.uniform(1, 2))

    logger.info(f"Done. {total_new} new articles saved.")


if __name__ == "__main__":
    main()
