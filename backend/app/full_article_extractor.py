import os
import re
from typing import Optional, Dict, Any

import httpx
from bs4 import BeautifulSoup


DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)

# Very lightweight "readability-ish" extraction:
# - remove common boilerplate nodes
# - prefer <article>, else largest text container
# - return plain text (safe for your current schema)


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _strip_boilerplate(soup: BeautifulSoup) -> None:
    for tag in soup(["script", "style", "noscript", "iframe", "svg", "form"]):
        tag.decompose()

    # Common boilerplate containers
    selectors = [
        "header", "footer", "nav", "aside",
        ".advert", ".ads", ".ad", ".ad-container", ".ad-slot",
        ".cookie", ".cookies", ".newsletter", ".subscribe",
        ".social", ".share", ".sharing",
        ".related", ".recommended", ".promo", ".promotion",
        "[role='navigation']",
    ]
    for sel in selectors:
        for node in soup.select(sel):
            node.decompose()


def _pick_main_node(soup: BeautifulSoup):
    # Prefer semantic article
    article = soup.find("article")
    if article and article.get_text(strip=True):
        return article

    # Fallback: choose the node with the most text among common containers
    candidates = soup.find_all(["main", "div", "section"])
    best = None
    best_len = 0
    for c in candidates:
        txt = c.get_text(" ", strip=True)
        l = len(txt)
        if l > best_len:
            best = c
            best_len = l
    return best


async def fetch_full_article(url: str) -> Dict[str, Any]:
    """
    Fetch & extract full article text from a source URL.

    Fail-open contract:
    - Never raises for common network/site issues
    - Returns {ok: bool, status: str, content: Optional[str], error: Optional[str]}
    """
    enable = os.getenv("ENABLE_FULL_SCRAPE", "0") == "1"
    if not enable:
        return {"ok": False, "status": "disabled", "content": None, "error": None}

    if not url or not url.startswith("http"):
        return {"ok": False, "status": "bad_url", "content": None, "error": None}

    timeout_s = float(os.getenv("FULL_SCRAPE_TIMEOUT_SECONDS", "8"))
    headers = {
        "User-Agent": os.getenv("SCRAPE_USER_AGENT", DEFAULT_UA),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_s, connect=min(3.0, timeout_s)),
            follow_redirects=True,
            headers=headers,
        ) as client:
            r = await client.get(url)

        code = r.status_code
        if code in (401, 403):
            return {"ok": False, "status": "blocked", "content": None, "error": f"http_{code}"}
        if code == 404:
            return {"ok": False, "status": "not_found", "content": None, "error": "http_404"}
        if code >= 400:
            return {"ok": False, "status": "http_error", "content": None, "error": f"http_{code}"}

        html = r.text or ""
        if len(html) < 500:
            return {"ok": False, "status": "too_short", "content": None, "error": "html_too_short"}

        soup = BeautifulSoup(html, "lxml")
        _strip_boilerplate(soup)
        main = _pick_main_node(soup)
        if not main:
            return {"ok": False, "status": "no_content", "content": None, "error": "no_main_node"}

        text = main.get_text("\n", strip=True)
        text = _clean_text(text)

        min_chars = int(os.getenv("FULL_SCRAPE_MIN_CHARS", "600"))
        if len(text) < min_chars:
            return {"ok": False, "status": "extracted_too_short", "content": None, "error": "extracted_short"}

        return {"ok": True, "status": "ok", "content": text, "error": None}

    except httpx.TimeoutException:
        return {"ok": False, "status": "timeout", "content": None, "error": "timeout"}
    except Exception as e:
        return {"ok": False, "status": "failed", "content": None, "error": str(e)[:200]}
