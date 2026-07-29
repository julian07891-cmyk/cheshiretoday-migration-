"""Regression checks for committed Admin credential hygiene."""

import ast
import json
import re
from pathlib import Path

import pytest

from tests.external_admin_test_safety import get_local_admin_test_credentials


ROOT = Path(__file__).resolve().parents[1]
LEGACY_ADMIN_TESTS = (
    ROOT / "tests/test_facebook_features.py",
    ROOT / "tests/test_most_read_push_features.py",
    ROOT / "tests/test_scheduler_lock.py",
)
HISTORICAL_REPORTS = tuple((ROOT / "test_reports").glob("iteration_*.json"))


def test_legacy_tests_do_not_assign_literal_admin_credentials():
    forbidden_names = {"ADMIN_USERNAME", "ADMIN_PASSWORD"}
    for path in LEGACY_ADMIN_TESTS:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        literal_assignments = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                continue
            for target in targets:
                if isinstance(target, ast.Name) and target.id in forbidden_names:
                    literal_assignments.append((target.id, node.lineno))
        assert literal_assignments == [], f"literal Admin credential in {path.name}"


def test_historical_reports_contain_no_plaintext_admin_passwords():
    for path in HISTORICAL_REPORTS:
        data = json.loads(path.read_text(encoding="utf-8"))
        password = data.get("test_credentials", {}).get("admin_password")
        if password is not None:
            assert password == "[REDACTED]", f"unredacted Admin password in {path.name}"


def test_product_requirements_contains_no_admin_password_pair():
    text = (ROOT / "memory/PRD.md").read_text(encoding="utf-8")
    assert not re.search(r"(?im)^\s*-\s*\*\*Admin\*\*:[^\n]*/\s*(?!\[REDACTED\])\S+", text)


@pytest.mark.parametrize(
    "target",
    (
        "https://cheshiretoday.co.uk",
        "https://www.cheshiretoday.co.uk",
        "https://localhost.evil.example",
        "",
    ),
)
def test_admin_credentials_are_unavailable_for_non_loopback_targets(target):
    with pytest.raises(pytest.skip.Exception):
        get_local_admin_test_credentials(target)


@pytest.mark.parametrize(
    "target",
    (
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://[::1]:8000",
    ),
)
def test_admin_credentials_are_test_only_for_loopback_targets(target, monkeypatch):
    monkeypatch.delenv("CT_TEST_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("CT_TEST_ADMIN_PASSWORD", raising=False)
    credentials = get_local_admin_test_credentials(target)
    assert credentials["username"].endswith(".invalid")
    assert "test" in credentials["password"]
