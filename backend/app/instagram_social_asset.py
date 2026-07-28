"""Pure composition for approved Cheshire Today Instagram masters."""

from __future__ import annotations

import base64
import hashlib
import re
import socket
import xml.etree.ElementTree as ET
from typing import Callable, Mapping

import httpx

from backend.app.facebook_social_asset import (
    APPROVED_LOGO_SHA256,
    ArticleValidationError,
    ImageContentError,
    ImageFetchError,
    ImageURLValidationError,
    TemplateValidationError,
    _estimated_text_width,
    _find_placeholder,
    _replace_placeholder,
    _svg_element,
    fetch_validated_article_image,
    validate_mongo_object_id,
)
from backend.app.social_asset_constants import (
    APPROVED_LOGO_PATH,
    INSTAGRAM_GRAPHIC_FORMATS,
    INSTAGRAM_GRAPHIC_MASTERS,
)


INSTAGRAM_TOP_STORY_FORMAT = ("story", "top-story")
INSTAGRAM_FEED_FORMAT = ("feed", "local-news")
INSTAGRAM_REELS_COVER_FORMAT = ("reels-cover", "local-news")
APPROVED_INSTAGRAM_TOP_STORY_PATH, APPROVED_INSTAGRAM_TOP_STORY_SHA256 = (
    INSTAGRAM_GRAPHIC_MASTERS[INSTAGRAM_TOP_STORY_FORMAT]
)
APPROVED_INSTAGRAM_FEED_PATH, APPROVED_INSTAGRAM_FEED_SHA256 = (
    INSTAGRAM_GRAPHIC_MASTERS[INSTAGRAM_FEED_FORMAT]
)
APPROVED_INSTAGRAM_REELS_COVER_PATH, APPROVED_INSTAGRAM_REELS_COVER_SHA256 = (
    INSTAGRAM_GRAPHIC_MASTERS[INSTAGRAM_REELS_COVER_FORMAT]
)
STORY_WIDTH = 1080
STORY_HEIGHT = 1920
MAX_STORY_HEADLINE_LINES = 3
STORY_HEADLINE_X = 72
STORY_HEADLINE_RIGHT = 960
STORY_HEADLINE_MAX_WIDTH = STORY_HEADLINE_RIGHT - STORY_HEADLINE_X
STORY_HEADLINE_Y = 1239
STORY_HEADLINE_BOTTOM = 1450
STORY_CTA_Y_OFFSET = 24
STORY_SAFE_BOTTOM = 1620
STORY_CTA = "READ THE FULL STORY"
FEED_WIDTH = 1080
FEED_HEIGHT = 1080
FEED_HEADLINE_X = 72
FEED_HEADLINE_RIGHT = 960
FEED_HEADLINE_Y = 760
FEED_HEADLINE_MAX_WIDTH = FEED_HEADLINE_RIGHT - FEED_HEADLINE_X
FEED_HEADLINE_BOTTOM = 890
FEED_MAX_HEADLINE_LINES = 3
REELS_WIDTH = 1080
REELS_HEIGHT = 1920
REELS_HEADLINE_X = 72
REELS_HEADLINE_RIGHT = 960
REELS_HEADLINE_Y = 1215
REELS_HEADLINE_MAX_WIDTH = REELS_HEADLINE_RIGHT - REELS_HEADLINE_X
REELS_HEADLINE_BOTTOM = 1440
REELS_MAX_HEADLINE_LINES = 3
REELS_SAFE_BOTTOM = 1620
REELS_BADGE = "REEL"
HEADLINE_WIDTH_SAFETY_FACTOR = 1.08


def _safe_headline_width(text: str, font_size: int) -> float:
    """Conservatively bound Playfair text where SVG renderers shape glyphs differently."""
    return _estimated_text_width(text, font_size) * HEADLINE_WIDTH_SAFETY_FACTOR


def _read_approved_assets(
    master_path,
    master_sha256,
) -> tuple[bytes, bytes]:
    try:
        master = master_path.read_bytes()
        logo = APPROVED_LOGO_PATH.read_bytes()
    except OSError as exc:
        raise TemplateValidationError("Approved Instagram assets are unavailable") from exc
    if hashlib.sha256(master).hexdigest() != master_sha256:
        raise TemplateValidationError("Approved Instagram template checksum is invalid")
    if hashlib.sha256(logo).hexdigest() != APPROVED_LOGO_SHA256:
        raise TemplateValidationError("Approved Cheshire Today logo checksum is invalid")
    return master, logo


