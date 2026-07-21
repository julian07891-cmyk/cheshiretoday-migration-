import copy
import importlib
import json
import subprocess
import sys
from dataclasses import dataclass

import pytest


MODULE_NAME = "backend.scripts.backfill_newsquest_images"


@pytest.fixture
def module():
    sys.modules.pop(MODULE_NAME, None)
    return importlib.import_module(MODULE_NAME)


@dataclass
class FakeUpdateResult:
    matched_count: int
    modified_count: int


class FakeCursor:
    def __init__(self, records):
        self.records = records

    def sort(self, field, direction):
        assert field == "_id"
        assert direction == 1
        return self

    def __iter__(self):
        return iter(sorted(self.records, key=lambda item: item["_id"]))


class FakeCollection:
    def __init__(self, records):
        self.records = copy.deepcopy(records)
        self.writes = []

    def find(self, query, projection):
        assert set(projection) == {"_id", "image", "source_url"}
        matching = []
        for record in self.records:
            image = record.get("image")
            source = record.get("source_url")
            if (
                isinstance(image, str)
                and "/resources/images/" in image.lower()
                and isinstance(source, str)
            ):
                matching.append(
                    {key: record[key] for key in projection if key in record}
                )
        return FakeCursor(matching)

    def update_one(self, filter_document, update_document):
        assert set(update_document) == {"$set"}
        assert set(update_document["$set"]) == {"image"}
        self.writes.append(
            (copy.deepcopy(filter_document), copy.deepcopy(update_document))
        )
        for record in self.records:
            if all(
                record.get(key) == value
                for key, value in filter_document.items()
            ):
                before = record.get("image")
                record["image"] = update_document["$set"]["image"]
                return FakeUpdateResult(1, int(before != record["image"]))
        return FakeUpdateResult(0, 0)

    def find_one(self, filter_document, projection):
        assert projection == {"_id": 0, "image": 1}
        for record in self.records:
            if record.get("_id") == filter_document.get("_id"):
                return {"image": record.get("image")}
        return None


def article(record_id="a1", **overrides):
    record = {
        "_id": record_id,
        "image": (
            "https://www.chesterstandard.co.uk/"
            "resources/images/legacy.jpg"
        ),
        "source_url": "https://www.chesterstandard.co.uk/news/example-story/",
        "title": "Example story",
        "content": "Unchanged body",
        "created_at": "unchanged",
        "metadata": {"keep": True},
    }
    record.update(overrides)
    return record


def valid_html(url="https://images.example.com/resolved.jpg"):
    return f'<html><meta property="og:image" content="{url}"></html>'


def repository(module, records):
    collection = FakeCollection(records)
    return module.ArticleRepository(collection), collection


def test_import_performs_no_work(monkeypatch):
    monkeypatch.setattr(
        "requests.get", lambda *args, **kwargs: pytest.fail("network")
    )
    sys.modules.pop(MODULE_NAME, None)
    imported = importlib.import_module(MODULE_NAME)
    assert imported.CONFIRMATION_TEXT == "APPLY NEWSQUEST IMAGE BACKFILL"


