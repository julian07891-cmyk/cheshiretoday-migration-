"""Allow-listed composition for the remaining approved Facebook masters."""

from __future__ import annotations

import base64
import hashlib
import re
import socket
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Mapping

import httpx

from backend.app.facebook_newsletter_asset import _build_inverse_logo
from backend.app.facebook_social_asset import (
    APPROVED_LOGO_SHA256,
    ArticleValidationError,
    TemplateValidationError,
    _find_placeholder,
    _estimated_text_width,
    _replace_placeholder,
    _svg_element,
    fetch_validated_article_image,
    validate_composed_svg,
    validate_mongo_object_id,
    wrap_headline,
)
from backend.app.social_asset_constants import (
    APPROVED_LOGO_PATH,
    FACEBOOK_GRAPHIC_MASTERS,
)


QUOTE_MAX_LENGTH = 240
ATTRIBUTION_MAX_LENGTH = 80
POLL_QUESTION_MAX_LENGTH = 140
POLL_OPTION_MAX_LENGTH = 48
FORBIDDEN_EDITOR_TEXT_RE = re.compile(
    r"(?:https?://|www\.|mailto:|ftp:|file:|data:|javascript:|<\s*/?\s*[a-z!][^>]*(?:>|$))",
    re.I,
)


@dataclass(frozen=True)
class GraphicType:
    label: str
    categories: frozenset[str] | None
    logo_variant: str
    cta: str


GRAPHIC_TYPES = MappingProxyType({
    "business": GraphicType("BUSINESS", frozenset({"Business", "Finance"}), "standard", "READ THE FULL STORY"),
    "property": GraphicType("PROPERTY", frozenset({"Property"}), "inverse", "READ THE FULL STORY"),
    "ai-tech": GraphicType("AI & TECH", frozenset({"AI & Tech"}), "inverse", "READ THE FULL STORY"),
    "breaking-news": GraphicType("BREAKING", None, "inverse", "LATEST UPDATE"),
    "event": GraphicType("EVENT", frozenset({"Entertainment"}), "standard", "FIND OUT MORE"),
    "quote": GraphicType("QUOTE", None, "standard", "VERIFIED QUOTE"),
    "poll": GraphicType("YOUR VIEW", None, "standard", "REPLY IN COMMENTS"),
})
ARTICLE_GRAPHIC_TYPES = frozenset(
    {"business", "property", "ai-tech", "breaking-news", "event"}
)


def validate_editor_text(value: object, *, label: str, maximum: int) -> str:
    text = str(value or "").strip()
    if not text or len(text) > maximum or FORBIDDEN_EDITOR_TEXT_RE.search(text):
        raise ArticleValidationError(f"{label} is invalid")
    return text


def _read_assets(graphic_type: str) -> tuple[bytes, bytes]:
    try:
        path, checksum = FACEBOOK_GRAPHIC_MASTERS[graphic_type]
        master = path.read_bytes()
        logo = APPROVED_LOGO_PATH.read_bytes()
    except (KeyError, OSError) as exc:
        raise TemplateValidationError("Approved Facebook assets are unavailable") from exc
    if hashlib.sha256(master).hexdigest() != checksum:
        raise TemplateValidationError("Approved Facebook template checksum is invalid")
    if hashlib.sha256(logo).hexdigest() != APPROVED_LOGO_SHA256:
        raise TemplateValidationError("Approved Cheshire Today logo checksum is invalid")
    return master, logo


def _replace_logo(root: ET.Element, logo: bytes, variant: str) -> None:
    content = _build_inverse_logo(logo) if variant == "inverse" else logo
    group = _svg_element("g", {"data-content": "logo", "data-logo-variant": variant})
    group.append(_svg_element("image", {
        "x": 72, "y": 72, "width": 159.34, "height": 54,
        "preserveAspectRatio": "xMidYMid meet",
        "href": f"data:image/png;base64,{base64.b64encode(content).decode('ascii')}",
        "data-source-sha256": APPROVED_LOGO_SHA256,
    }))
    _replace_placeholder(root, "logo", group)