def _placeholder_rect(root: ET.Element, name: str) -> ET.Element:
    _parent, group = _find_placeholder(root, name)
    rect = next((element for element in group if element.tag.endswith("rect")), None)
    if rect is None:
        raise TemplateValidationError(f"Approved {name} placeholder is invalid")
    return rect


def _replace_logo(root: ET.Element, logo: bytes) -> None:
    rect = _placeholder_rect(root, "logo")
    x = float(rect.attrib["x"])
    y = float(rect.attrib["y"])
    height = float(rect.attrib["height"])
    width = round(height * 159.34 / 54, 2)
    group = _svg_element("g", {"data-content": "logo", "data-logo-variant": "standard"})
    group.append(_svg_element("image", {
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "preserveAspectRatio": "xMidYMid meet",
        "href": f"data:image/png;base64,{base64.b64encode(logo).decode('ascii')}",
        "data-source-sha256": APPROVED_LOGO_SHA256,
    }))
    _replace_placeholder(root, "logo", group)


def _replace_image(root: ET.Element, image: object, clip_id: str = "instagram-story-image-clip") -> None:
    rect = _placeholder_rect(root, "image")
    geometry = {key: rect.attrib[key] for key in ("x", "y", "width", "height")}
    group = _svg_element("g", {"data-content": "image"})
    clip = _svg_element("clipPath", {"id": clip_id})
    clip.append(_svg_element("rect", {**geometry, "rx": rect.attrib.get("rx", 0)}))
    group.append(clip)
    group.append(_svg_element("image", {
        **geometry,
        "preserveAspectRatio": "xMidYMid slice",
        "clip-path": f"url(#{clip_id})",
        "href": f"data:{image.mime_type};base64,{base64.b64encode(image.content).decode('ascii')}",
    }))
    _replace_placeholder(root, "image", group)


def _replace_label(root: ET.Element, name: str, value: str) -> None:
    _parent, group = _find_placeholder(root, name)
    target = next((element for element in group.iter() if element.tag.endswith("text")), None)
    if target is None:
        raise TemplateValidationError(f"Approved {name} placeholder is invalid")
    for child in list(target):
        target.remove(child)
    target.text = value
    group.attrib.pop("data-placeholder", None)
    group.attrib["data-content"] = name


def _fit_headline(title: str) -> tuple[list[str], int]:
    words = title.split()
    for font_size in range(88, 41, -2):
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if not current or _safe_headline_width(candidate, font_size) <= STORY_HEADLINE_MAX_WIDTH:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        line_height = round(font_size * 1.12)
        if (
            len(lines) <= MAX_STORY_HEADLINE_LINES
            and STORY_HEADLINE_Y + (len(lines) - 1) * line_height <= STORY_HEADLINE_BOTTOM
            and all(_safe_headline_width(line, font_size) <= STORY_HEADLINE_MAX_WIDTH for line in lines)
        ):
            return lines, font_size
    raise ArticleValidationError("Article headline is too long for the approved template")


def _replace_headline(root: ET.Element, title: str) -> None:
    lines, font_size = _fit_headline(title)
    line_height = round(font_size * 1.12)
    group = _svg_element("g", {"data-content": "headline", "class": "headline", "fill": "#020617"})
    target = _svg_element(
        "text",
        {"x": STORY_HEADLINE_X, "y": STORY_HEADLINE_Y, "font-size": font_size, "font-weight": 700},
    )
    for index, line in enumerate(lines):
        child = _svg_element(
            "tspan",
            {"x": STORY_HEADLINE_X, "y": STORY_HEADLINE_Y + index * line_height},
        )
        child.text = line + (" " if index < len(lines) - 1 else "")
        target.append(child)
    group.append(target)
    _replace_placeholder(root, "headline", group)


