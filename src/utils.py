"""Utility functions — logging, posted-URL history, datetime parsing."""

import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from dateutil import parser as date_parser

# Beijing Time (UTC+8), used for all timestamps in this project
BJT = timezone(timedelta(hours=8))


def setup_logger(name: str = "ai-facebook") -> logging.Logger:
    """Create a logger that writes to both the console and a timestamped log file.

    The log file is created under LOGS_DIR with a name like run_20260708_223038.log.
    Console output is INFO level; file output is DEBUG level for full detail.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # Avoid duplicate handlers if called multiple times

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler — shows INFO+ to the terminal
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler — captures DEBUG+ for later inspection
    # Import inside function to break circular import (config.settings -> src.utils)
    from config.settings import LOGS_DIR
    log_file = LOGS_DIR / f"run_{datetime.now(BJT).strftime('%Y%m%d_%H%M%S')}.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def load_posted_urls(filepath: Path) -> list[dict]:
    """Load the history of previously posted URLs from a JSON file.

    Each entry is a dict with keys "url" and "posted_at".
    Returns an empty list if the file is missing or corrupt.
    """
    if not filepath.exists():
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def save_posted_url(url: str, filepath: Path, retention_days: int = 30):
    """Append a URL to the history file, removing entries older than retention_days."""
    history = load_posted_urls(filepath)
    cut_off = datetime.now(BJT) - timedelta(days=retention_days)

    # Keep only entries within the retention window
    history = [
        entry for entry in history
        if parse_datetime(entry.get("posted_at", ""))
        and parse_datetime(entry["posted_at"]) > cut_off
    ]
    # Append the new entry
    history.append({
        "url": url,
        "posted_at": datetime.now(BJT).isoformat(),
    })
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def is_already_posted(url: str, filepath: Path) -> bool:
    """Check whether a URL has already been posted (based on history file)."""
    history = load_posted_urls(filepath)
    return any(entry.get("url") == url for entry in history)


def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse a date string from RSS feeds into a timezone-aware datetime.

    Handles RFC 822, ISO 8601, and many other formats via python-dateutil.
    Returns None if parsing fails.
    """
    if not dt_str:
        return None
    try:
        return date_parser.parse(dt_str)
    except (ValueError, TypeError):
        return None
