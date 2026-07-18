import inspect
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


UNAVAILABLE_DETAIL = "Secure newsletter management is not yet available."
TOKEN = "offline-test-token"
VALID_EMAIL = "reader@example.com"

SECURE_ROUTES = (
    (
        "POST",
        "/api/newsletter/preferences/verify",
        server.verify_secure_newsletter_preferences,
        {"token": TOKEN},
        "NewsletterTokenRequest",
        "NewsletterSecurePreferencesResponse",
    ),
    (
        "PUT",
        "/api/newsletter/preferences/secure",
        server.update_secure_newsletter_preferences,
        {
            "token": TOKEN,
            "daily_brief": True,
            "weekly_roundup": False,
            "breaking_news": False,
        },
        "SecureNewsletterPreferencesUpdateRequest",
        "NewsletterGenericResponse",
    ),
    (
        "POST",
        "/api/newsletter/preferences/request-link",
        server.request_secure_newsletter_preferences_link,
        {"email": VALID_EMAIL},
        "NewsletterSecureLinkRequest",
        "NewsletterGenericResponse",
    ),
    (
        "POST",
        "/api/newsletter/unsubscribe/confirm",
        server.confirm_secure_newsletter_unsubscribe,
        {"token": TOKEN},
        "NewsletterTokenRequest",
        "NewsletterGenericResponse",
    ),
    (
        "POST",
        "/api/newsletter/unsubscribe/one-click",
        server.one_click_secure_newsletter_unsubscribe,
        None,
        None,
        "NewsletterGenericResponse",
    ),
    (
        "POST",
        "/api/newsletter/unsubscribe/request-link",
        server.request_secure_newsletter_unsubscribe_link,
        {"email": VALID_EMAIL},
        "NewsletterSecureLinkRequest",
        "NewsletterGenericResponse",
    ),
    (
        "POST",
        "/api/newsletter/reactivate/request-link",
        server.request_secure_newsletter_reactivation_link,
        {"email": VALID_EMAIL},
        "NewsletterSecureLinkRequest",
        "NewsletterGenericResponse",
    ),
    (
        "POST",
        "/api/newsletter/reactivate/confirm",
        server.confirm_secure_newsletter_reactivation,
        {
            "token": TOKEN,
            "daily_brief": True,
            "weekly_roundup": False,
            "breaking_news": False,
        },
        "NewsletterReactivationConfirmRequest",
        "NewsletterGenericResponse",
    ),
)

LEGACY_ROUTES = (
    ("POST", "/api/subscribe", server.subscribe_newsletter),
    ("POST", "/api/newsletter/subscribe", server.subscribe_newsletter),
    ("GET", "/api/newsletter/preferences/{email}", server.get_newsletter_preferences),
    ("PUT", "/api/newsletter/preferences", server.update_newsletter_preferences),
    ("POST", "/api/newsletter/email-preferences", None),
    ("PUT", "/api/newsletter/email-preferences", None),
    ("GET", "/api/newsletter/email-preferences/{email}", server.get_email_preferences),
    ("POST", "/api/newsletter/unsubscribe", server.unsubscribe_newsletter),
)


def _routes(method, path):
    return [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == path
        and method in getattr(route, "methods", set())
    ]


def _model_schema(model):
    return model.model_json_schema()


@pytest.mark.parametrize(
    ("method", "path", "endpoint", "_payload", "_request_model", "_response_model"),
    SECURE_ROUTES,
)
def test_each_secure_contract_is_registered_once(
    method,
    path,
    endpoint,
    _payload,
    _request_model,
    _response_model,
):
    routes = _routes(method, path)

    assert len(routes) == 1
    assert routes[0].endpoint is endpoint


def test_secure_endpoint_names_and_openapi_operation_ids_are_unique():
    endpoint_names = [endpoint.__name__ for _, _, endpoint, *_ in SECURE_ROUTES]
    assert len(endpoint_names) == len(set(endpoint_names))

    operation_ids = [
        operation["operationId"]
        for path_item in server.app.openapi()["paths"].values()
        for operation in path_item.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]
    assert len(operation_ids) == len(set(operation_ids))


@pytest.mark.parametrize(("method", "path", "endpoint"), LEGACY_ROUTES)
def test_existing_newsletter_routes_remain_registered(method, path, endpoint):
    routes = _routes(method, path)

    assert len(routes) == 1
    if endpoint is not None:
        assert routes[0].endpoint is endpoint


