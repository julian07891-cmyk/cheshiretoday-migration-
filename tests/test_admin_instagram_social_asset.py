import hashlib
import io
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx
import pytest
from PIL import Image

from backend.app import instagram_social_asset as social_asset


MASTER = Path("docs/brand-assets/social/stories/templates/top-story.svg")
ARTICLE = {
    "mongo_id": "507f1f77bcf86cd799439011",
    "title": "Council investment supports new jobs in Knutsford town centre",
    "category": "Local News",
    "image": "https://images.example.test/story.jpg",
}


def image_bytes():
    output = io.BytesIO()
    Image.new("RGB", (1200, 800), (31, 58, 138)).save(output, format="JPEG")
    return output.getvalue()


def public_resolver(host, port, type=None):
    return [(2, 1, 6, "", ("93.184.216.34", port))]


def compose(article=None, handler=None):
    body = image_bytes()
    handler = handler or (
        lambda request: httpx.Response(
            200, headers={"content-type": "image/jpeg"}, content=body
        )
    )
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        return social_asset.compose_instagram_top_story_svg(
            article or ARTICLE,
            http_client=client,
            resolver=public_resolver,
        )


def test_top_story_composition_is_self_contained_and_exact():
    svg = compose()
    root = ET.fromstring(svg)
    assert root.attrib == {
        **root.attrib,
        "width": "1080",
        "height": "1920",
        "viewBox": "0 0 1080 1920",
    }
    assert b"data:image/jpeg;base64," in svg
    assert b"data:image/png;base64," in svg
    assert b"https://images.example.test" not in svg
    assert social_asset.APPROVED_LOGO_SHA256.encode() in svg
    assert not [node for node in root.iter() if node.attrib.get("data-placeholder")]
    rendered = "".join(root.itertext())
    assert ARTICLE["title"] in rendered
    assert "LOCAL NEWS" in rendered
    assert "READ THE FULL STORY" in rendered
    assert "[HEADLINE]" not in rendered
    assert "[CATEGORY]" not in rendered
    assert "[CTA]" not in rendered
    assert "IMAGE" not in rendered
    assert "LOGO" not in rendered
    guides = next(node for node in root.iter() if node.attrib.get("id") == "editor-guides")
    assert guides.attrib.get("display") == "none"


def test_headline_is_fitted_inside_story_geometry_and_xml_escaped():
    article = {
        **ARTICLE,
        "title": "Council & residents approve <major> investment bringing new jobs and improved public services across Knutsford",
    }
    root = ET.fromstring(compose(article=article))
    headline = next(node for node in root.iter() if node.attrib.get("data-content") == "headline")
    lines = [node for node in headline.iter() if node.tag.endswith("tspan")]
    assert 2 <= len(lines) <= social_asset.MAX_STORY_HEADLINE_LINES
    assert all(float(node.attrib["x"]) == 72 for node in lines)
    assert article["title"] == "".join("".join(node.itertext()) for node in lines)
    assert max(float(node.attrib["y"]) for node in lines) <= 1450


@pytest.mark.parametrize(
    "image_url",
    ["file:///tmp/story.jpg", "http://127.0.0.1/story.jpg", "https://localhost/story.jpg"],
)
def test_unsafe_images_are_rejected(image_url):
    with pytest.raises(
        (social_asset.ImageURLValidationError, social_asset.ArticleValidationError)
    ):
        compose(article={**ARTICLE, "image": image_url})


def test_private_redirect_is_rejected():
    def handler(request):
        return httpx.Response(302, headers={"location": "http://127.0.0.1/private.jpg"})

    with pytest.raises(social_asset.ImageURLValidationError):
        compose(handler=handler)


def test_master_checksum_failure_is_detected(monkeypatch):
    monkeypatch.setattr(social_asset, "APPROVED_INSTAGRAM_TOP_STORY_SHA256", "0" * 64)
    with pytest.raises(social_asset.TemplateValidationError):
        compose()


def test_master_is_immutable_and_composer_has_no_write_or_database_path(monkeypatch):
    before = hashlib.sha256(MASTER.read_bytes()).hexdigest()
    monkeypatch.setattr(Path, "write_text", lambda *args, **kwargs: pytest.fail("write_text called"))
    monkeypatch.setattr(Path, "write_bytes", lambda *args, **kwargs: pytest.fail("write_bytes called"))
    compose()
    assert hashlib.sha256(MASTER.read_bytes()).hexdigest() == before
    source = Path(social_asset.__file__).read_text(encoding="utf-8")
    for forbidden in ("db.", "insert_one", "update_one", "delete_one", "write_bytes", "write_text"):
        assert forbidden not in source
