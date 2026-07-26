"""Pure composition for the approved Facebook Local News social asset.

This module deliberately has no database, route, file-write or publishing code.
Callers provide an already selected article record; the only network operation is
the bounded retrieval of that record's stored featured image.
"""

from __future__ import annotations

import base64
import hashlib
import io
import ipaddress
import re
import socket
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Callable, Mapping
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx
from PIL import Image, UnidentifiedImageError

from backend.app.social_asset_constants import (
    APPROVED_LOGO_PATH,
    APPROVED_LOGO_SHA256,
    APPROVED_MASTER_SHA256,
    MASTER_SVG_PATH,
)

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_REDIRECTS = 4
MIN_IMAGE_WIDTH = 300
MIN_IMAGE_HEIGHT = 200
MAX_IMAGE_DIMENSION = 12_000
MAX_IMAGE_PIXELS = 40_000_000
MAX_HEADLINE_LINES = 4
SUPPORTED_IMAGE_MIME = {
    "image/jpeg": "jpeg",
    "image/png": "png",
    "image/webp": "webp",
}


class SocialAssetError(Exception):
    """Base error suitable for later mapping to a safe API response."""


class ArticleValidationError(SocialAssetError):
    """The supplied article record does not meet the Local News contract."""


class ImageURLValidationError(SocialAssetError):
    """The stored article image URL is unsafe or malformed."""


class ImageFetchError(SocialAssetError):
    """The stored article image could not be retrieved safely."""


class ImageContentError(SocialAssetError):
    """Retrieved bytes do not meet the supported image contract."""


class TemplateValidationError(SocialAssetError):
    """The immutable master or composed SVG violates its contract."""


@dataclass(frozen=True)
class ValidatedImage:
    content: bytes
    mime_type: str
    width: int
    height: int


