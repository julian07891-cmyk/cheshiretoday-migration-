"""Pure composition for the approved Instagram Top Story master."""

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
APPROVED_INSTAGRAM_TOP_STORY_PATH, APPROVED_INSTAGRAM_TOP_STORY_SHA256 = (
    INSTAGRAM_GRAPHIC_MASTERS[INSTAGRAM_TOP_STORY_FORMAT]
)
STORY_WIDTH = 1080
STORY_HEIGHT = 1920
MAX_STORY_HEADLINE_LINES = 3
STORY_HEADLINE_MAX_WIDTH = 936
STORY_HEADLINE_BOTTOM = 1450
STORY_CTA = "READ THE FULL STORY"


def _read_approved_assets() -> tuple[bytes, bytes]:
    try:
        master = APPROVED_INSTAGRAM_TOP_STORY_PATH.read_bytes()
        logo = APPROVED_LOGO_PATH.read_bytes()
    except OSError as exc:
        raise TemplateValidationError("Approved Instagram assets are unavailable") from exc
    if hashlib.sha256(master).hexdigest() != APPROVED_INSTAGRAM_TOP_STORY_SHA256:
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


def _replace_image(root: ET.Element, image: object) -> None:
    rect = _placeholder_rect(root, "image")
    geometry = {key: rect.attrib[key] for key in ("x", "y", "width", "height")}
    clip_id = "instagram-story-image-clip"
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
            if not current or _estimated_text_width(candidate, font_size) <= STORY_HEADLINE_MAX_WIDTH:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        line_height = round(font_size * 1.12)
        if (
            len(lines) <= MAX_STORY_HEADLINE_LINES
            and 1215 + (len(lines) - 1) * line_height <= STORY_HEADLINE_BOTTOM
            and all(_estimated_text_width(line, font_size) <= STORY_HEADLINE_MAX_WIDTH for line in lines)
        ):
            return lines, font_size
    raise ArticleValidationError("Article headline is too long for the approved template")


def _replace_headline(root: ET.Element, title: str) -> None:
    lines, font_size = _fit_headline(title)
    line_height = round(font_size * 1.12)
    group = _svg_element("g", {"data-content": "headline", "class": "headline", "fill": "#020617"})
    target = _svg_element("text", {"x": 72, "y": 1215, "font-size": font_size, "font-weight": 700})
    for index, line in enumerate(lines):
        child = _svg_element("tspan", {"x": 72, "y": 1215 + index * line_height})
        child.text = line + (" " if index < len(lines) - 1 else "")
        target.append(child)
    group.append(target)
    _replace_placeholder(root, "headline", group)


def validate_instagram_top_story_svg(svg: bytes) -> None:
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as exc:
        raise TemplateValidationError("Composed Instagram asset is not valid XML") from exc
    if (
        root.attrib.get("width") != str(STORY_WIDTH)
        or root.attrib.get("height") != str(STORY_HEIGHT)
        or root.attrib.get("viewBox") != f"0 0 {STORY_WIDTH} {STORY_HEIGHT}"
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
    master, logo = _read_approved_assets()
    try:
        root = ET.fromstring(master)
    except ET.ParseError as exc:
        raise TemplateValidationError("Approved Instagram template is invalid") from exc
    _replace_logo(root, logo)
    _replace_image(root, image)
    _replace_label(root, "category", "LOCAL NEWS")
    _replace_headline(root, title)
    _replace_label(root, "cta", STORY_CTA)
    svg = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    validate_instagram_top_story_svg(svg)
    return svg
