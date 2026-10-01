"""Offline contract tests for the actual automatic rewrite service payloads."""

import asyncio
import copy
import socket
from types import SimpleNamespace

import httpx
import pytest

from backend.app import perplexity_service as module


STORY = {
    "title": "Council approves library refurbishment",
    "summary": "The council approved the refurbishment on Tuesday.",
    "source": "Fixture council",
    "source_url": "https://source.invalid/library",
}
SHORT = "The council approved the library refurbishment on Tuesday."


def response(content="", status=200):
    return SimpleNamespace(
        status_code=status,
        json=lambda: {"choices": [{"message": {"content": content}}]},
    )


@pytest.fixture
def provider(monkeypatch):
    """Replace the transport entirely; also forbid accidental socket connections."""
    def no_network(*args, **kwargs):
        raise AssertionError("Network is forbidden in rewrite contract tests")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket.socket, "connect_ex", no_network)
    monkeypatch.setenv("PERPLEXITY_ENABLED", "true")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "offline-test-key")
    monkeypatch.setattr(module, "ai_call_allowed", lambda cost: True)
    calls, replies = [], []

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
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

    def run(*outcomes):
        replies.extend(outcomes)
        return asyncio.run(module.PerplexityService().generate_article_content(**STORY))

    return SimpleNamespace(run=run, calls=calls)


def prompts(provider):
    assert provider.run(response(""), response(SHORT)) == SHORT
    assert len(provider.calls) == 2
    return ["\n".join(m["content"] for m in call[1]["json"]["messages"])
            for call in provider.calls]


@pytest.mark.parametrize("attempt", [0, 1], ids=["first", "retry"])
def test_conditional_depth_and_no_padding_in_actual_payload(provider, attempt):
    prompt = prompts(provider)[attempt].lower()
    for required in (
        "400-650 words", "700-900 words", "not quotas",
        "where verified evidence supports", "shorter accurate",
        "never invent facts to meet a word target",
        "never repeat facts merely to increase length",
        "every paragraph", "distinct verified information",
        "generic filler", "essay-style",
    ):
        assert required in prompt
    assert "do not refuse" not in prompt
    assert "do not explain limitations" not in prompt
    assert "minimum acceptable output" not in prompt
    assert "at least 2000 characters" not in prompt
    assert "explain why it matters" not in prompt


@pytest.mark.parametrize("attempt", [0, 1], ids=["first", "retry"])
def test_verified_reporting_checklist_in_actual_payload(provider, attempt):
    prompt = prompts(provider)[attempt].lower()
    for required in (
        "actively research", "core development", "exact names and roles",
        "exact dates and times", "exact places", "figures and amounts",
        "chronology", "background directly supported by sources",
        "attributed responses and viewpoints", "confirmed next steps",
        "deadlines", "practical information",
        "practical consequences only when explicitly supported",
    ):
        assert required in prompt


@pytest.mark.parametrize("attempt", [0, 1], ids=["first", "retry"])
def test_primary_source_and_unsupported_detail_rules(provider, attempt):
    prompt = prompts(provider)[attempt].lower()
    for value in STORY.values():
        assert value.lower() in prompt
    for required in (
        "source url", "primary reference", "reputable corroborating sources",
        "must not override or conflate the primary story without evidence",
        "street names", "quotes", "anonymous residents", "repair bills",
        "smashed windows", "police involvement", "social media reaction",
        "business history", "previous incidents",
    ):
        assert required in prompt


def test_request_contract_and_short_success_is_not_retried(provider):
    assert provider.run(response(SHORT)) == SHORT
    assert len(provider.calls) == 1
    url, call = provider.calls[0]
    assert url == module.PERPLEXITY_API_URL
    assert call["headers"] == {"Authorization": "Bearer offline-test-key", "Content-Type": "application/json"}
    assert call["timeout"] == 90.0
    payload = call["json"]
    assert {k: v for k, v in payload.items() if k != "messages"} == {
        "model": "sonar", "max_tokens": 2000, "temperature": 0.2,
        "return_citations": True, "search_recency_filter": "week",
    }
    assert [m["role"] for m in payload["messages"]] == ["system", "user"]


@pytest.mark.parametrize("first", ["", "   ", "I cannot write this article."])
def test_empty_or_refusal_retries_once_with_unchanged_settings(provider, first):
    assert provider.run(response(first), response(SHORT)) == SHORT
    assert len(provider.calls) == 2
    call = provider.calls[1][1]
    assert call["timeout"] == 90.0
    assert {k: v for k, v in call["json"].items() if k != "messages"} == {
        "model": "sonar", "max_tokens": 2400, "temperature": 0.4,
        "return_citations": True, "search_recency_filter": "week",
    }


@pytest.mark.parametrize("status", [400, 429, 500])
def test_non_200_returns_empty_without_retry(provider, status):
    assert provider.run(response(status=status)) == ""
    assert len(provider.calls) == 1


@pytest.mark.parametrize("retry", [False, True])
def test_timeout_is_safe(provider, retry):
    outcomes = [response("")] if retry else []
    assert provider.run(*outcomes, httpx.ReadTimeout("offline timeout")) == ""
    assert len(provider.calls) == (2 if retry else 1)


@pytest.mark.parametrize("final", ["", "I cannot write this report."])
def test_unusable_retry_returns_empty_without_third_call(provider, final):
    assert provider.run(response(""), response(final)) == ""
    assert len(provider.calls) == 2


def test_retry_non_200_is_safe(provider):
    assert provider.run(response(""), response(status=503)) == ""
    assert len(provider.calls) == 2


@pytest.mark.parametrize("retry", [False, True])
def test_cleanup_preserves_substantive_paragraphs(provider, retry):
    raw = "**The council approved £2.5 million on Tuesday.**[1]\n\nThe library will close on 4 May for the confirmed works.\n\nThe council said reopening is scheduled for September. (Word count: 30)"
    expected = "The council approved £2.5 million on Tuesday.\n\nThe library will close on 4 May for the confirmed works.\n\nThe council said reopening is scheduled for September."
    outcomes = [response("")] if retry else []
    assert provider.run(*outcomes, response(raw)) == expected
    assert len(provider.calls) == (2 if retry else 1)


def test_disabled_retains_existing_summary_link_fallback(provider, monkeypatch):
    monkeypatch.setenv("PERPLEXITY_ENABLED", "false")
    assert provider.run() == STORY["summary"] + "\n\nRead the full story at the source: " + STORY["source_url"]
    assert provider.calls == []


def test_budget_block_returns_empty_without_provider(provider, monkeypatch):
    monkeypatch.setattr(module, "ai_call_allowed", lambda cost: False)
    assert provider.run() == ""
    assert provider.calls == []


def test_missing_key_returns_empty_without_provider(provider, monkeypatch):
    monkeypatch.delenv("PERPLEXITY_API_KEY")
    assert provider.run() == ""
    assert provider.calls == []
