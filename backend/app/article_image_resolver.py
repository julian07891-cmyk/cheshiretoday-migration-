import re
from typing import Callable
from urllib.parse import urlparse


NEWSQUEST_HOSTS = {
    "www.chesterstandard.co.uk",
    "chesterstandard.co.uk",
    "www.warringtonguardian.co.uk",
    "warringtonguardian.co.uk",
}


def _is_http_url(value: str) -> bool:
    try:
        parsed = urlparse(str(value or "").strip())
    except Exception:
        return False

    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_newsquest_source(source_url: str) -> bool:
    try:
        host = urlparse(str(source_url or "").strip()).netloc.lower()
    except Exception:
        return False

    return host in NEWSQUEST_HOSTS


def _extract_open_graph_image(page_html: str) -> str:
    html = str(page_html or "")
    match = re.search(
        r'<meta[^>]+(?:property|name)=["\']og:image["\'][^>]+'
        r'content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE,
    )
    if not match:
        return ""

    candidate = match.group(1).replace("&amp;", "&").strip()
    return candidate if _is_http_url(candidate) else ""


def resolve_imported_article_image(
    image_url: str,
    source_url: str,
    *,
    fetch_page: Callable[[str], str],
) -> str:
    """
    Resolve a final image URL for an imported article.

    Only recognised Newsquest RSS resource images are upgraded through the
    source page's declared Open Graph image. All failures preserve the
    original image URL.
    """
    original = str(image_url or "").strip()
    source = str(source_url or "").strip()

    if not original:
        return ""

    if "/resources/images/" not in original.lower():
        return original

    if not _is_newsquest_source(source):
        return original

    try:
        page_html = fetch_page(source)
        resolved = _extract_open_graph_image(page_html)
        return resolved or original
    except Exception:
        return original
