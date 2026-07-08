"""Configuration center — loads all settings from .env and rss_sources.yaml."""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Project root — derived from this file's location ──
# config/settings.py 的父目录的父目录 = 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── .env loading — try work/ first (gitignored), fallback to project root ──
_env_work = PROJECT_ROOT / "work" / ".env"
_env_root = PROJECT_ROOT / ".env"
if _env_work.exists():
    load_dotenv(_env_work)
elif _env_root.exists():
    load_dotenv(_env_root)

# ── LLM API config ──
# Defaults to DeepSeek API. Change BASE_URL + MODEL to use other OpenAI-compatible providers.
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))          # seconds per API call

# ── Facebook Graph API config ──
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "")
FB_API_VERSION = "v22.0"  # latest stable as of 2026-07

# ── Runtime directory paths ──
WORK_DIR = PROJECT_ROOT / "work"            # runtime state (gitignored)
LOGS_DIR = PROJECT_ROOT / "outputs" / "logs"  # per-run log files (gitignored)
POSTED_URLS_FILE = WORK_DIR / "posted_urls.json"  # dedup history
RSS_SOURCES_FILE = PROJECT_ROOT / "config" / "rss_sources.yaml"

# Ensure output directories exist before any module imports them
WORK_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

APP_NAME = "AI-Facebook Poster"
