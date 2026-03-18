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
