"""RED contracts for bounded, publication-neutral source-reference evidence."""

import asyncio
import copy
import inspect
import socket
from types import SimpleNamespace

import httpx
import pytest

from backend.app import perplexity_service as module


STORY = {
    "title": "Council approves library refurbishment",
    "summary": "The council approved the refurbishment on Tuesday.",
    "source": "Fixture council",
    "source_url": "https://source.invalid/library?edition=cheshire&utm_source=rss",
}
CONTENT = "The council approved the library refurbishment on Tuesday."


def response(content=CONTENT, *, status=200, citations=None, search_results=None):
    payload = {"choices": [{"message": {"content": content}}]}
    if citations is not None:
        payload["citations"] = citations
    if search_results is not None:
        payload["search_results"] = search_results
    return SimpleNamespace(status_code=status, json=lambda: copy.deepcopy(payload))


def raw_response(payload, *, status=200):
    return SimpleNamespace(
        status_code=status,
        json=lambda: copy.deepcopy(payload),
    )


@pytest.fixture
def provider(monkeypatch):
    """Replace the provider transport and forbid all real network access."""

    def no_network(*_args, **_kwargs):
        raise AssertionError("Network is forbidden in source-evidence tests")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket.socket, "connect_ex", no_network)
    monkeypatch.setenv("PERPLEXITY_ENABLED", "true")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "offline-test-key")
    monkeypatch.setattr(module, "ai_call_allowed", lambda _cost: True)
    calls, replies = [], []

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def post(self, url, **kwargs):
            calls.append((url, copy.deepcopy(kwargs)))
            if not replies:
                raise AssertionError("Unexpected additional provider attempt")
            reply = replies.pop(0)
            if isinstance(reply, Exception):
                raise reply
            return reply

    monkeypatch.setattr(module.httpx, "AsyncClient", Client)

    def run_result(*outcomes, story=None):
        replies.extend(outcomes)
        service = module.PerplexityService()
        method = getattr(service, "generate_article_content_with_evidence")
        return asyncio.run(method(**(story or STORY)))

    def run_string(*outcomes, story=None):
        replies.extend(outcomes)
        return asyncio.run(
            module.PerplexityService().generate_article_content(**(story or STORY))
        )

    return SimpleNamespace(
        run_result=run_result,
        run_string=run_string,
        calls=calls,
        replies=replies,
    )


def evidence(result):
    assert isinstance(result.content, str)
    return result.evidence


def test_exact_primary_citation_is_reference_evidence_not_retrieval(provider):
    result = provider.run_result(
        response(citations=[STORY["source_url"]]),
    )

    assert result.content == CONTENT
    assert evidence(result).classification == "exact_primary_url_reference"
    assert result.evidence.primary_in_citations is True
    assert result.evidence.primary_in_search_results is False
    assert not hasattr(result.evidence, "full_source_retrieved")
    assert not hasattr(result.evidence, "article_complete")
    assert len(provider.calls) == 1


def test_primary_search_result_remains_distinct_from_citation(provider):
    result = provider.run_result(
        response(
            citations=["https://secondary.invalid/report"],
            search_results=[
                {"url": STORY["source_url"], "title": "Primary article"},
            ],
        )
    )

    assert result.content == CONTENT
    assert evidence(result).classification == "exact_primary_url_reference"
    assert result.evidence.primary_in_citations is False
    assert result.evidence.primary_in_search_results is True


@pytest.mark.parametrize(
    "reference",
    [
        "https://source.invalid/another-article",
        "https://source.invalid/library-update",
        "https://secondary.invalid/library?edition=cheshire",
    ],
)
def test_secondary_or_same_domain_different_path_is_not_primary(provider, reference):
    result = provider.run_result(response(citations=[reference]))

    assert result.content == CONTENT
    assert evidence(result).classification == "secondary_only"
    assert result.evidence.primary_in_citations is False
    assert result.evidence.primary_in_search_results is False


def test_missing_metadata_preserves_content_without_inventing_failure(provider):
    result = provider.run_result(response())

    assert result.content == CONTENT
    assert evidence(result).classification == "no_provider_evidence"
    assert result.evidence.provider_status == "success"
    assert result.evidence.citation_count == 0
    assert result.evidence.search_result_count == 0


@pytest.mark.parametrize(
    "citations,search_results",
    [
        ("not-a-list", {"url": STORY["source_url"]}),
        ([None, 42, {}, []], [None, "bad", 7]),
        ({"unexpected": "mapping"}, [[STORY["source_url"]]]),
    ],
)
def test_malformed_metadata_is_ignored_without_losing_valid_content(
    provider,
    citations,
    search_results,
):
    result = provider.run_result(
        response(citations=citations, search_results=search_results)
    )

    assert result.content == CONTENT
    assert evidence(result).classification == "no_provider_evidence"
    assert result.evidence.provider_status == "success"


