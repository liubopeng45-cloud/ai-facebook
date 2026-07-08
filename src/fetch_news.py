"""Fetch news from RSS feeds, filter duplicates, rank by AI keyword relevance."""

import logging
import re
from datetime import datetime, timedelta
from typing import Any

import feedparser
import requests
import yaml

from config.settings import RSS_SOURCES_FILE, POSTED_URLS_FILE
from src.utils import parse_datetime, is_already_posted, BJT

logger = logging.getLogger("ai-facebook")

NewsItem = dict[str, Any]  # Type alias: {title, link, published, summary, source, score, category}


def load_rss_config() -> dict:
    """Load RSS source list and AI keyword scoring rules from the YAML config file."""
    with open(RSS_SOURCES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_source(url: str, timeout: int = 15) -> list[dict]:
    """Fetch and parse a single RSS feed with a configurable timeout.

    Uses requests.get() for network-level timeout support (feedparser.parse
    does not natively support timeouts), then hands the response text to
    feedparser for parsing.

    Returns a list of feed entries, or an empty list on failure.
    """
    try:
        # Download feed XML with timeout — prevents hanging on slow feeds
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"

        # Parse the downloaded XML
        feed = feedparser.parse(resp.text)
        if feed.bozo and not feed.entries:
            logger.warning("Parse failed or empty: %s", url)
            return []
        return feed.entries
    except requests.RequestException as e:
        logger.warning("Network error fetching %s: %s", url, e)
        return []
    except Exception as e:
        logger.warning("Unexpected error parsing %s: %s", url, e)
        return []


def score_item(title: str, summary: str, keywords: list[dict]) -> int:
    """Calculate a relevance score by counting AI keyword matches (case-insensitive).

    Each keyword match adds its configured score value. Multiple occurrences
    of the same keyword are counted separately.
    """
    text = (title + " " + summary).lower()
    total = 0
    for kw in keywords:
        term = kw["term"].lower()
        # Count all occurrences using regex (word-boundary aware via re.escape)
        count = len(re.findall(re.escape(term), text))
        total += count * kw["score"]
    return total


def should_skip(title: str, skip_keywords: list[str]) -> bool:
    """Return True if the title contains any of the skip keywords (case-insensitive).

    Used to filter out job postings, sponsored content, webinars, etc.
    """
    lower = title.lower()
    return any(kw.lower() in lower for kw in skip_keywords)


def fetch_and_rank() -> list[NewsItem]:
    """Main entry point: fetch all RSS sources → filter → score → return top N articles.

    Pipeline:
      1. Load YAML config (sources, keywords, skip list, limits)
      2. Fetch each RSS source in sequence
      3. Filter: deduplicate by URL, recency check, skip keywords, already-posted check
      4. Score each remaining article by AI keyword relevance
      5. Sort descending, return top max_posts_per_run articles
    """
    config = load_rss_config()
    sources = config.get("sources", [])
    keywords = config.get("keywords", [])
    skip_words = config.get("skip_keywords", [])
    max_posts = config.get("max_posts_per_run", 2)
    freshness = config.get("freshness_hours", 48)

    # Only consider articles published within the freshness window
    cut_off = datetime.now(BJT) - timedelta(hours=freshness)
    all_items: list[NewsItem] = []
    seen_urls: set[str] = set()

    logger.info("Fetching %d RSS sources ...", len(sources))

    for src in sources:
        name = src["name"]
        url = src["url"]
        weight = src.get("weight", 1.0)      # Source importance multiplier
        # category = src.get("category", "other")  # Available for future filtering

        entries = fetch_source(url)
        if not entries:
            continue
        logger.debug("  %s: got %d entries", name, len(entries))

        for entry in entries:
            link = entry.get("link", "")
            if not link or link in seen_urls:
                continue  # Skip entries without a link or already seen in this run
            seen_urls.add(link)

            title = entry.get("title", "").strip()
            pub_date = parse_datetime(entry.get("published", ""))
            summary_text = entry.get("summary", "")

            # Apply filters
            if should_skip(title, skip_words):
                continue
            if pub_date and pub_date < cut_off:
                continue  # Too old
            if is_already_posted(link, POSTED_URLS_FILE):
                continue  # Already posted in a previous run

            # Calculate AI relevance score
            score = score_item(title, summary_text, keywords)
            score = round(score * weight, 1)

            all_items.append({
                "title": title,
                "link": link,
                "published": pub_date,
                "summary": summary_text[:500] if summary_text else "",
                "source": name,
                "score": score,
                "category": src.get("category", "other"),
            })

    # Sort by score descending and take the top N
    all_items.sort(key=lambda x: x["score"], reverse=True)
    top = all_items[:max_posts]

    logger.info("Candidates: %d, selected Top %d", len(all_items), len(top))
    for item in top:
        logger.info("  [score %s] %s - %s", item["score"], item["title"][:60], item["source"])

    return top
