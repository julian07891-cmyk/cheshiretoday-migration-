"""Offline regression for the real nested homepage UK predicate; no server startup."""

import ast
import copy
from pathlib import Path
import re
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "backend/server.py"
BASELINE = "b98a49eaba32659bd0e83fa27506c944802e5d65"
DIESEL = {
    "title": "UK Engages European Allies on Emergency Diesel Stockpiles Amid US Supply Threats",
    "summary": "The UK is in discussions with European nations regarding the potential release of emergency diesel reserves following threats from the Trump administration to cut off US supplies.",
    "category": "UK News",
    "source": "The Guardian",
    "source_url": "https://www.theguardian.com/business/2026/oct/01/britain-talks-european-allies-eu-emergency-diesel-stockpiles-reserves",
}


@pytest.fixture
def is_noise():
    tree = ast.parse(SERVER.read_text())
    handler = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "get_articles")
    # Compile the actual enclosing constants and predicate, never a copied rule.
    block = next(n for n in ast.walk(handler) if isinstance(n, ast.If) and any(
        isinstance(child, ast.FunctionDef) and child.name == "is_noise_uk" for child in n.body
    ))
    nodes = []
    for node in block.body:
        nodes.append(node)
        if isinstance(node, ast.FunctionDef) and node.name == "is_noise_uk":
            break
    namespace = {"re": re}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SERVER), "exec"), namespace)
    return namespace["is_noise_uk"]


def test_exact_diesel_metadata_is_accepted_without_body(is_noise):
    assert "content" not in DIESEL
    assert is_noise(DIESEL) is False


@pytest.mark.parametrize("title", [
    "Britain reviews strategic petrol reserves",
    "British ministers discuss fuel supply security",
    "UK prepares for diesel shortages",
])
def test_bounded_supply_context(is_noise, title):
    assert is_noise({**DIESEL, "title": title, "summary": ""}) is False


@pytest.mark.parametrize("title", [
    "UK walkers fuel their enthusiasm for autumn",
    "UK collector restores a diesel engine",
    "British nature reserves welcome visitors",
    "UK hobbyists share a supply of coloured beads",
    "UK enthusiasts discuss fuel supplies for their models",
    "Canada reviews emergency diesel stockpiles",
    "UKulele enthusiasts discuss emergency diesel stockpiles",
    "UK discusses emergency diesel stockpilesque sculptures",
])
def test_isolated_words_and_missing_context_stay_rejected(is_noise, title):
    assert is_noise({**DIESEL, "title": title, "summary": ""}) is True


@pytest.mark.parametrize("changes", [
    {"source": "BBC Sport"},
    {"category": "Sports"},
    {"source_url": "https://example.test/sport/story"},
    {"source_url": "https://example.test/video/story"},
    {"title": "Watch video: UK emergency diesel stockpiles"},
    {"title": "The papers: UK emergency diesel stockpiles"},
    {"title": "The papers: Britain's boundless energy"},
    {"title": "MP discusses UK emergency diesel stockpiles"},
])
def test_earlier_noise_and_politics_guards_keep_precedence(is_noise, changes):
    assert is_noise({**DIESEL, **changes}) is True


@pytest.mark.parametrize("title", [
    "UK inflation slows as prices stabilise",
    "UK energy bills fall",
    "Council announces housing investment",
])
def test_existing_economic_acceptance_unchanged(is_noise, title):
    assert is_noise({**DIESEL, "title": title, "summary": ""}) is False


def test_body_does_not_supply_missing_metadata_context(is_noise):
    assert is_noise({**DIESEL, "title": "UK officials meet", "summary": "",
                     "content": DIESEL["title"] + " " + DIESEL["summary"]}) is True


@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize("prefix,accepted", [("", True), ("Podcast: ", False), ("Murder inquiry: ", False)])
def test_real_handler_keeps_later_guards_and_fallback(monkeypatch, fallback, prefix, accepted):
    import asyncio
    from tests.test_homepage_article_list_timing import FakeArticlesCollection, _article, server

    article = {**_article(1, local=False), **DIESEL, "title": prefix + DIESEL["title"]}
    collection = FakeArticlesCollection(
        local=[], uk=[_article(2, local=False)] if fallback else [article],
        fallback=[article] if fallback else [],
    )
    monkeypatch.setattr(server.db, "articles", collection)
    monkeypatch.setenv("UK_FILTER_NOISE", "1")
    result = asyncio.run(server.get_articles(limit=80))
    assert [a["id"] for a in result] == (["article-1"] if accepted else [])
    # Query-contract assertions, not claims that this lightweight fake executes Mongo filters.
    for call in collection.calls:
        if call[0] == "find":
            query = call[1]
            assert (query.get("manual_review_hidden_from_public") == {"$ne": True}
                    or {"manual_review_hidden_from_public": {"$ne": True}} in query.get("$and", []))
            archive_clause = {"$or": [{"archived": {"$exists": False}}, {"archived": False}]}
            assert (archive_clause in query.get("$and", [])
                    or query.get("$or") == archive_clause["$or"])


def test_every_other_server_decision_matches_baseline():
    """Locks visibility, sensitive handling, sort/caps/dedupe, hubs and imports."""
    old = subprocess.run(
        ["git", "show", f"{BASELINE}:backend/server.py"], cwd=ROOT,
        check=True, capture_output=True, text=True,
    ).stdout

    class MaskPredicate(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            if node.name == "is_noise_uk":
                node = copy.deepcopy(node)
                node.body = [ast.Pass()]
                return node
            return self.generic_visit(node)

    assert ast.dump(MaskPredicate().visit(ast.parse(SERVER.read_text()))) == ast.dump(
        MaskPredicate().visit(ast.parse(old))
    )
