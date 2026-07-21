from backend.app.article_image_resolver import resolve_imported_article_image


NEWSQUEST_IMAGE = (
    "https://www.chesterstandard.co.uk/resources/images/21201208/"
)
NEWSQUEST_SOURCE = (
    "https://www.chesterstandard.co.uk/news/"
    "26290039.chester-suda-sauna-authentic-sauna-experience/"
)
NEWSQUEST_OG_IMAGE = (
    "https://www.chesterstandard.co.uk/"
    "resources/images/21201208.jpg?type=og-image"
)


def test_newsquest_rss_image_uses_source_open_graph_image():
    calls = []

    def fetch_page(url):
        calls.append(url)
        return (
            '<html><head>'
            f'<meta property="og:image" content="{NEWSQUEST_OG_IMAGE}">'
            '</head></html>'
        )

    resolved = resolve_imported_article_image(
        NEWSQUEST_IMAGE,
        NEWSQUEST_SOURCE,
        fetch_page=fetch_page,
    )

    assert resolved == NEWSQUEST_OG_IMAGE
    assert calls == [NEWSQUEST_SOURCE]


def test_non_newsquest_image_is_preserved_without_source_lookup():
    calls = []

    def fetch_page(url):
        calls.append(url)
        raise AssertionError("non-Newsquest image must not fetch source page")

    image = "https://ichef.bbci.co.uk/news/1024/example.jpg"

    resolved = resolve_imported_article_image(
        image,
        "https://www.bbc.co.uk/news/articles/example",
        fetch_page=fetch_page,
    )

    assert resolved == image
    assert calls == []


def test_newsquest_lookup_failure_preserves_original_image():
    def fetch_page(url):
        raise TimeoutError("source unavailable")

    resolved = resolve_imported_article_image(
        NEWSQUEST_IMAGE,
        NEWSQUEST_SOURCE,
        fetch_page=fetch_page,
    )

    assert resolved == NEWSQUEST_IMAGE


def test_newsquest_invalid_open_graph_image_preserves_original_image():
    def fetch_page(url):
        return '<meta property="og:image" content="javascript:alert(1)">'

    resolved = resolve_imported_article_image(
        NEWSQUEST_IMAGE,
        NEWSQUEST_SOURCE,
        fetch_page=fetch_page,
    )

    assert resolved == NEWSQUEST_IMAGE