def _fit_format_headline(
    title: str,
    *,
    max_width: int,
    y: int,
    bottom: int,
    max_lines: int,
    largest_font: int,
) -> tuple[list[str], int]:
    words = title.split()
    for font_size in range(largest_font, 35, -2):
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if not current or _safe_headline_width(candidate, font_size) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        line_height = round(font_size * 1.12)
        if (
            len(lines) <= max_lines
            and y + (len(lines) - 1) * line_height <= bottom
            and all(_safe_headline_width(line, font_size) <= max_width for line in lines)
        ):
            return lines, font_size
    raise ArticleValidationError("Article headline is too long for the approved template")


def _replace_format_headline(
    root: ET.Element,
    title: str,
    *,
    x: int,
    y: int,
    max_width: int,
    bottom: int,
    max_lines: int,
    largest_font: int,
) -> None:
    lines, font_size = _fit_format_headline(
        title,
        max_width=max_width,
        y=y,
        bottom=bottom,
        max_lines=max_lines,
        largest_font=largest_font,
    )
    line_height = round(font_size * 1.12)
    group = _svg_element("g", {"data-content": "headline", "class": "headline", "fill": "#020617"})
    target = _svg_element("text", {"x": x, "y": y, "font-size": font_size, "font-weight": 700})
    for index, line in enumerate(lines):
        child = _svg_element("tspan", {"x": x, "y": y + index * line_height})
        child.text = line + (" " if index < len(lines) - 1 else "")
        target.append(child)
    group.append(target)
    _replace_placeholder(root, "headline", group)


def _move_cta_down(root: ET.Element) -> None:
    _parent, group = _find_placeholder(root, "cta")
    for element in group.iter():
        if "y" in element.attrib:
            element.attrib["y"] = str(float(element.attrib["y"]) + STORY_CTA_Y_OFFSET)
    rect = next((element for element in group if element.tag.endswith("rect")), None)
    if rect is None or float(rect.attrib["y"]) + float(rect.attrib["height"]) > STORY_SAFE_BOTTOM:
        raise TemplateValidationError("Approved Instagram CTA exceeds the Story safe area")


def validate_instagram_top_story_svg(svg: bytes) -> None:
    _validate_instagram_svg(svg, width=STORY_WIDTH, height=STORY_HEIGHT)


def _validate_instagram_svg(svg: bytes, *, width: int, height: int) -> None:
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as exc:
        raise TemplateValidationError("Composed Instagram asset is not valid XML") from exc
    if (
        root.attrib.get("width") != str(width)
        or root.attrib.get("height") != str(height)
        or root.attrib.get("viewBox") != f"0 0 {width} {height}"
    ):
        raise TemplateValidationError("Composed Instagram asset dimensions changed")
    for element in root.iter():
        if element.attrib.get("data-placeholder"):
            raise TemplateValidationError("Composed Instagram asset contains an unresolved placeholder")
        if element.attrib.get("id") == "editor-guides" and element.attrib.get("display") != "none":
            raise TemplateValidationError("Editor guides must remain hidden")
        if element.tag.endswith("image") and not element.attrib.get("href", "").startswith("data:image/"):
            raise TemplateValidationError("Composed Instagram asset contains an external image")
    rendered = "".join(root.itertext())
    if re.search(r"\[[A-Z][A-Z0-9 _-]*\]", rendered) or "IMAGE" in rendered or "LOGO" in rendered:
        raise TemplateValidationError("Composed Instagram asset contains visible placeholder text")
    if APPROVED_LOGO_SHA256 not in svg.decode("utf-8"):
        raise TemplateValidationError("Composed Instagram asset does not contain the approved logo")


def compose_instagram_top_story_svg(
    article: Mapping[str, object],
    *,
    http_client: httpx.Client | None = None,
    resolver: Callable[..., list] = socket.getaddrinfo,
) -> bytes:
    if INSTAGRAM_TOP_STORY_FORMAT not in INSTAGRAM_GRAPHIC_FORMATS:
        raise TemplateValidationError("Approved Instagram format is unavailable")
    validate_mongo_object_id(article.get("mongo_id"))
    title = str(article.get("title") or "").strip()
    if not title:
        raise ArticleValidationError("Article title is required")
    if str(article.get("category") or "").strip() != "Local News":
        raise ArticleValidationError("Only Local News articles are supported")
    image = fetch_validated_article_image(
        article.get("image"), http_client=http_client, resolver=resolver
    )
    master, logo = _read_approved_assets(
        APPROVED_INSTAGRAM_TOP_STORY_PATH,
        APPROVED_INSTAGRAM_TOP_STORY_SHA256,
    )
    try:
        root = ET.fromstring(master)
    except ET.ParseError as exc:
        raise TemplateValidationError("Approved Instagram template is invalid") from exc
    _replace_logo(root, logo)
    _replace_image(root, image)
    _replace_label(root, "category", "LOCAL NEWS")
    _replace_headline(root, title)
    _move_cta_down(root)
    _replace_label(root, "cta", STORY_CTA)
    svg = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    validate_instagram_top_story_svg(svg)
    return svg


