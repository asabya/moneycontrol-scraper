# tests/test_scraper.py
"""Tests for scraper parsing logic.

Fixtures based on real moneycontrol HTML structure (discovered March 2026).
Listing pages: li.clearfix > a[href][title] > h2, with p for summary.
Article pages: .article_schedule span for date, .article_author for author,
               meta[name="news_keywords"] for tags.
"""
import pytest
from scraper import parse_listing_page, parse_article_page


LISTING_HTML = """
<html>
<body>
<div class="fleft">
  <ul>
    <li class="clearfix" id="newslist-0">
      <a href="https://www.moneycontrol.com/news/business/article-1"
         style="text-decoration: none!important;"
         title="Market Rally Continues">
        <img src="thumb.jpg" />
        <h2>Market Rally Continues</h2>
      </a>
      <p>Markets surged today on strong earnings.</p>
      <p></p>
    </li>
    <li class="clearfix" id="newslist-1">
      <a href="https://www.moneycontrol.com/news/business/article-2"
         style="text-decoration: none!important;"
         title="RBI Policy Update">
        <img src="thumb2.jpg" />
        <h2>RBI Policy Update</h2>
      </a>
      <p>RBI keeps rates unchanged in latest meeting.</p>
      <p></p>
    </li>
  </ul>
</div>
</body>
</html>
"""

ARTICLE_HTML = """
<html>
<head>
  <meta name="news_keywords" content="Nifty, Sensex, Markets" />
</head>
<body>
  <h1 class="article_title">Market Rally Continues</h1>
  <div class="article_schedule">
    <span>March 18, 2026</span>
    / 10:30 IST
  </div>
  <div class="article_author">
    John Doe
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
    # Date is not present on listing pages
    assert articles[0]["date"] is None


def test_parse_listing_page_empty():
    articles = parse_listing_page("<html><body></body></html>", "news")
    assert articles == []


def test_parse_article_page():
    metadata = parse_article_page(ARTICLE_HTML)
    assert metadata["author"] == "John Doe"
    assert metadata["tags"] == "Nifty, Sensex, Markets"
    assert metadata["date"] == "2026-03-18"


def test_parse_article_page_missing_metadata():
    metadata = parse_article_page("<html><head></head><body></body></html>")
    assert metadata["author"] is None
    assert metadata["tags"] is None
    assert metadata["date"] is None


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
    assert metadata["date"] is None


def test_parse_article_page_meta_author():
    """When meta[name='author'] is present, it takes priority."""
    html = """
    <html><head>
      <meta name="author" content="Jane Smith" />
    </head><body>
      <div class="article_author">Fallback Author</div>
    </body></html>
    """
    metadata = parse_article_page(html)
    assert metadata["author"] == "Jane Smith"


def test_parse_listing_page_relative_url():
    """Relative URLs should be made absolute."""
    html = """
    <html><body>
    <li class="clearfix">
      <a href="/news/business/test-article-123.html" title="Test Article">
        <h2>Test Article</h2>
      </a>
      <p>A test summary.</p>
    </li>
    </body></html>
    """
    articles = parse_listing_page(html, "business")
    assert len(articles) == 1
    assert articles[0]["url"] == "https://www.moneycontrol.com/news/business/test-article-123.html"