def _replace_image(root: ET.Element, image: object) -> None:
    _parent, placeholder = _find_placeholder(root, "image")
    rect = next((item for item in placeholder if item.tag.endswith("rect")), None)
    if rect is None:
        raise TemplateValidationError("Approved template image box is invalid")
    x, y, width, height = (rect.attrib[key] for key in ("x", "y", "width", "height"))
    clip_id = "article-image-clip"
    group = _svg_element("g", {"data-content": "image"})
    clip = _svg_element("clipPath", {"id": clip_id})
    clip.append(_svg_element("rect", {"x": x, "y": y, "width": width, "height": height, "rx": rect.attrib.get("rx", 0)}))
    group.append(clip)
    group.append(_svg_element("image", {
        "x": x, "y": y, "width": width, "height": height,
        "preserveAspectRatio": "xMidYMid slice", "clip-path": f"url(#{clip_id})",
        "href": f"data:{image.mime_type};base64,{base64.b64encode(image.content).decode('ascii')}",
    }))
    _replace_placeholder(root, "image", group)


def _replace_group_text(root: ET.Element, placeholder: str, values: list[str]) -> None:
    _parent, group = _find_placeholder(root, placeholder)
    targets = [item for item in group.iter() if item.tag.endswith("text") and "[" in "".join(item.itertext())]
    if not targets and placeholder == "category":
        targets = [item for item in group.iter() if item.tag.endswith("text")]
    if len(targets) < len(values):
        raise TemplateValidationError(f"Approved {placeholder} placeholder is invalid")
    for target, value in zip(targets, values):
        for child in list(target):
            target.remove(child)
        target.text = value
    group.attrib.pop("data-placeholder", None)
    group.attrib["data-content"] = placeholder


