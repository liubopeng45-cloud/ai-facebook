"""Summarize articles by fetching full text and calling an LLM for Chinese summary.

Uses DeepSeek (or any OpenAI-compatible API) to translate and condense
English AI news articles into concise Chinese summaries suitable for Facebook.
"""

import logging

import requests
from bs4 import BeautifulSoup

from config.settings import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, LLM_TIMEOUT,
)

logger = logging.getLogger("ai-facebook")


def fetch_article_text(url: str, timeout: int = 15) -> str:
    """Download an article HTML page and extract its readable text content.

    Uses requests for the HTTP call and BeautifulSoup for HTML parsing.
    Removes navigation, scripts, and other boilerplate elements.
    Truncates to 8000 characters to avoid exceeding LLM token limits.

    Returns the extracted text, or an empty string on failure.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"

        # Parse HTML and strip non-content elements
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Extract clean text: collapse whitespace, remove empty lines
        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)
        return text[:8000]  # Truncate to fit token limits
    except requests.RequestException as e:
        logger.warning("Failed to fetch article: %s - %s", url, e)
        return ""


def summarize_with_llm(title: str, text: str) -> str:
    """Send article text to the LLM API and return a Chinese summary.

    The prompt instructs the model to:
      - Write an attractive Chinese headline
      - Write a 150-200 character Chinese summary
      - Keep key technical points
      - Use simple, reader-friendly Chinese

    Returns the summary text, or an empty string on failure.
    """
    if not DEEPSEEK_API_KEY:
        logger.error("DEEPSEEK_API_KEY not set, skipping summary")
        return ""

    # Build the instruction prompt for the LLM
    prompt = (
        "You are an AI industry news editor. Summarize the following English article in Chinese.\n\n"
        "Requirements:\n"
        "1. First give an attractive Chinese headline\n"
        "2. Then write a 150-200 character Chinese summary\n"
        "3. Keep key technical points and information\n"
        "4. Use simple, clear Chinese suitable for Facebook readers\n"
        "5. Do not add information not in the original\n\n"
        f"Original title: {title}\n\n"
        f"Original content:\n{text[:7000]}\n\n"
        "Output format:\n"
        "【Chinese Title】\n"
        "(Summary content)"
    )

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,   # Balance between creativity and faithfulness
        "max_tokens": 800,    # Enough for a headline + 200-char summary
    }

    try:
        # Build the full API URL, handling trailing slashes in the base URL
        api_url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/v1/chat/completions"
        resp = requests.post(api_url, headers=headers, json=payload, timeout=LLM_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        logger.info("LLM summary generated (%d chars)", len(content))
        return content
    except requests.RequestException as e:
        logger.error("LLM API call failed: %s", e)
        return ""
    except (KeyError, IndexError, ValueError) as e:
        logger.error("LLM response parse failed: %s", e)
        return ""


def process(url: str, title: str) -> str:
    """Convenience wrapper: fetch article → summarize with LLM → return summary."""
    logger.info("Fetching article: %s", title[:50])
    article_text = fetch_article_text(url)
    if not article_text:
        logger.warning("Could not fetch article content")
        return ""
    logger.info("Article length: %d chars, calling LLM ...", len(article_text))
    return summarize_with_llm(title, article_text)