def validate_mongo_object_id(value: object) -> str:
    mongo_id = str(value or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{24}", mongo_id):
        raise ArticleValidationError("Article identifier is invalid")
    return mongo_id


def _validate_host_addresses(
    host: str,
    port: int,
    resolver: Callable[..., list],
) -> None:
    try:
        addresses = resolver(host, port, type=socket.SOCK_STREAM)
    except (OSError, socket.gaierror) as exc:
        raise ImageURLValidationError("Article image host could not be resolved") from exc
    if not addresses:
        raise ImageURLValidationError("Article image host could not be resolved")

    for address in addresses:
        raw_ip = address[4][0].split("%", 1)[0]
        try:
            parsed_ip = ipaddress.ip_address(raw_ip)
        except ValueError as exc:
            raise ImageURLValidationError("Article image host resolved invalidly") from exc
        if not parsed_ip.is_global:
            raise ImageURLValidationError("Article image host is not publicly routable")


def validate_and_normalize_image_url(
    value: object,
    *,
    resolver: Callable[..., list] = socket.getaddrinfo,
) -> str:
    raw_url = str(value or "").strip()
    if not raw_url:
        raise ArticleValidationError("Article image is required")

    try:
        parsed = urlsplit(raw_url)
        port = parsed.port
    except ValueError as exc:
        raise ImageURLValidationError("Article image URL is invalid") from exc

    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise ImageURLValidationError("Article image URL must use HTTP or HTTPS")
    if parsed.username or parsed.password:
        raise ImageURLValidationError("Article image URL must not contain credentials")
    if not parsed.hostname or any(character.isspace() for character in parsed.hostname):
        raise ImageURLValidationError("Article image URL host is invalid")

    try:
        host = parsed.hostname.encode("idna").decode("ascii").lower().rstrip(".")
    except UnicodeError as exc:
        raise ImageURLValidationError("Article image URL host is invalid") from exc
    if not host or host == "localhost" or host.endswith(".localhost"):
        raise ImageURLValidationError("Article image URL host is not allowed")
    if not re.fullmatch(r"[a-z0-9.-]+", host) and not re.fullmatch(r"[0-9a-f:]+", host):
        raise ImageURLValidationError("Article image URL host is invalid")

    effective_port = port or (443 if scheme == "https" else 80)
    try:
        literal_ip = ipaddress.ip_address(host)
    except ValueError:
        literal_ip = None
    if literal_ip is not None:
        if not literal_ip.is_global:
            raise ImageURLValidationError("Article image host is not publicly routable")
    else:
        _validate_host_addresses(host, effective_port, resolver)

    default_port = (scheme == "https" and effective_port == 443) or (scheme == "http" and effective_port == 80)
    bracketed_host = f"[{host}]" if ":" in host else host
    netloc = bracketed_host if default_port else f"{bracketed_host}:{effective_port}"
    return urlunsplit((scheme, netloc, parsed.path or "/", parsed.query, ""))


def _validate_image_content(content: bytes, mime_type: str) -> ValidatedImage:
    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
        with Image.open(io.BytesIO(content)) as image:
            width, height = image.size
            detected_format = str(image.format or "").lower()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ImageContentError("Article image data is invalid") from exc

    expected_format = SUPPORTED_IMAGE_MIME[mime_type]
    if detected_format != expected_format:
        raise ImageContentError("Article image MIME type does not match its data")
    if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
        raise ImageContentError("Article image dimensions are too small")
    if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION or width * height > MAX_IMAGE_PIXELS:
        raise ImageContentError("Article image dimensions are too large")
    return ValidatedImage(content=content, mime_type=mime_type, width=width, height=height)


def fetch_validated_article_image(
    image_url: object,
    *,
    http_client: httpx.Client | None = None,
    resolver: Callable[..., list] = socket.getaddrinfo,
) -> ValidatedImage:
    """Fetch one stored image with bounded redirects, bytes and dimensions."""
    current_url = validate_and_normalize_image_url(image_url, resolver=resolver)
    owns_client = http_client is None
    client = http_client or httpx.Client(timeout=httpx.Timeout(10.0, connect=5.0), follow_redirects=False)

    try:
        for redirect_count in range(MAX_REDIRECTS + 1):
            try:
                request = client.build_request("GET", current_url, headers={"User-Agent": "CheshireTodaySocialAsset/1.0"})
                response = client.send(request, stream=True)
            except httpx.HTTPError as exc:
                raise ImageFetchError("Article image could not be retrieved") from exc

            try:
                if response.status_code in {301, 302, 303, 307, 308}:
                    if redirect_count >= MAX_REDIRECTS:
                        raise ImageFetchError("Article image redirected too many times")
                    location = response.headers.get("location")
                    if not location:
                        raise ImageFetchError("Article image redirect was invalid")
                    current_url = validate_and_normalize_image_url(
                        urljoin(current_url, location),
                        resolver=resolver,
                    )
                    continue
                if response.status_code != 200:
                    raise ImageFetchError("Article image request was unsuccessful")

                mime_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if mime_type not in SUPPORTED_IMAGE_MIME:
                    raise ImageContentError("Article image type is not supported")
                content_length = response.headers.get("content-length")
                if content_length:
                    try:
                        if int(content_length) > MAX_IMAGE_BYTES:
                            raise ImageContentError("Article image exceeds the size limit")
                    except ValueError as exc:
                        raise ImageContentError("Article image size header is invalid") from exc

                chunks = bytearray()
                for chunk in response.iter_bytes():
                    chunks.extend(chunk)
                    if len(chunks) > MAX_IMAGE_BYTES:
                        raise ImageContentError("Article image exceeds the size limit")
                return _validate_image_content(bytes(chunks), mime_type)
            finally:
                response.close()
    finally:
        if owns_client:
            client.close()

    raise ImageFetchError("Article image could not be retrieved")


def _read_approved_assets() -> tuple[bytes, bytes]:
    try:
        master = MASTER_SVG_PATH.read_bytes()
        logo = APPROVED_LOGO_PATH.read_bytes()
    except OSError as exc:
        raise TemplateValidationError("Approved social asset files are unavailable") from exc
    if hashlib.sha256(master).hexdigest() != APPROVED_MASTER_SHA256:
        raise TemplateValidationError("Approved Facebook template checksum is invalid")
    if hashlib.sha256(logo).hexdigest() != APPROVED_LOGO_SHA256:
        raise TemplateValidationError("Approved Cheshire Today logo checksum is invalid")
    return master, logo


def _find_placeholder(root: ET.Element, name: str) -> tuple[ET.Element, ET.Element]:
    for parent in root.iter():
        for child in list(parent):
            if child.attrib.get("data-placeholder") == name:
                return parent, child
    raise TemplateValidationError(f"Approved template is missing the {name} placeholder")


def _replace_placeholder(root: ET.Element, name: str, replacement: ET.Element) -> None:
    parent, current = _find_placeholder(root, name)
    index = list(parent).index(current)
    parent.remove(current)
    parent.insert(index, replacement)


def _estimated_text_width(text: str, font_size: int) -> float:
    units = 0.0
    for character in text:
        if character in "ilI.,'’!|":
            units += 0.28
        elif character in "mwMW@%&":
            units += 0.88
        elif character == " ":
            units += 0.30
        elif character.isupper():
            units += 0.66
        else:
            units += 0.53
    return units * font_size


def wrap_headline(title: str, *, max_width: int = 448) -> tuple[list[str], int]:
    words = title.split()
    for font_size in range(58, 29, -2):
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if not current or _estimated_text_width(candidate, font_size) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        if len(lines) <= MAX_HEADLINE_LINES and all(_estimated_text_width(line, font_size) <= max_width for line in lines):
            return lines, font_size
    raise ArticleValidationError("Article headline is too long for the approved template")


def _svg_element(tag: str, attributes: Mapping[str, object] | None = None) -> ET.Element:
    return ET.Element(f"{{{SVG_NS}}}{tag}", {key: str(value) for key, value in (attributes or {}).items()})


def _build_composed_svg(root: ET.Element, title: str, category: str, cta: str, image: ValidatedImage, logo: bytes) -> None:
    logo_group = _svg_element("g", {"data-content": "logo"})
    logo_group.append(_svg_element("image", {
        "x": 72, "y": 72, "width": 159.34, "height": 54,
        "preserveAspectRatio": "xMidYMid meet",
        "href": f"data:image/png;base64,{base64.b64encode(logo).decode('ascii')}",
        "data-source-sha256": APPROVED_LOGO_SHA256,
    }))
    _replace_placeholder(root, "logo", logo_group)

    image_group = _svg_element("g", {"data-content": "image"})
    clip = _svg_element("clipPath", {"id": "article-image-clip"})
    clip.append(_svg_element("rect", {"x": 72, "y": 158, "width": 560, "height": 364, "rx": 18}))
    image_group.append(clip)
    image_group.append(_svg_element("image", {
        "x": 72, "y": 158, "width": 560, "height": 364,
        "preserveAspectRatio": "xMidYMid slice", "clip-path": "url(#article-image-clip)",
        "href": f"data:{image.mime_type};base64,{base64.b64encode(image.content).decode('ascii')}",
    }))
    _replace_placeholder(root, "image", image_group)

    category_group = _svg_element("g", {"data-content": "category", "class": "interface"})
    category_group.append(_svg_element("rect", {"x": 900, "y": 74, "width": 228, "height": 50, "rx": 25, "fill": "#1E3A8A"}))
    category_text = _svg_element("text", {"x": 1014, "y": 106, "fill": "#F7F4EE", "text-anchor": "middle", "font-size": 18, "font-weight": 700, "letter-spacing": 2})
    category_text.text = category.upper()
    category_group.append(category_text)
    _replace_placeholder(root, "category", category_group)

    lines, font_size = wrap_headline(title)
    line_height = round(font_size * 1.14)
    headline_group = _svg_element("g", {"data-content": "headline", "class": "headline", "fill": "#020617"})
    headline_text = _svg_element("text", {"x": 680, "y": 220, "font-size": font_size, "font-weight": 700})
    for index, line in enumerate(lines):
        tspan = _svg_element("tspan", {"x": 680, "dy": 0 if index == 0 else line_height})
        tspan.text = line + (" " if index < len(lines) - 1 else "")
        headline_text.append(tspan)
    headline_group.append(headline_text)
    _replace_placeholder(root, "headline", headline_group)

    cta_group = _svg_element("g", {"data-content": "cta", "class": "interface"})
    cta_group.append(_svg_element("rect", {"x": 680, "y": 474, "width": 300, "height": 72, "rx": 10, "fill": "#1E3A8A"}))
    cta_text = _svg_element("text", {"x": 830, "y": 520, "fill": "#F7F4EE", "text-anchor": "middle", "font-size": 23, "font-weight": 700})
    cta_text.text = cta
    cta_group.append(cta_text)
    _replace_placeholder(root, "cta", cta_group)


def validate_composed_svg(svg: bytes) -> None:
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as exc:
        raise TemplateValidationError("Composed social asset is not valid XML") from exc
    if root.attrib.get("width") != "1200" or root.attrib.get("height") != "630" or root.attrib.get("viewBox") != "0 0 1200 630":
        raise TemplateValidationError("Composed social asset dimensions changed")
    for element in root.iter():
        if element.attrib.get("data-placeholder"):
            raise TemplateValidationError("Composed social asset contains an unresolved placeholder")
        if element.attrib.get("id") == "editor-guides" and element.attrib.get("display") != "none":
            raise TemplateValidationError("Editor guides must remain hidden")
        if element.tag.endswith("image"):
            href = element.attrib.get("href", "")
            if not href.startswith("data:image/"):
                raise TemplateValidationError("Composed social asset contains an external image")
    rendered_text = "".join(root.itertext())
    if "IMAGE" in rendered_text or re.search(r"\[[A-Z][A-Z0-9 _-]*\]", rendered_text):
        raise TemplateValidationError("Composed social asset contains visible placeholder text")
    if APPROVED_LOGO_SHA256 not in svg.decode("utf-8"):
        raise TemplateValidationError("Composed social asset does not contain the approved logo")


def compose_facebook_local_news_svg(
    article: Mapping[str, object],
    *,
    cta: str = "READ THE FULL STORY",
    http_client: httpx.Client | None = None,
    resolver: Callable[..., list] = socket.getaddrinfo,
) -> bytes:
    """Return a self-contained approved SVG without persisting any state."""
    validate_mongo_object_id(article.get("mongo_id"))
    title = str(article.get("title") or "").strip()
    if not title:
        raise ArticleValidationError("Article title is required")
    category = str(article.get("category") or "").strip()
    if category != "Local News":
        raise ArticleValidationError("Only Local News articles are supported")
    clean_cta = str(cta or "").strip()
    if not clean_cta or len(clean_cta) > 40:
        raise ArticleValidationError("Call to action is invalid")

    image = fetch_validated_article_image(article.get("image"), http_client=http_client, resolver=resolver)
    master, logo = _read_approved_assets()
    try:
        root = ET.fromstring(master)
    except ET.ParseError as exc:
        raise TemplateValidationError("Approved Facebook template is invalid") from exc
    _build_composed_svg(root, title, category, clean_cta, image, logo)
    svg = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    validate_composed_svg(svg)
    return svg