def _compose_instagram_local_news_svg(
    article: Mapping[str, object],
    *,
    format_key: tuple[str, str],
    width: int,
    height: int,
    headline_x: int,
    headline_y: int,
    headline_max_width: int,
    headline_bottom: int,
    max_headline_lines: int,
    largest_font: int,
    clip_id: str,
    http_client: httpx.Client | None = None,
    resolver: Callable[..., list] = socket.getaddrinfo,
) -> bytes:
    if format_key not in INSTAGRAM_GRAPHIC_FORMATS:
        raise TemplateValidationError("Approved Instagram format is unavailable")
    validate_mongo_object_id(article.get("mongo_id"))
    title = str(article.get("title") or "").strip()
    if not title:
        raise ArticleValidationError("Article title is required")
    if str(article.get("category") or "").strip() != "Local News":
        raise ArticleValidationError("Only Local News articles are supported")
    image = fetch_validated_article_image(
        article.get("image"), http_client=http_client, resolver=resolver
    )
    master_path, master_sha256 = INSTAGRAM_GRAPHIC_MASTERS[format_key]
    master, logo = _read_approved_assets(master_path, master_sha256)
    try:
        root = ET.fromstring(master)
    except ET.ParseError as exc:
        raise TemplateValidationError("Approved Instagram template is invalid") from exc
    _replace_logo(root, logo)
    _replace_image(root, image, clip_id)
    _replace_label(root, "category", "LOCAL NEWS")
    _replace_format_headline(
        root,
        title,
        x=headline_x,
        y=headline_y,
        max_width=headline_max_width,
        bottom=headline_bottom,
        max_lines=max_headline_lines,
        largest_font=largest_font,
    )
    _replace_label(root, "cta", STORY_CTA)
    if format_key == INSTAGRAM_REELS_COVER_FORMAT:
        _replace_label(root, "reel-badge", REELS_BADGE)
    svg = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    _validate_instagram_svg(svg, width=width, height=height)
    return svg


def compose_instagram_feed_svg(
    article: Mapping[str, object],
    *,
    http_client: httpx.Client | None = None,
    resolver: Callable[..., list] = socket.getaddrinfo,
) -> bytes:
    return _compose_instagram_local_news_svg(
        article,
        format_key=INSTAGRAM_FEED_FORMAT,
        width=FEED_WIDTH,
        height=FEED_HEIGHT,
        headline_x=FEED_HEADLINE_X,
        headline_y=FEED_HEADLINE_Y,
        headline_max_width=FEED_HEADLINE_MAX_WIDTH,
        headline_bottom=FEED_HEADLINE_BOTTOM,
        max_headline_lines=FEED_MAX_HEADLINE_LINES,
        largest_font=70,
        clip_id="instagram-feed-image-clip",
        http_client=http_client,
        resolver=resolver,
    )


def compose_instagram_reels_cover_svg(
    article: Mapping[str, object],
    *,
    http_client: httpx.Client | None = None,
    resolver: Callable[..., list] = socket.getaddrinfo,
) -> bytes:
    return _compose_instagram_local_news_svg(
        article,
        format_key=INSTAGRAM_REELS_COVER_FORMAT,
        width=REELS_WIDTH,
        height=REELS_HEIGHT,
        headline_x=REELS_HEADLINE_X,
        headline_y=REELS_HEADLINE_Y,
        headline_max_width=REELS_HEADLINE_MAX_WIDTH,
        headline_bottom=REELS_HEADLINE_BOTTOM,
        max_headline_lines=REELS_MAX_HEADLINE_LINES,
        largest_font=86,
        clip_id="instagram-reels-cover-image-clip",
        http_client=http_client,
        resolver=resolver,
    )
