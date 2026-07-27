"""Pure composition for the approved Facebook Newsletter social asset."""

from __future__ import annotations

import base64
import hashlib
import io
import xml.etree.ElementTree as ET

from PIL import Image

from backend.app.facebook_social_asset import (
    TemplateValidationError,
    _replace_placeholder,
    _svg_element,
    validate_composed_svg,
)
from backend.app.social_asset_constants import (
    APPROVED_LOGO_PATH,
    APPROVED_LOGO_SHA256,
    APPROVED_NEWSLETTER_MASTER_SHA256,
    NEWSLETTER_MASTER_SVG_PATH,
)

NEWSLETTER_HEADLINE = "Join thousands of Cheshire readers"
NEWSLETTER_SUPPORTING_MESSAGE = (
    "Get the latest local, business, property and AI & Tech stories."
)
NEWSLETTER_CTA = "SIGN UP FREE"
NEWSLETTER_WEBSITE = "cheshiretoday.co.uk/newsletter"
INVERSE_LOGO_COLOUR = (247, 244, 238)


def _read_approved_newsletter_assets() -> tuple[bytes, bytes]:
    try:
        master = NEWSLETTER_MASTER_SVG_PATH.read_bytes()
        logo = APPROVED_LOGO_PATH.read_bytes()
    except OSError as exc:
        raise TemplateValidationError("Approved Newsletter asset files are unavailable") from exc
    if hashlib.sha256(master).hexdigest() != APPROVED_NEWSLETTER_MASTER_SHA256:
        raise TemplateValidationError("Approved Newsletter template checksum is invalid")
    if hashlib.sha256(logo).hexdigest() != APPROVED_LOGO_SHA256:
        raise TemplateValidationError("Approved Cheshire Today logo checksum is invalid")
    return master, logo


def _build_inverse_logo(logo: bytes) -> bytes:
    try:
        with Image.open(io.BytesIO(logo)) as source:
            image = source.convert("RGBA")
    except OSError as exc:
        raise TemplateValidationError("Approved Cheshire Today logo is invalid") from exc
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, alpha = pixels[x, y]
            if alpha:
                pixels[x, y] = (*INVERSE_LOGO_COLOUR, alpha)
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _text(x: int, y: int, value: str, **attributes: object) -> ET.Element:
    element = _svg_element("text", {"x": x, "y": y, **attributes})
    element.text = value
    return element


def _compose(root: ET.Element, inverse_logo: bytes) -> None:
    logo_group = _svg_element(
        "g",
        {"data-content": "logo", "data-logo-variant": "inverse"},
    )
    logo_group.append(
        _svg_element(
            "image",
            {
                "x": 72,
                "y": 72,
                "width": 159.34,
                "height": 54,
                "preserveAspectRatio": "xMidYMid meet",
                "href": f"data:image/png;base64,{base64.b64encode(inverse_logo).decode('ascii')}",
                "data-source-sha256": APPROVED_LOGO_SHA256,
            },
        )
    )
    _replace_placeholder(root, "logo", logo_group)

    category_group = _svg_element("g", {"data-content": "category", "class": "interface"})
    category_group.append(
        _svg_element(
            "rect",
            {"x": 868, "y": 74, "width": 260, "height": 50, "rx": 25, "fill": "#059669"},
        )
    )
    category_group.append(
        _text(
            998,
            106,
            "NEWSLETTER",
            fill="#F7F4EE",
            **{"text-anchor": "middle", "font-size": 18, "font-weight": 700, "letter-spacing": 2},
        )
    )
    _replace_placeholder(root, "category", category_group)

    supporting_group = _svg_element("g", {"data-content": "supporting", "class": "interface"})
    supporting_group.append(
        _svg_element(
            "rect",
            {"x": 72, "y": 168, "width": 430, "height": 326, "rx": 18, "fill": "#FBFAF7"},
        )
    )
    supporting_group.append(
        _text(108, 246, "Get the latest local, business,", fill="#1E293B", **{"font-size": 25, "font-weight": 700})
    )
    supporting_group.append(
        _text(108, 286, "property and AI & Tech stories.", fill="#1E293B", **{"font-size": 25, "font-weight": 700})
    )
    supporting_group.append(
        _text(108, 428, NEWSLETTER_WEBSITE, fill="#1E3A8A", **{"font-size": 22, "font-weight": 700})
    )
    _replace_placeholder(root, "image", supporting_group)

    headline_group = _svg_element("g", {"data-content": "headline", "class": "headline", "fill": "#F7F4EE"})
    headline_group.append(
        _text(560, 224, "Join thousands of", **{"font-size": 60, "font-weight": 700})
    )
    headline_group.append(
        _text(560, 298, "Cheshire readers", **{"font-size": 60, "font-weight": 700})
    )
    _replace_placeholder(root, "headline", headline_group)

    cta_group = _svg_element("g", {"data-content": "cta", "class": "interface"})
    cta_group.append(
        _svg_element(
            "rect",
            {"x": 560, "y": 474, "width": 360, "height": 72, "rx": 10, "fill": "#F7F4EE"},
        )
    )
    cta_group.append(
        _text(
            740,
            520,
            NEWSLETTER_CTA,
            fill="#1E3A8A",
            **{"text-anchor": "middle", "font-size": 23, "font-weight": 700},
        )
    )
    _replace_placeholder(root, "cta", cta_group)


def compose_facebook_newsletter_svg() -> bytes:
    """Return the deterministic self-contained Newsletter SVG in memory."""
    master, logo = _read_approved_newsletter_assets()
    try:
        root = ET.fromstring(master)
    except ET.ParseError as exc:
        raise TemplateValidationError("Approved Newsletter template is invalid") from exc
    _compose(root, _build_inverse_logo(logo))
    svg = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    validate_composed_svg(svg)
    return svg