def _wrap_fitted_text(text: str, font_size: int, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for character in text:
        candidate = current + character
        if not current or _estimated_text_width(candidate, font_size) <= max_width:
            current = candidate
        else:
            lines.append(current.rstrip())
            current = character.lstrip()
    if current:
        lines.append(current.rstrip())
    return lines


def _fit_text(text: str, *, max_width: int, max_lines: int, maximum_font: int, minimum_font: int) -> tuple[list[str], int]:
    for font_size in range(maximum_font, minimum_font - 1, -1):
        lines = _wrap_fitted_text(text, font_size, max_width)
        if len(lines) <= max_lines and all(
            _estimated_text_width(line, font_size) <= max_width for line in lines
        ):
            return lines, font_size
    raise ArticleValidationError("Editor text cannot fit the approved template")


def _replace_fitted_group_text(
    root: ET.Element,
    placeholder: str,
    values: list[str],
    *,
    max_width: int,
    max_lines: int = 2,
    minimum_font: int = 12,
) -> None:
    _parent, group = _find_placeholder(root, placeholder)
    targets = [
        item for item in group.iter()
        if item.tag.endswith("text") and "[" in "".join(item.itertext())
    ]
    if len(targets) < len(values):
        raise TemplateValidationError(f"Approved {placeholder} placeholder is invalid")
    for target, value in zip(targets, values):
        maximum_font = int(float(target.attrib.get("font-size", 20)))
        lines, font_size = _fit_text(
            value,
            max_width=max_width,
            max_lines=max_lines,
            maximum_font=maximum_font,
            minimum_font=minimum_font,
        )
        x = target.attrib.get("x", "0")
        original_y = float(target.attrib.get("y", "0"))
        line_height = round(font_size * 1.15)
        first_y = original_y - ((len(lines) - 1) * line_height / 2)
        for child in list(target):
            target.remove(child)
        target.text = None
        target.attrib["font-size"] = str(font_size)
        target.attrib["data-fit-width"] = str(max_width)
        target.attrib["data-fit-lines"] = str(max_lines)
        for index, line in enumerate(lines):
            tspan = _svg_element(
                "tspan",
                {"x": x, "y": first_y + index * line_height},
            )
            tspan.text = line
            target.append(tspan)
    group.attrib.pop("data-placeholder", None)
    group.attrib["data-content"] = placeholder


def _replace_headline(root: ET.Element, value: str) -> None:
    _parent, group = _find_placeholder(root, "headline")
    target = next((item for item in group.iter() if item.tag.endswith("text") and "[" in "".join(item.itertext())), None)
    if target is None:
        raise TemplateValidationError("Approved headline placeholder is invalid")
    x = int(float(target.attrib.get("x", 680)))
    max_width = max(300, 1128 - x)
    lines, font_size = wrap_headline(value, max_width=max_width)
    for child in list(target):
        target.remove(child)
    target.text = None
    target.attrib["font-size"] = str(min(font_size, int(float(target.attrib.get("font-size", font_size)))))
    for index, line in enumerate(lines):
        tspan = _svg_element("tspan", {"x": x, "dy": 0 if index == 0 else round(font_size * 1.14)})
        tspan.text = line + (" " if index < len(lines) - 1 else "")
        target.append(tspan)
    group.attrib.pop("data-placeholder", None)
    group.attrib["data-content"] = "headline"


def _remove_placeholder(root: ET.Element, name: str) -> None:
    parent, group = _find_placeholder(root, name)
    parent.remove(group)


def compose_facebook_graphic_svg(
    article: Mapping[str, object], graphic_type: str, *, quote: object = None,
    attribution: object = None, question: object = None, option_a: object = None,
    option_b: object = None, http_client: httpx.Client | None = None,
    resolver: Callable[..., list] = socket.getaddrinfo,
) -> bytes:
    definition = GRAPHIC_TYPES.get(graphic_type)
    if definition is None:
        raise ArticleValidationError("Graphic type is unsupported")
    validate_mongo_object_id(article.get("mongo_id"))
    title = str(article.get("title") or "").strip()
    category = str(article.get("category") or "").strip()
    if not title:
        raise ArticleValidationError("Article title is required")
    if definition.categories is not None and category not in definition.categories:
        raise ArticleValidationError("Article category is unsupported for this graphic")

    image = fetch_validated_article_image(article.get("image"), http_client=http_client, resolver=resolver)
    master, logo = _read_assets(graphic_type)
    try:
        root = ET.fromstring(master)
    except ET.ParseError as exc:
        raise TemplateValidationError("Approved Facebook template is invalid") from exc
    _replace_logo(root, logo, definition.logo_variant)
    _replace_image(root, image)
    _replace_group_text(root, "category", [definition.label])

    if graphic_type == "quote":
        verified_quote = validate_editor_text(quote, label="Quote", maximum=QUOTE_MAX_LENGTH)
        verified_attribution = validate_editor_text(attribution, label="Attribution", maximum=ATTRIBUTION_MAX_LENGTH)
        _replace_headline(root, verified_quote)
        _replace_fitted_group_text(
            root,
            "cta",
            [verified_attribution],
            max_width=276,
        )
    elif graphic_type == "poll":
        poll_question = validate_editor_text(question, label="Poll question", maximum=POLL_QUESTION_MAX_LENGTH)
        first = validate_editor_text(option_a, label="Poll option A", maximum=POLL_OPTION_MAX_LENGTH)
        second = validate_editor_text(option_b, label="Poll option B", maximum=POLL_OPTION_MAX_LENGTH)
        _replace_headline(root, poll_question)
        _replace_fitted_group_text(
            root,
            "poll-options",
            [first, second],
            max_width=286,
        )
        _replace_group_text(root, "cta", [definition.cta])
    else:
        _replace_headline(root, title)
        _replace_group_text(root, "cta", [definition.cta])
        if graphic_type == "event":
            _remove_placeholder(root, "event-date")
            _remove_placeholder(root, "event-location")

    svg = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    validate_composed_svg(svg)
    return svg
