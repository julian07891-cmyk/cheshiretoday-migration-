import hashlib
import io
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx
import pytest
from PIL import Image

from backend.app import facebook_social_asset as social_asset


MASTER = Path("docs/brand-assets/social/facebook/templates/local-news-facebook.svg")
MASTER_SHA256 = "c18d61bef5844703235643d1007454920f8cdf17a2d96ed3814cefebcc196994"
ARTICLE = {
    "mongo_id": "507f1f77bcf86cd799439011",
    "title": "New investment brings jobs to Knutsford town centre",
    "category": "Local News",
    "image": "https://images.example.test/story.jpg",
}


def image_bytes(fmt="JPEG", size=(1200, 800)):
    output = io.BytesIO()
    Image.new("RGB", size, (31, 58, 138)).save(output, format=fmt)
    return output.getvalue()


def public_resolver(host, port, type=None):
    return [(2, 1, 6, "", ("93.184.216.34", port))]


def client_for(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def compose(handler=None, article=None, **kwargs):
    body = image_bytes()
    handler = handler or (lambda request: httpx.Response(200, headers={"content-type": "image/jpeg"}, content=body))
    with client_for(handler) as client:
        return social_asset.compose_facebook_local_news_svg(
            article or ARTICLE,
            http_client=client,
            resolver=public_resolver,
            **kwargs,
        )


def test_valid_article_composition_is_self_contained_and_exact_size():
    svg = compose()
    root = ET.fromstring(svg)
    assert root.attrib["width"] == "1200"
    assert root.attrib["height"] == "630"
    assert root.attrib["viewBox"] == "0 0 1200 630"
    assert b"data:image/jpeg;base64," in svg
    assert b"data:image/png;base64," in svg
    assert b"https://images.example.test" not in svg
    assert b"[HEADLINE]" not in svg
    assert b"[CATEGORY]" not in svg
    assert b"[CTA]" not in svg
    assert b"[STANDARD LOGO]" not in svg
    assert social_asset.APPROVED_LOGO_SHA256.encode() in svg
    assert not [node for node in root.iter() if node.attrib.get("data-placeholder")]
    guides = next(node for node in root.iter() if node.attrib.get("id") == "editor-guides")
    assert guides.attrib.get("display") == "none"


@pytest.mark.parametrize("mongo_id", ["", "not-an-id", "507f1f77bcf86cd79943901z"])
def test_malformed_mongo_id_is_rejected(mongo_id):
    with pytest.raises(social_asset.ArticleValidationError):
        compose(article={**ARTICLE, "mongo_id": mongo_id})


@pytest.mark.parametrize(
    "updates",
    [
        {"title": ""},
        {"category": "Business"},
        {"image": ""},
        {"image": "file:///tmp/story.jpg"},
        {"image": "data:image/png;base64,AAAA"},
        {"image": "ftp://example.test/story.jpg"},
        {"image": "https://localhost/story.jpg"},
        {"image": "https://bad host/story.jpg"},
    ],
)
def test_invalid_article_fields_are_rejected_before_fetch(updates):
    with pytest.raises((social_asset.ArticleValidationError, social_asset.ImageURLValidationError)):
        compose(article={**ARTICLE, **updates})


@pytest.mark.parametrize("address", ["127.0.0.1", "10.1.2.3", "169.254.10.2", "::1", "fc00::1"])
def test_internal_network_destinations_are_rejected(address):
    def resolver(host, port, type=None):
        family = 10 if ":" in address else 2
        return [(family, 1, 6, "", (address, port))]

    with client_for(lambda request: pytest.fail("network request must not occur")) as client:
        with pytest.raises(social_asset.ImageURLValidationError):
            social_asset.fetch_validated_article_image(ARTICLE["image"], http_client=client, resolver=resolver)


def test_redirect_destination_is_revalidated_and_private_redirect_is_rejected():
    def handler(request):
        return httpx.Response(302, headers={"location": "http://127.0.0.1/private.jpg"})

    with client_for(handler) as client:
        with pytest.raises(social_asset.ImageURLValidationError):
            social_asset.fetch_validated_article_image(ARTICLE["image"], http_client=client, resolver=public_resolver)


def test_unsupported_mime_type_is_rejected():
    with pytest.raises(social_asset.ImageContentError):
        compose(lambda request: httpx.Response(200, headers={"content-type": "text/html"}, content=b"not an image"))


def test_oversized_response_is_rejected():
    with pytest.raises(social_asset.ImageContentError):
        compose(
            lambda request: httpx.Response(
                200,
                headers={"content-type": "image/jpeg", "content-length": str(social_asset.MAX_IMAGE_BYTES + 1)},
                content=b"x",
            )
        )


@pytest.mark.parametrize("size", [(99, 99), (13000, 200), (7000, 7000)])
def test_invalid_image_dimensions_are_rejected(size):
    body = image_bytes(size=size)
    with pytest.raises(social_asset.ImageContentError):
        compose(lambda request: httpx.Response(200, headers={"content-type": "image/jpeg"}, content=body))


def test_xml_escaping_and_long_headline_wrapping():
    article = {
        **ARTICLE,
        "title": "Council & residents approve <major> town-centre investment with a deliberately long explanatory headline",
    }
    svg = compose(article=article, cta="Read & discover")
    root = ET.fromstring(svg)
    text = "".join(root.itertext())
    assert article["title"] in text
    assert "Read & discover" in text
    headline_group = next(node for node in root.iter() if node.attrib.get("data-content") == "headline")
    tspans = [node for node in headline_group.iter() if node.tag.endswith("tspan")]
    assert 2 <= len(tspans) <= social_asset.MAX_HEADLINE_LINES
    assert all(float(node.attrib["x"]) == 680 for node in tspans)


def test_master_is_immutable_and_composer_has_no_write_or_database_path(monkeypatch):
    before = hashlib.sha256(MASTER.read_bytes()).hexdigest()
    monkeypatch.setattr(Path, "write_text", lambda *args, **kwargs: pytest.fail("write_text called"))
    monkeypatch.setattr(Path, "write_bytes", lambda *args, **kwargs: pytest.fail("write_bytes called"))
    compose()
    after = hashlib.sha256(MASTER.read_bytes()).hexdigest()
    assert before == after == MASTER_SHA256
    source = Path(social_asset.__file__).read_text(encoding="utf-8")
    assert "db." not in source
    assert "insert_one" not in source
    assert "update_one" not in source
    assert "delete_one" not in source
