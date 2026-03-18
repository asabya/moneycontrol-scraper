# tests/test_scraper.py
"""Tests for scraper parsing logic.

NOTE: The HTML fixtures below are PLACEHOLDERS based on expected moneycontrol
structure. They MUST be updated after inspecting actual HTML from the site.
"""
import pytest
from scraper import parse_listing_page, parse_article_page


# Placeholder fixture — update after inspecting real moneycontrol HTML
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