def test_repository_root_cli_invocation_can_load_shared_resolver():
    result = subprocess.run(
        [
            sys.executable,
            "backend/scripts/backfill_newsquest_images.py",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--dry-run" in result.stdout


def test_dry_run_performs_zero_writes(module):
    repo, collection = repository(module, [article()])
    stats = module.execute_dry_run(repo, fetch_page=lambda _: valid_html())
    assert stats.updates_planned == 1
    assert stats.records_updated == 0
    assert collection.writes == []


def test_dry_run_is_deterministic_and_ordered(module):
    records = [article("b"), article("a")]
    repo, _ = repository(module, records)
    first = module.build_plan(
        repo, fetch_page=lambda _: valid_html(), mode="dry-run"
    )
    second = module.build_plan(
        repo, fetch_page=lambda _: valid_html(), mode="dry-run"
    )
    assert first == second
    assert [item.record_id for item in first.updates] == ["a", "b"]


def test_expected_count_mismatch_stops_before_confirmation_and_writes(module):
    repo, collection = repository(module, [article()])
    prompted = []
    with pytest.raises(module.ConfigurationError):
        module.execute_apply(
            repo,
            fetch_page=lambda _: valid_html(),
            expected_count=2,
            input_func=lambda prompt: prompted.append(prompt)
            or module.CONFIRMATION_TEXT,
            stdin_isatty=lambda: True,
        )
    assert prompted == []
    assert collection.writes == []


def test_confirmation_failure_performs_zero_writes(module):
    repo, collection = repository(module, [article()])
    with pytest.raises(module.ConfirmationError):
        module.execute_apply(
            repo,
            fetch_page=lambda _: valid_html(),
            expected_count=1,
            input_func=lambda _: "wrong",
            stdin_isatty=lambda: True,
        )
    assert collection.writes == []


def test_non_interactive_apply_performs_zero_writes(module):
    repo, collection = repository(module, [article()])
    with pytest.raises(module.ConfirmationError):
        module.execute_apply(
            repo,
            fetch_page=lambda _: valid_html(),
            expected_count=1,
            stdin_isatty=lambda: False,
        )
    assert collection.writes == []


def test_lookup_failure_is_counted_without_write(module):
    repo, collection = repository(module, [article()])

    def fail(_):
        raise RuntimeError("private lookup detail")

    stats = module.execute_dry_run(repo, fetch_page=fail)
    assert stats.lookup_failures == 1
    assert stats.updates_planned == 0
    assert collection.writes == []


def test_lookup_failure_blocks_apply_before_confirmation_or_write(module):
    repo, collection = repository(module, [article()])
    prompted = []

    def fail(_):
        raise RuntimeError("private lookup detail")

    with pytest.raises(module.BackfillError):
        module.execute_apply(
            repo,
            fetch_page=fail,
            expected_count=1,
            input_func=lambda prompt: prompted.append(prompt)
            or module.CONFIRMATION_TEXT,
            stdin_isatty=lambda: True,
        )
    assert prompted == []
    assert collection.writes == []


@pytest.mark.parametrize(
    "html",
    [
        "<html></html>",
        '<meta property="og:image" content="javascript:alert(1)">',
        '<meta property="og:image" content="/relative.jpg">',
    ],
)
def test_invalid_open_graph_image_is_unchanged(module, html):
    repo, collection = repository(module, [article()])
    stats = module.execute_dry_run(repo, fetch_page=lambda _: html)
    assert stats.unchanged == 1
    assert stats.updates_planned == 0
    assert collection.writes == []


@pytest.mark.parametrize(
    "source_url",
    [
        "https://www.chesterstandard.co.uk/news/example/",
        "https://chesterstandard.co.uk/news/example/",
        "https://www.warringtonguardian.co.uk/news/example/",
        "https://warringtonguardian.co.uk/news/example/",
    ],
)
def test_supported_newsquest_hosts_are_planned(module, source_url):
    repo, _ = repository(module, [article(source_url=source_url)])
    stats = module.execute_dry_run(repo, fetch_page=lambda _: valid_html())
    assert stats.updates_planned == 1


def test_unsupported_source_is_never_looked_up(module):
    repo, collection = repository(
        module,
        [article(source_url="https://example.com/news/story/")],
    )
    calls = []
    stats = module.execute_dry_run(
        repo, fetch_page=lambda url: calls.append(url) or valid_html()
    )
    assert stats.candidates == 0
    assert calls == []
    assert collection.writes == []


def test_nonlegacy_image_is_not_a_candidate(module):
    repo, collection = repository(
        module,
        [article(image="https://images.example.com/already-good.jpg")],
    )
    stats = module.execute_dry_run(repo, fetch_page=lambda _: valid_html())
    assert stats.scanned == 0
    assert stats.updates_planned == 0
    assert collection.writes == []


def test_successful_apply_updates_only_image_and_verifies(module):
    original = article()
    repo, collection = repository(module, [original])
    stats = module.execute_apply(
        repo,
        fetch_page=lambda _: valid_html(),
        expected_count=1,
        input_func=lambda _: module.CONFIRMATION_TEXT,
        stdin_isatty=lambda: True,
    )
    assert stats.records_updated == 1
    assert stats.status == "verified"
    changed = collection.records[0]
    assert changed["image"] == "https://images.example.com/resolved.jpg"
    assert {
        key: value for key, value in changed.items() if key != "image"
    } == {key: value for key, value in original.items() if key != "image"}
    assert collection.writes[0][1] == {
        "$set": {"image": "https://images.example.com/resolved.jpg"}
    }


def test_idempotent_second_run_plans_and_writes_nothing(module):
    repo, collection = repository(module, [article()])
    module.execute_apply(
        repo,
        fetch_page=lambda _: valid_html(),
        expected_count=1,
        input_func=lambda _: module.CONFIRMATION_TEXT,
        stdin_isatty=lambda: True,
    )
    writes_after_first = len(collection.writes)
    stats = module.execute_dry_run(repo, fetch_page=lambda _: valid_html())
    assert stats.updates_planned == 0
    assert len(collection.writes) == writes_after_first

    with pytest.raises(module.ConfigurationError):
        module.execute_apply(
            repo,
            fetch_page=lambda _: valid_html(),
            expected_count=1,
            input_func=lambda _: module.CONFIRMATION_TEXT,
            stdin_isatty=lambda: True,
        )
    assert len(collection.writes) == writes_after_first


def test_whitespace_around_legacy_url_does_not_create_false_update(module):
    original = (
        "  https://www.chesterstandard.co.uk/resources/images/legacy.jpg  "
    )
    repo, collection = repository(module, [article(image=original)])
    stats = module.execute_dry_run(repo, fetch_page=lambda _: "<html></html>")
    assert stats.updates_planned == 0
    assert collection.writes == []


def test_conditional_conflict_is_reported(module):
    class ConflictRepository:
        def scan_candidates(self):
            return [article()]

        def apply_update(self, update):
            return module.UpdateResult(
                modified_count=0, conditional_conflicts=1
            )

        def verify_image(self, update):
            pytest.fail("conflicted update must not be verified")

    stats = module.execute_apply(
        ConflictRepository(),
        fetch_page=lambda _: valid_html(),
        expected_count=1,
        input_func=lambda _: module.CONFIRMATION_TEXT,
        stdin_isatty=lambda: True,
    )
    assert stats.conditional_conflicts == 1
    assert stats.status == "failed"


def test_verification_failure_fails_closed(module):
    class VerificationRepository:
        def scan_candidates(self):
            return [article()]

        def apply_update(self, update):
            return module.UpdateResult(
                modified_count=1, conditional_conflicts=0
            )

        def verify_image(self, update):
            return False

    with pytest.raises(module.VerificationError):
        module.execute_apply(
            VerificationRepository(),
            fetch_page=lambda _: valid_html(),
            expected_count=1,
            input_func=lambda _: module.CONFIRMATION_TEXT,
            stdin_isatty=lambda: True,
        )


def test_cli_requires_expected_count_for_apply(module, capsys):
    called = []
    result = module.main(
        ["--apply"], repository_factory=lambda: called.append(True)
    )
    assert result == 1
    assert called == []
    assert "--expected-count is required" in capsys.readouterr().err


def test_cli_rejects_expected_count_for_dry_run(module, capsys):
    result = module.main(["--dry-run", "--expected-count", "1"])
    assert result == 1
    assert "--expected-count is only valid" in capsys.readouterr().err


def test_cli_prints_aggregate_json_only(module, capsys):
    repo, _ = repository(module, [article()])
    result = module.main(
        ["--dry-run"],
        repository_factory=lambda: repo,
        fetch_page=lambda _: valid_html(),
    )
    assert result == 0
    output = capsys.readouterr().out.strip()
    payload = json.loads(output)
    assert payload["updates_planned"] == 1
    assert set(payload) == {
        "mode",
        "scanned",
        "candidates",
        "resolved",
        "unchanged",
        "lookup_failures",
        "updates_planned",
        "records_updated",
        "conditional_conflicts",
        "verification_failures",
        "status",
    }
    assert "example-story" not in output
    assert "legacy.jpg" not in output
    assert "resolved.jpg" not in output


def test_cli_error_is_privacy_safe(module, capsys):
    class BrokenRepository:
        def scan_candidates(self):
            raise RuntimeError("mongodb://secret@example.invalid private-id")

    result = module.main(
        ["--dry-run"], repository_factory=lambda: BrokenRepository()
    )
    assert result == 1
    error = capsys.readouterr().err
    assert "mongodb://" not in error
    assert "private-id" not in error
    assert "unexpected error" in error
