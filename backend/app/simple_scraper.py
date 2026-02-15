import re
from datetime import datetime, timezone
from typing import Dict, Optional
from urllib.parse import urlparse

import requests


# Basic, dependency-light HTML -> text extraction.
# Tries <article>, then <main>, then <body>. Removes scripts/styles/nav/footer headers.
# Returns clean text + basic metadata.
def _strip_tags(html: str) -> str:
    # Remove scripts/styles/noscript
    html = re.sub(r"(?is)<(script|style|noscript|svg|canvas).*?>.*?</\1>", " ", html)
    # Remove common junk blocks (best-effort)
    html = re.sub(r"(?is)<(nav|footer|header|aside).*?>.*?</\1>", " ", html)
    # Convert <br> and </p> to newlines
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    html = re.sub(r"(?i)</p\s*>", "\n\n", html)
    # Drop all remaining tags
    text = re.sub(r"(?s)<.*?>", " ", html)
    # Decode a few common entities
    text = (
        text.replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
    )
    # Collapse whitespace
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s+\n", "\n\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _pick_main_block(html: str) -> str:
    m = re.search(r"(?is)<article\b.*?>.*?</article>", html)
    if m:
        return m.group(0)
    m = re.search(r"(?is)<main\b.*?>.*?</main>", html)
    if m:
        return m.group(0)
    m = re.search(r"(?is)<body\b.*?>.*?</body>", html)
    if m:
        return m.group(0)
    return html


def _extract_title(html: str) -> Optional[str]:
    m = re.search(r"(?is)<meta\s+property=['\"]og:title['\"]\s+content=['\"](.*?)['\"]", html)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    m = re.search(r"(?is)<title\b.*?>(.*?)</title>", html)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    return None


def _extract_image(html: str) -> Optional[str]:
    m = re.search(r"(?is)<meta\s+property=['\"]og:image['\"]\s+content=['\"](.*?)['\"]", html)
    if m:
        return m.group(1).strip()
    return None


def scrape_article(url: str, timeout: int = 15) -> Dict[str, object]:
    """
    Fetches and extracts readable article text from a URL.
    Returns:
      {
        ok: bool,
        content: str,
        title: Optional[str],
        image: Optional[str],
        error: Optional[str],
        fetched_at: ISO8601 UTC
      }
    """
    fetched_at = datetime.now(timezone.utc).isoformat()

    if not url or not isinstance(url, str):
        return {"ok": False, "content": "", "title": None, "image": None, "error": "Missing URL", "fetched_at": fetched_at}

    # Basic sanity check
    try:
        parts = urlparse(url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            return {"ok": False, "content": "", "title": None, "image": None, "error": "Invalid URL", "fetched_at": fetched_at}
    except Exception:
        return {"ok": False, "content": "", "title": None, "image": None, "error": "Invalid URL", "fetched_at": fetched_at}

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; CheshireTodayBot/1.0; +https://cheshiretoday.co.uk)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if r.status_code >= 400:
            return {"ok": False, "content": "", "title": None, "image": None, "error": f"HTTP {r.status_code}", "fetched_at": fetched_at}

        html = r.text or ""
        if len(html) < 400:
            return {"ok": False, "content": "", "title": None, "image": None, "error": "Empty/short HTML", "fetched_at": fetched_at}

        picked = _pick_main_block(html)
        text = _strip_tags(picked)

        # Remove common boilerplate lines
        text = re.sub(r"(?im)^\s*(cookie|privacy|sign up|subscribe|advertisement|advertising)\b.*$", "", text).strip()

        # Heuristic: require minimum length
        if len(text) < 600:
            return {"ok": False, "content": text, "title": _extract_title(html), "image": _extract_image(html), "error": "Extracted content too short", "fetched_at": fetched_at}

        return {"ok": True, "content": text, "title": _extract_title(html), "image": _extract_image(html), "error": None, "fetched_at": fetched_at}

    except Exception as e:
        return {"ok": False, "content": "", "title": None, "image": None, "error": str(e), "fetched_at": fetched_at}
