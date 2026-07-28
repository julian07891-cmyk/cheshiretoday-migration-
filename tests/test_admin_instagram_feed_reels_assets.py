import hashlib
import io
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx
import pytest
from PIL import Image

from backend.app import instagram_social_asset as social_asset


ARTICLE = {
    "mongo_id": "507f1f77bcf86cd799439011",
    "title": "Council investment supports new jobs in Knutsford town centre",
    "category": "Local News",
    "image": "https://images.example.test/story.jpg",
}
JODRELL_TITLE = "Huge blow as Jodrell Bank funding withdrawn putting its future at risk"


def image_bytes():
    output = io.BytesIO()
    Image.new("RGB", (1200, 800), (31, 58, 138)).save(output, format="JPEG")
    return output.getvalue()


def public_resolver(host, port, type=None):
    return [(2, 1, 6, "", ("93.184.216.34", port))]


def compose(composer, article=None):
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                headers={"content-type": "image/jpeg"},
                content=image_bytes(),
            )
        )
    ) as client:
        return composer(
            article or ARTICLE,
            http_client=client,
            resolver=public_resolver,
        )


@pytest.mark.parametrize(
    "composer,format_key,width,height,required_text",
    [
        (social_asset.compose_instagram_feed_svg, social_asset.INSTAGRAM_FEED_FORMAT, 1080, 1080, "READ THE FULL STORY"),
        (social_asset.compose_instagram_reels_cover_svg, social_asset.INSTAGRAM_REELS_COVER_FORMAT, 1080, 1920, "REEL"),
    ],
)
def test_feed_and_reels_are_exact_self_contained_assets(
    composer, format_key, width, height, required_text
):
    svg = compose(composer)
    root = ET.fromstring(svg)
    assert root.attrib["width"] == str(width)
    assert root.attrib["height"] == str(height)
    assert root.attrib["viewBox"] == f"0 0 {width} {height}"
    assert b"data:image/jpeg;base64," in svg
    assert b"data:image/png;base64," in svg
    assert b"https://images.example.test" not in svg
    assert social_asset.APPROVED_LOGO_SHA256.encode() in svg
    assert not [node for node in root.iter() if node.attrib.get("data-placeholder")]
    rendered = "".join(root.itertext())
    assert ARTICLE["title"] in rendered
    assert "LOCAL NEWS" in rendered
    assert required_text in rendered
    assert not any(label in rendered for label in ("[HEADLINE]", "[CATEGORY]", "[CTA]", "[REEL]", "IMAGE", "LOGO"))
    guides = next(node for node in root.iter() if node.attrib.get("id") == "editor-guides")
    assert guides.attrib.get("display") == "none"
    master, checksum = social_asset.INSTAGRAM_GRAPHIC_MASTERS[format_key]
    assert hashlib.sha256(master.read_bytes()).hexdigest() == checksum


@pytest.mark.parametrize(
    "composer,bottom,max_lines",
    [
        (social_asset.compose_instagram_feed_svg, social_asset.FEED_HEADLINE_BOTTOM, social_asset.FEED_MAX_HEADLINE_LINES),
        (social_asset.compose_instagram_reels_cover_svg, social_asset.REELS_HEADLINE_BOTTOM, social_asset.REELS_MAX_HEADLINE_LINES),
    ],
)
def test_headlines_fit_the_approved_format_geometry(composer, bottom, max_lines):
    root = ET.fromstring(compose(composer))
    headline = next(node for node in root.iter() if node.attrib.get("data-content") == "headline")
    lines = [node for node in headline.iter() if node.tag.endswith("tspan")]
    assert 1 <= len(lines) <= max_lines
    assert max(float(line.attrib["y"]) for line in lines) <= bottom


@pytest.mark.parametrize(
    "composer,right_boundary,max_lines",
    [
        (social_asset.compose_instagram_feed_svg, social_asset.FEED_HEADLINE_RIGHT, social_asset.FEED_MAX_HEADLINE_LINES),
        (social_asset.compose_instagram_reels_cover_svg, social_asset.REELS_HEADLINE_RIGHT, social_asset.REELS_MAX_HEADLINE_LINES),
    ],
)
def test_jodrell_headline_respects_explicit_format_right_boundary(composer, right_boundary, max_lines):
    root = ET.fromstring(compose(composer, {**ARTICLE, "title": JODRELL_TITLE}))
    headline = next(node for node in root.iter() if node.attrib.get("data-content") == "headline")
    text = next(node for node in headline if node.tag.endswith("text"))
    font_size = int(text.attrib["font-size"])
    lines = [node for node in text if node.tag.endswith("tspan")]
    assert 1 <= len(lines) <= max_lines
    for line in lines:
        x = float(line.attrib["x"])
        assert x + social_asset._safe_headline_width("".join(line.itertext()).strip(), font_size) <= right_boundary


def test_reels_badge_and_cta_remain_inside_the_story_safe_area():
    root = ET.fromstring(compose(social_asset.compose_instagram_reels_cover_svg))
    for name in ("reel-badge", "cta"):
        group = next(node for node in root.iter() if node.attrib.get("data-content") == name)
        rect = next(node for node in group if node.tag.endswith("rect"))
        assert float(rect.attrib["y"]) + float(rect.attrib["height"]) <= social_asset.REELS_SAFE_BOTTOM


@pytest.mark.parametrize(
    "composer",
    [social_asset.compose_instagram_feed_svg, social_asset.compose_instagram_reels_cover_svg],
)
def test_new_formats_reject_unsafe_images_and_have_no_write_path(composer, monkeypatch):
    with pytest.raises(social_asset.ImageURLValidationError):
        compose(composer, {**ARTICLE, "image": "http://127.0.0.1/private.jpg"})
    monkeypatch.setattr(Path, "write_text", lambda *args, **kwargs: pytest.fail("write_text called"))
    monkeypatch.setattr(Path, "write_bytes", lambda *args, **kwargs: pytest.fail("write_bytes called"))
    compose(composer)
