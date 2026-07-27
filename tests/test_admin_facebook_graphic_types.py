import xml.etree.ElementTree as ET
import re
from pathlib import Path

import pytest

from backend.app import facebook_graphic_types as graphics
from backend.app.facebook_social_asset import ArticleValidationError, ValidatedImage


ARTICLE = {
    "mongo_id": "507f1f77bcf86cd799439011",
    "title": "Cheshire investment creates new skilled jobs",
    "category": "Business",
    "image": "https://images.example.test/story.jpg",
}
IMAGE = ValidatedImage(b"image-bytes", "image/png", 1200, 630)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(graphics, "fetch_validated_article_image", lambda *args, **kwargs: IMAGE)


@pytest.mark.parametrize(
    ("graphic_type", "category", "expected"),
    [
        ("business", "Business", "BUSINESS"),
        ("business", "Finance", "BUSINESS"),
        ("property", "Property", "PROPERTY"),
        ("ai-tech", "AI & Tech", "AI & TECH"),
        ("breaking-news", "Local News", "BREAKING"),
        ("event", "Entertainment", "EVENT"),
    ],
)
def test_article_graphic_types_use_approved_self_contained_masters(graphic_type, category, expected):
    svg = graphics.compose_facebook_graphic_svg({**ARTICLE, "category": category}, graphic_type)
    root = ET.fromstring(svg)
    assert root.attrib["width"] == "1200"
    assert root.attrib["height"] == "630"
    assert root.attrib["viewBox"] == "0 0 1200 630"
    assert expected in "".join(root.itertext())
    assert b"data:image/png;base64," in svg
    assert b"data-placeholder" not in svg
    assert b"http://images.example" not in svg
    assert b"[DATE]" not in svg and b"[LOCATION]" not in svg


@pytest.mark.parametrize(
    ("graphic_type", "category"),
    [
        ("business", "Local News"), ("property", "Business"),
        ("property", "Planning"), ("property", "Housing"),
        ("ai-tech", "Technology"), ("event", "Local News"), ("event", "Events"),
    ],
)
def test_category_eligibility_is_explicit(graphic_type, category):
    with pytest.raises(ArticleValidationError):
        graphics.compose_facebook_graphic_svg({**ARTICLE, "category": category}, graphic_type)


def test_quote_is_verified_editor_text_and_xml_escaped():
    svg = graphics.compose_facebook_graphic_svg(
        ARTICLE,
        "quote",
        quote='Growth & jobs are "essential"',
        attribution="Jane O'Brien & Co",
    )
    root = ET.fromstring(svg)
    rendered = "".join(root.itertext())
    assert 'Growth & jobs are "essential"' in rendered
    assert "Jane O'Brien & Co" in rendered
    assert b"&amp;" in svg


@pytest.mark.parametrize(
    ("quote", "attribution"),
    [("x" * 241, "Source"), ("Verified", "x" * 81), ("https://unsafe.test", "Source"), ("<b>claim</b>", "Source")],
)
def test_quote_rejects_long_html_and_url_input(quote, attribution):
    with pytest.raises(ArticleValidationError):
        graphics.compose_facebook_graphic_svg(ARTICLE, "quote", quote=quote, attribution=attribution)


def test_poll_has_exactly_two_escaped_options_and_no_interactive_claim():
    svg = graphics.compose_facebook_graphic_svg(
        ARTICLE,
        "poll",
        question="Should Cheshire invest more?",
        option_a="Yes & now",
        option_b="Not yet",
    )
    rendered = "".join(ET.fromstring(svg).itertext())
    assert "Should Cheshire invest more?" in rendered
    assert "Yes & now" in rendered
    assert "Not yet" in rendered
    assert "REPLY IN COMMENTS" in rendered
    assert "interactive" not in rendered.lower()


@pytest.mark.parametrize("field", ["question", "option_a", "option_b"])
def test_poll_rejects_invalid_editor_fields(field):
    values = {"question": "Your view?", "option_a": "Yes", "option_b": "No"}
    values[field] = "https://unsafe.test"
    with pytest.raises(ArticleValidationError):
        graphics.compose_facebook_graphic_svg(ARTICLE, "poll", **values)


def test_approved_masters_remain_immutable_and_module_has_no_write_path():
    for path, checksum in graphics.FACEBOOK_GRAPHIC_MASTERS.values():
        import hashlib
        assert hashlib.sha256(path.read_bytes()).hexdigest() == checksum
    source = Path(graphics.__file__).read_text()
    for forbidden in ("write_bytes(", "write_text(", "insert_one(", "update_one(", "delete_one("):
        assert forbidden not in source


