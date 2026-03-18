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
