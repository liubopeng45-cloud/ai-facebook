"""Main entry point — orchestrates the full pipeline:

  1. Fetch and rank AI news from RSS feeds
  2. Generate Chinese summaries via LLM (DeepSeek)
  3. Post to Facebook Page

Designed to be run as a batch job via Windows Task Scheduler.
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path when running from any working directory
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


def main():
    """Run the full AI-news-to-Facebook pipeline once.

    Flow:
      1. Setup logging (console + file)
      2. fetch_and_rank() → list of top articles
      3. For each article: fetch full text → LLM Chinese summary → build post
      4. Post to Facebook Page
      5. Record posted URL to avoid duplicates in future runs
    """
    # Deferred imports to avoid circular dependency:
    #   main.py -> fetch_news -> utils -> settings
    #   main.py -> settings (via import)
    from config.settings import APP_NAME, POSTED_URLS_FILE
    from src.utils import setup_logger, save_posted_url
    from src import fetch_news, summarize, facebook_poster

    logger = setup_logger()
    logger.info("=" * 50)
    logger.info("%s started", APP_NAME)
    logger.info("=" * 50)

    # ── Step 1: Fetch and rank ──
    articles = fetch_news.fetch_and_rank()

    if not articles:
        logger.info("No new articles found, run complete")
        return

    # ── Step 2-3: Process each article ──
    success_count = 0
    for article in articles:
        title = article["title"]
        link = article["link"]
        logger.info("Processing: %s", title)
        logger.info("Link: %s", link)

        # Fetch article text and generate Chinese summary via LLM
        chinese_summary = summarize.process(link, title)
        if not chinese_summary:
            logger.warning("Summary empty, skipping: %s", title)
            continue

        # Assemble post content and publish to Facebook
        post_content = facebook_poster.build_post_content(chinese_summary, link)
        logger.info("Post content preview:\n%s", post_content[:200])

        ok = facebook_poster.post_to_page(post_content, link)
        if ok:
            # Record in history file so we don't post the same article again
            save_posted_url(link, POSTED_URLS_FILE)
            success_count += 1
            logger.info("Post success, recorded: %s", link)
        else:
            logger.error("Post failed: %s", title)

    logger.info("Run complete: success %d / total %d", success_count, len(articles))


if __name__ == "__main__":
    main()
