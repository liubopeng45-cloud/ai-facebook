"""Post formatted content to a Facebook Page via the Graph API.

Requires a valid Facebook Page Access Token and Page ID.
See README.md for step-by-step instructions on obtaining these.
"""

import logging

import requests

from config.settings import FACEBOOK_PAGE_ACCESS_TOKEN, FACEBOOK_PAGE_ID, FB_API_VERSION

logger = logging.getLogger("ai-facebook")


def post_to_page(message: str, link: str = "") -> bool:
    """Post a message (with optional link) to the configured Facebook Page.

    Uses the Facebook Graph API endpoint /{page-id}/feed.
    The link is passed as a separate parameter so Facebook renders it as
    a rich link preview with thumbnail, title, and description.

    Returns True on success, False on failure. Logs detailed error info,
    including a special warning if the access token appears to be expired.
    """
    # Validate configuration upfront
    if not FACEBOOK_PAGE_ACCESS_TOKEN or not FACEBOOK_PAGE_ID:
        logger.error(
            "Facebook config incomplete: PAGE_ID=%s, TOKEN=%s...",
            FACEBOOK_PAGE_ID or "(empty)",
            FACEBOOK_PAGE_ACCESS_TOKEN[:10] if FACEBOOK_PAGE_ACCESS_TOKEN else "(empty)",
        )
        return False

    url = f"https://graph.facebook.com/{FB_API_VERSION}/{FACEBOOK_PAGE_ID}/feed"
    payload = {
        "message": message,
        "access_token": FACEBOOK_PAGE_ACCESS_TOKEN,
    }
    # If a link is provided, Facebook will render it as a rich preview
    if link:
        payload["link"] = link

    try:
        resp = requests.post(url, data=payload, timeout=30)
        data = resp.json()

        # Success — response includes the new post ID
        if resp.status_code == 200 and "id" in data:
            logger.info("Facebook post success! Post ID: %s", data["id"])
            return True
        else:
            logger.error("Facebook post failed: HTTP %s - %s", resp.status_code, data)

            # Detect token expiry (Facebook error code 190) and give actionable advice
            error = data.get("error", {})
            if error.get("code") == 190 or "token" in str(error).lower():
                logger.error(
                    "Token may have expired. Re-generate at "
                    "https://developers.facebook.com/tools/accesstoken/"
                )
            return False

    except requests.RequestException as e:
        logger.error("Facebook API request error: %s", e)
        return False


def build_post_content(chinese_summary: str, link: str) -> str:
    """Assemble the Facebook post body from the Chinese summary and original link.

    Format:
      (Chinese summary with headline)
      (blank line)
      Link: {original_url}
    """
    parts = [chinese_summary]
    if link:
        parts.append(f"\nLink: {link}")
    return "\n\n".join(parts)
