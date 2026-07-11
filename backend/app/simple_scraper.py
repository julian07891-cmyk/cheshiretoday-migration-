import re
from datetime import datetime, timezone
from typing import Dict, Optional
from urllib.parse import urlparse

import requests
import html as html_lib
# Basic, dependency-light HTML -> text extraction.
# Tries <article>, then <main>, then <body>. Removes scripts/styles/nav/footer headers.
# Returns clean text + basic metadata.
def _strip_tags(html_text: str) -> str:
    # Remove scripts/styles/noscript + some heavy non-text elements
    html_text = re.sub(r"(?is)<(script|style|noscript|svg|canvas).*?>.*?</\1>", " ", html_text)
    # Remove common junk blocks (best-effort)
    html_text = re.sub(r"(?is)<(nav|footer|header|aside).*?>.*?</\1>", " ", html_text)
    # Convert <br> and </p> to newlines
    html_text = re.sub(r"(?i)<br\s*/?>", "\\n", html_text)
    html_text = re.sub(r"(?i)</p\s*>", "\\n\\n", html_text)
    # Drop all remaining tags
    text = re.sub(r"(?s)<.*?>", " ", html_text)

    # Decode entities (e.g. &#x27;) and normalize a few common ones
    text = html_lib.unescape(text)
    text = (
        text.replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
    )

    # Remove common invisible junk chars (ZWSP/ZWNJ/BOM)
    text = text.replace("\\u200c", "").replace("\\u200b", "").replace("\\ufeff", "")

    # Collapse whitespace
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s+\n", "\\n\\n", text)
    text = re.sub(r"\n{3,}", "\\n\\n", text)
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
        # Remove common boilerplate lines (publisher UI chrome that makes content look unprofessional)
        # We do this line-by-line to keep genuine paragraphs intact.
        drop_patterns = [
            r"^\s*comments\b.*$",
            r"^\s*news\b\s*$",
            r"^\s*live\b\s*$",
            r"^\s*local democracy reporter\b.*$",
            r"^\s*[0-2]?\d:\d\d,\s*\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\s*$",  # e.g. 06:00, 15 Feb 2026
            r"^\s*sign up\b.*$",
            r"^\s*subscribe\b.*$",
            r"^\s*newsletter\b.*$",
            r"^\s*advertisement\b.*$",
            r"^\s*advertising\b.*$",
            r"^\s*cookie\b.*$",
            r"^\s*privacy\b.*$",
            r"^\s*read more\b.*$",
            r"^\s*related articles\b.*$",
            r"^\s*article continues below\b.*$",
            r"^\s*follow us\b.*$",
            r"^\s*share\b.*$",
            r"^\s*get the .* briefing\b.*$",
            r"^\s*email\s+direct\s+to\s+your\s+inbox\b.*$",
        ]

        lines = [ln.strip() for ln in text.splitlines()]
        cleaned = []
        for ln in lines:
            if not ln:
                cleaned.append("")
                continue
            low = ln.lower()

            if any(re.search(pat, ln, flags=re.IGNORECASE) for pat in drop_patterns):
                continue

            # Drop short bylines / UI crumbs
            if low.startswith("by ") and len(ln) <= 80:
                continue
            if "cookie" in low and len(ln) <= 120:
                continue

            cleaned.append(ln)

        text = "\n".join(cleaned)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()


        # Heuristic: require minimum length
        if len(text) < 600:
            return {"ok": False, "content": text, "title": _extract_title(html), "image": _extract_image(html), "error": "Extracted content too short", "fetched_at": fetched_at}

        return {"ok": True, "content": text, "title": _extract_title(html), "image": _extract_image(html), "error": None, "fetched_at": fetched_at}

    except Exception as e:
        return {"ok": False, "content": "", "title": None, "image": None, "error": str(e), "fetched_at": fetched_at}
