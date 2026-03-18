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
        lambda row: f'<a href="{html_lib.escape(str(row["url"]))}" target="_blank">{html_lib.escape(str(row["title"]))}</a>',
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