@pytest.mark.parametrize(
    "source_url,reference_url,expected",
    [
        (
            "https://SOURCE.invalid:443/library?edition=cheshire&utm_source=rss#top",
            "https://source.invalid/library?utm_campaign=x&edition=cheshire",
            "exact_primary_url_reference",
        ),
        (
            "http://SOURCE.invalid:80/library?edition=cheshire#top",
            "http://source.invalid/library?edition=cheshire&ref=rss",
            "exact_primary_url_reference",
        ),
        (
            "https://source.invalid/library?edition=cheshire",
            "https://source.invalid/library?edition=wirral",
            "secondary_only",
        ),
        (
            "https://source.invalid/library?edition=cheshire",
            "https://source.invalid/other?edition=cheshire",
            "secondary_only",
        ),
    ],
)
def test_url_normalisation_is_bounded_and_preserves_meaningful_queries(
    provider,
    source_url,
    reference_url,
    expected,
):
    story = {**STORY, "source_url": source_url}
    result = provider.run_result(
        response(citations=[reference_url]),
        story=story,
    )

    assert result.content == CONTENT
    assert evidence(result).classification == expected
    assert len(provider.calls) == 1


@pytest.mark.parametrize("status", [400, 429, 500])
def test_http_failure_preserves_existing_empty_result_without_retry(
    provider,
    status,
):
    result = provider.run_result(response(status=status))

    assert result.content == ""
    assert evidence(result).provider_status == "http_error"
    assert len(provider.calls) == 1


def test_timeout_preserves_existing_empty_result(provider):
    result = provider.run_result(httpx.ReadTimeout("offline timeout"))

    assert result.content == ""
    assert evidence(result).provider_status == "timeout"
    assert len(provider.calls) == 1


def test_malformed_provider_body_fails_safely(provider):
    malformed = SimpleNamespace(
        status_code=200,
        json=lambda: {"choices": "not-a-list", "citations": [STORY["source_url"]]},
    )
    result = provider.run_result(malformed)

    assert result.content == ""
    assert evidence(result).provider_status == "malformed_response"
    assert len(provider.calls) == 1


@pytest.mark.parametrize(
    "initial_payload",
    [
        {},
        {"choices": [{}]},
        {"choices": [{"message": {}}]},
        {"choices": [{"message": {"content": ""}}]},
    ],
)
def test_missing_initial_content_preserves_retry_and_final_result_evidence(
    provider,
    initial_payload,
):
    result = provider.run_result(
        raw_response(initial_payload),
        response(CONTENT, citations=[STORY["source_url"]]),
    )

    assert result.content == CONTENT
    assert result.evidence.provider_status == "success"
    assert result.evidence.attempt == "retry"
    assert result.evidence.primary_in_citations is True
    assert len(provider.calls) == 2
    events = []
    emitted = module.log_source_evidence_diagnostic(
        SimpleNamespace(info=lambda *args, **kwargs: events.append((args, kwargs))),
        result,
        context="local_rss",
    )
    assert emitted is True
    assert len(events) == 1


@pytest.mark.parametrize(
    "initial_payload",
    [
        {},
        {"choices": [{}]},
        {"choices": [{"message": {}}]},
        {"choices": [{"message": {"content": ""}}]},
    ],
)
def test_missing_initial_content_preserves_retry_for_legacy_string_interface(
    provider,
    initial_payload,
):
    content = provider.run_string(
        raw_response(initial_payload),
        response(CONTENT, search_results=[{"url": STORY["source_url"]}]),
    )

    assert content == CONTENT
    assert type(content) is str
    assert len(provider.calls) == 2


@pytest.mark.parametrize("first", ["", "I cannot write this article."])
def test_retry_uses_only_existing_second_attempt_and_final_evidence(
    provider,
    first,
):
    result = provider.run_result(
        response(first, citations=["https://secondary.invalid/first"]),
        response(CONTENT, search_results=[{"url": STORY["source_url"]}]),
    )

    assert result.content == CONTENT
    assert evidence(result).attempt == "retry"
    assert result.evidence.classification == "exact_primary_url_reference"
    assert result.evidence.primary_in_search_results is True
    assert result.evidence.primary_in_citations is False
    assert len(provider.calls) == 2


def test_string_interface_remains_compatible_and_uses_one_provider_request(provider):
    result = provider.run_string(
        response(CONTENT, citations=[STORY["source_url"]])
    )

    assert result == CONTENT
    assert type(result) is str
    assert len(provider.calls) == 1


