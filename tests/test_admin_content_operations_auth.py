import os

import pytest
from fastapi.testclient import TestClient


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


ROUTES = (
    ("/api/sync-rss-now", server.sync_rss_now),
    ("/api/fix-mismatched-content", server.fix_mismatched_content),
    ("/api/remove-product-articles", server.remove_product_articles),
)


def _post_routes(path):
    return [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == path
        and "POST" in getattr(route, "methods", set())
    ]


def _dependency_calls(dependant):
    calls = set()
    pending = list(dependant.dependencies)
    while pending:
        dependency = pending.pop()
        calls.add(dependency.call)
        pending.extend(dependency.dependencies)
    return calls


@pytest.mark.parametrize(("path", "endpoint"), ROUTES)
def test_content_operation_has_one_authenticated_route(path, endpoint):
    routes = _post_routes(path)

    assert len(routes) == 1
    assert routes[0].endpoint is endpoint
    assert server.get_admin_auth in _dependency_calls(routes[0].dependant)


@pytest.mark.parametrize(("path", "_endpoint"), ROUTES)
def test_unauthenticated_content_operation_starts_no_business_work(
    monkeypatch,
    path,
    _endpoint,
):
    class UntouchedCollaborator:
        def __init__(self):
            self.touched = False

        def __getattr__(self, name):
            self.touched = True
            raise AssertionError(
                f"business collaborator {name} must not be used before authentication"
            )

    database = UntouchedCollaborator()
    rss_feed = UntouchedCollaborator()
    perplexity = UntouchedCollaborator()

    monkeypatch.setattr(server, "db", database)

    import app.news_feed_service
    import app.perplexity_service

    monkeypatch.setattr(app.news_feed_service, "news_feed_service", rss_feed)
    monkeypatch.setattr(app.perplexity_service, "perplexity_service", perplexity)

    response = TestClient(server.app).post(path)

    assert response.status_code == 401
    assert database.touched is False
    assert rss_feed.touched is False
    assert perplexity.touched is False