def _fitted_text_geometry(svg, content_name):
    root = ET.fromstring(svg)
    groups = [item for item in root.iter() if item.attrib.get("data-content") == content_name]
    assert len(groups) == 1
    results = []
    for text in (item for item in groups[0].iter() if item.tag.endswith("text")):
        tspans = [item for item in text if item.tag.endswith("tspan")]
        if not tspans:
            continue
        font_size = int(text.attrib["font-size"])
        width = int(text.attrib["data-fit-width"])
        lines = [(item.text or "", float(item.attrib["x"]), float(item.attrib["y"])) for item in tspans]
        results.append((font_size, width, lines))
    return results


@pytest.mark.parametrize(
    "attribution",
    ["i" * graphics.ATTRIBUTION_MAX_LENGTH, "W" * 40, 'A & B "verified"'],
)
def test_quote_attribution_fits_approved_box(attribution):
    svg = graphics.compose_facebook_graphic_svg(
        ARTICLE, "quote", quote="Verified & exact", attribution=attribution
    )
    fitted = _fitted_text_geometry(svg, "cta")
    assert len(fitted) == 1
    font_size, width, lines = fitted[0]
    assert len(lines) <= 2
    assert width == 276
    assert all(graphics._estimated_text_width(line, font_size) <= width for line, _x, _y in lines)
    assert all(486 <= y - font_size and y + font_size * 0.25 <= 550 for _line, _x, y in lines)


def test_quote_one_character_beyond_limit_is_rejected():
    with pytest.raises(ArticleValidationError):
        graphics.compose_facebook_graphic_svg(
            ARTICLE,
            "quote",
            quote="Verified",
            attribution="i" * (graphics.ATTRIBUTION_MAX_LENGTH + 1),
        )


@pytest.mark.parametrize("option", ["i" * graphics.POLL_OPTION_MAX_LENGTH, "W" * graphics.POLL_OPTION_MAX_LENGTH, "Yes & now"])
def test_poll_options_fit_separate_approved_boxes(option):
    svg = graphics.compose_facebook_graphic_svg(
        ARTICLE, "poll", question="Your view?", option_a=option, option_b=option
    )
    fitted = _fitted_text_geometry(svg, "poll-options")
    assert len(fitted) == 2
    boxes = [(462, 772), (796, 1106)]
    for (font_size, width, lines), (left, right) in zip(fitted, boxes):
        assert len(lines) <= 2
        assert width == 286
        for line, x, y in lines:
            measured = graphics._estimated_text_width(line, font_size)
            assert measured <= width
            assert left <= x - measured / 2
            assert x + measured / 2 <= right
            assert 360 <= y - font_size and y + font_size * 0.25 <= 430
    assert boxes[0][1] < boxes[1][0]


def test_poll_one_character_beyond_option_limit_is_rejected():
    with pytest.raises(ArticleValidationError):
        graphics.compose_facebook_graphic_svg(
            ARTICLE,
            "poll",
            question="Your view?",
            option_a="i" * (graphics.POLL_OPTION_MAX_LENGTH + 1),
            option_b="No",
        )


@pytest.mark.parametrize(
    "unsafe",
    [
        "http://example.test", "https://example.test", "www.example.test",
        "mailto:editor@example.test", "ftp://example.test", "file:///tmp/x",
        "data:text/plain,test", "javascript:alert(1)", "<strong>text</strong>",
        "<script alert(1)",
    ],
)
def test_editor_text_rejects_urls_html_and_tag_like_fragments(unsafe):
    with pytest.raises(ArticleValidationError):
        graphics.validate_editor_text(unsafe, label="Editor text", maximum=240)


def test_backend_registries_are_genuinely_immutable():
    with pytest.raises(TypeError):
        graphics.GRAPHIC_TYPES["business"] = graphics.GRAPHIC_TYPES["business"]
    with pytest.raises(TypeError):
        graphics.FACEBOOK_GRAPHIC_MASTERS["business"] = graphics.FACEBOOK_GRAPHIC_MASTERS["business"]


def test_frontend_transport_routes_and_backend_composer_inventory_remain_in_parity():
    root = Path(__file__).resolve().parents[1]
    dialog = (root / "frontend/src/components/admin/FacebookLocalGraphicDialog.jsx").read_text()
    transport = (root / "frontend/src/services/facebookSocialAsset.js").read_text()
    options_block = dialog.split("const GRAPHIC_TYPES", 1)[1].split("]);", 1)[0]
    frontend_options = set(re.findall(r"value: '([^']+)'", options_block))
    article_block = transport.split("const articleTypes", 1)[1].split(");", 1)[0]
    editor_block = transport.split("const editorTypes", 1)[1].split(");", 1)[0]
    frontend_transport = {
        "local-news", "newsletter", *re.findall(r"'([^']+)'", article_block),
        *re.findall(r"'([^']+)'", editor_block),
    }
    backend_inventory = {"local-news", "newsletter", *graphics.GRAPHIC_TYPES.keys()}
    assert frontend_options == frontend_transport == backend_inventory
    assert graphics.ARTICLE_GRAPHIC_TYPES == {
        "business", "property", "ai-tech", "breaking-news", "event"
    }