def test_existing_newsletter_request_and_response_contracts_are_preserved():
    openapi = server.app.openapi()

    subscribe = openapi["paths"]["/api/subscribe"]["post"]
    assert subscribe["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/SubscribeRequest"
    )
    assert subscribe["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/SubscribeResponse")

    preferences = openapi["paths"]["/api/newsletter/preferences"]["put"]
    assert preferences["requestBody"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/UpdatePreferencesRequest")

    unsubscribe = openapi["paths"]["/api/newsletter/unsubscribe"]["post"]
    assert unsubscribe["requestBody"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/UnsubscribeRequest")


@pytest.mark.parametrize("model", (server.NewsletterTokenRequest,))
def test_token_is_required(model):
    with pytest.raises(ValidationError):
        model()


@pytest.mark.parametrize("token", ("", " ", "\t\n", "x" * 4097))
def test_invalid_tokens_are_rejected(token):
    with pytest.raises(ValidationError):
        server.NewsletterTokenRequest(token=token)


def test_valid_token_is_trimmed_and_accepted():
    request = server.NewsletterTokenRequest(token=f"  {TOKEN}  ")
    assert request.token == TOKEN


def test_maximum_length_token_is_accepted():
    request = server.NewsletterTokenRequest(token="x" * 4096)
    assert len(request.token) == 4096


@pytest.mark.parametrize("email", ("invalid", "reader@", "@example.com", ""))
def test_invalid_secure_link_email_is_rejected(email):
    with pytest.raises(ValidationError):
        server.NewsletterSecureLinkRequest(email=email)


def test_valid_secure_link_email_is_accepted():
    request = server.NewsletterSecureLinkRequest(email=VALID_EMAIL)
    assert str(request.email) == VALID_EMAIL


@pytest.mark.parametrize(
    "model",
    (
        server.SecureNewsletterPreferencesUpdateRequest,
        server.NewsletterReactivationConfirmRequest,
    ),
)
@pytest.mark.parametrize("missing", ("daily_brief", "weekly_roundup", "breaking_news"))
def test_all_secure_preference_booleans_are_required(model, missing):
    payload = {
        "token": TOKEN,
        "daily_brief": True,
        "weekly_roundup": False,
        "breaking_news": False,
    }
    del payload[missing]

    with pytest.raises(ValidationError):
        model(**payload)


@pytest.mark.parametrize(
    "model",
    (
        server.SecureNewsletterPreferencesUpdateRequest,
        server.NewsletterReactivationConfirmRequest,
    ),
)
@pytest.mark.parametrize("invalid", ("true", "false", 0, 1, None))
def test_secure_preference_values_are_strict_booleans(model, invalid):
    with pytest.raises(ValidationError):
        model(
            token=TOKEN,
            daily_brief=invalid,
            weekly_roundup=False,
            breaking_news=False,
        )


def test_reactivation_confirmation_requires_token():
    with pytest.raises(ValidationError):
        server.NewsletterReactivationConfirmRequest(
            daily_brief=True,
            weekly_roundup=False,
            breaking_news=False,
        )


class FailOnAccess:
    def __init__(self, label):
        self.label = label
        self.touched = False

    def __getattr__(self, name):
        self.touched = True
        raise AssertionError(f"{self.label} must remain unused")


@pytest.mark.parametrize(
    ("method", "path", "_endpoint", "payload", "_request_model", "_response_model"),
    SECURE_ROUTES,
)
def test_dormant_routes_return_only_generic_503_without_business_access(
    monkeypatch,
    method,
    path,
    _endpoint,
    payload,
    _request_model,
    _response_model,
):
    database = FailOnAccess("database")
    email_service = FailOnAccess("email service")
    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "email_service", email_service)

    client = TestClient(server.app)
    if path.endswith("/one-click"):
        response = client.request(
            method,
            path,
            content="List-Unsubscribe=One-Click",
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
    else:
        response = client.request(method, path, json=payload)

    assert response.status_code == 503
    assert response.json() == {"detail": UNAVAILABLE_DETAIL}
    assert database.touched is False
    assert email_service.touched is False

    rendered = response.text.lower()
    for prohibited in (
        VALID_EMAIL,
        TOKEN,
        "daily_brief",
        "weekly_roundup",
        "breaking_news",
        "subscriber",
        "active",
        "timestamp",
        "management_id",
        "token_version",
        "configuration",
    ):
        assert prohibited.lower() not in rendered


@pytest.mark.parametrize(
    ("method", "path", "_endpoint", "_payload", "request_model", "response_model"),
    SECURE_ROUTES,
)
def test_openapi_documents_secure_contracts_and_503(
    method,
    path,
    _endpoint,
    _payload,
    request_model,
    response_model,
):
    operation = server.app.openapi()["paths"][path][method.lower()]

    if request_model is None:
        assert "requestBody" not in operation
    else:
        schema = operation["requestBody"]["content"]["application/json"]["schema"]
        assert schema["$ref"].endswith(f"/{request_model}")

    success_schema = operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]
    assert success_schema["$ref"].endswith(f"/{response_model}")
    assert "503" in operation["responses"]
    assert operation["responses"]["503"]["description"] == UNAVAILABLE_DETAIL
    assert "security" not in operation
    assert "{" not in path


def test_secure_models_expose_only_frozen_fields():
    assert set(_model_schema(server.NewsletterTokenRequest)["properties"]) == {"token"}
    assert set(
        _model_schema(server.SecureNewsletterPreferencesUpdateRequest)["properties"]
    ) == {"token", "daily_brief", "weekly_roundup", "breaking_news"}
    assert set(_model_schema(server.NewsletterSecureLinkRequest)["properties"]) == {
        "email"
    }
    assert set(
        _model_schema(server.NewsletterReactivationConfirmRequest)["properties"]
    ) == {"token", "daily_brief", "weekly_roundup", "breaking_news"}
    assert set(_model_schema(server.NewsletterGenericResponse)["properties"]) == {
        "success",
        "message",
    }
    assert set(_model_schema(server.NewsletterSecurePreferences)["properties"]) == {
        "daily_brief",
        "weekly_roundup",
        "breaking_news",
    }
    assert set(
        _model_schema(server.NewsletterSecurePreferencesResponse)["properties"]
    ) == {"success", "preferences"}


def test_token_and_migration_modules_remain_unused_by_application_startup():
    source = Path(server.__file__).read_text()

    assert "newsletter_token_service" not in source
    assert "migrate_newsletter_management_ids" not in source
    assert "NEWSLETTER_LINK_SECRET" not in source


def test_scheduler_registration_source_is_unchanged_by_secure_skeletons():
    source = inspect.getsource(server)

    assert "id='morning_article_generation'" in source
    assert "id='midday_article_generation'" in source
    assert "id='evening_article_generation'" in source
    assert "id='daily_brief'" in source
    assert "id=f'weekly_roundup_batch_{roundup_batch_slot}'" in source