def test_result_diagnostic_is_bounded_and_excludes_sensitive_payloads(provider):
    result = provider.run_result(
        response(
            CONTENT,
            citations=[
                STORY["source_url"],
                "https://secondary.invalid/report?token=do-not-log",
            ],
            search_results=[
                {
                    "url": STORY["source_url"],
                    "title": "Do not log this title",
                    "snippet": "Do not log this source snippet",
                }
            ],
        )
    )
    fields = result.diagnostic_fields(context="local_rss")
    serialised = repr(fields)

    assert fields["shadow_mode"] == "source_evidence_log_only"
    assert fields["context"] == "local_rss"
    assert fields["publication_effect"] == "none"
    assert fields["citation_count"] == 2
    assert fields["search_result_count"] == 1
    assert "source_url_fingerprint" in fields
    assert len(fields) <= 16
    for unsafe in (
        CONTENT,
        STORY["summary"],
        STORY["source_url"],
        "token=do-not-log",
        "Do not log this title",
        "Do not log this source snippet",
        "offline-test-key",
        "messages",
    ):
        assert unsafe not in serialised


@pytest.mark.parametrize(
    "metadata",
    [
        {"citations": ["https://source.invalid/" + ("a" * 5000)]},
        {
            "search_results": [
                {"url": "https://source.invalid/" + ("a" * 5000)}
            ]
        },
    ],
)
def test_oversized_reference_urls_are_ignored_without_changing_content(
    provider,
    metadata,
):
    oversized_url = next(iter(metadata.values()))[0]
    if isinstance(oversized_url, dict):
        oversized_url = oversized_url["url"]
    story = {**STORY, "source_url": oversized_url}
    result = provider.run_result(
        raw_response(
            {
                "choices": [{"message": {"content": CONTENT}}],
                **metadata,
            }
        ),
        story=story,
    )

    assert result.content == CONTENT
    assert result.evidence.classification == "no_provider_evidence"
    assert result.evidence.citation_count == 0
    assert result.evidence.search_result_count == 0
    assert len(provider.calls) == 1


def test_excessive_query_fields_are_ignored_without_false_primary_match(provider):
    query = "&".join(f"field{index}=value" for index in range(101))
    oversized_query_url = f"https://source.invalid/library?{query}"
    story = {**STORY, "source_url": oversized_query_url}
    result = provider.run_result(
        response(CONTENT, citations=[oversized_query_url]),
        story=story,
    )

    assert result.content == CONTENT
    assert result.evidence.classification == "no_provider_evidence"
    assert result.evidence.citation_count == 0
    assert len(provider.calls) == 1


def test_mixed_valid_and_invalid_references_keep_only_bounded_valid_evidence(provider):
    result = provider.run_result(
        response(
            CONTENT,
            citations=[
                "https://source.invalid/" + ("a" * 5000),
                None,
                STORY["source_url"],
            ],
            search_results=[
                {"url": "https://source.invalid/" + ("b" * 5000)},
                {"url": "https://secondary.invalid/report"},
            ],
        )
    )

    assert result.content == CONTENT
    assert result.evidence.classification == "exact_primary_url_reference"
    assert result.evidence.citation_count == 1
    assert result.evidence.search_result_count == 1
    assert len(provider.calls) == 1


def test_diagnostic_logging_failure_cannot_fail_generation(provider):
    result = provider.run_result(response(citations=[STORY["source_url"]]))

    class BrokenLogger:
        def info(self, *_args, **_kwargs):
            raise RuntimeError("logging unavailable")

    emitted = module.log_source_evidence_diagnostic(
        BrokenLogger(),
        result,
        context="local_rss",
    )

    assert emitted is False
    assert result.content == CONTENT
    assert len(provider.calls) == 1


def test_retry_emits_only_one_diagnostic_for_the_successful_attempt(provider):
    result = provider.run_result(
        response("I cannot write this article.", citations=["https://first.invalid"]),
        response(CONTENT, citations=[STORY["source_url"]]),
    )

    class RecordingLogger:
        def __init__(self):
            self.events = []

        def info(self, message, *args, **kwargs):
            self.events.append((message, args, kwargs))

    logger = RecordingLogger()
    emitted = module.log_source_evidence_diagnostic(
        logger,
        result,
        context="local_rss",
    )

    assert emitted is True
    assert len(logger.events) == 1
    assert result.evidence.attempt == "retry"
    assert result.evidence.primary_in_citations is True
    assert len(provider.calls) == 2


def test_source_evidence_path_does_not_import_publisher_http_or_database_clients():
    source = "\n".join(
        [
            inspect.getsource(module.PerplexityService.generate_article_content),
            inspect.getsource(
                module.PerplexityService.generate_article_content_with_evidence
            ),
            inspect.getsource(module.PerplexityService._generate_article_content_result),
            inspect.getsource(module._provider_response_content),
            inspect.getsource(module._source_reference_evidence),
            inspect.getsource(module._normalise_evidence_url),
        ]
    )

    assert "simple_scraper" not in source
    assert "scrape_article" not in source
    assert "requests.get" not in source
    assert "insert_one" not in source
    assert "update_one" not in source
