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
