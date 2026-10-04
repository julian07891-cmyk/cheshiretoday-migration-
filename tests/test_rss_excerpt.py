"""Offline excerpt contract: no application startup or provider access."""
import ast
from pathlib import Path
import re
import subprocess

import pytest


SERVER = Path(__file__).resolve().parents[1] / "backend/server.py"


def excerpt(source, body=""):
    tree = ast.parse(SERVER.read_text())
    names = {"select_rss_excerpt", "sanitize_rss_text", "_normalize_rss_line_endings"}
    nodes = [n for n in tree.body if (
        isinstance(n, ast.FunctionDef) and n.name in names
    ) or (isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "RSS_TERMINAL_CONTINUATION_RE"
        for t in n.targets
    ))]
    namespace = {"re": re}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SERVER), "exec"), namespace)
    assert "select_rss_excerpt" in namespace, "Missing deterministic excerpt selector"
    return namespace["select_rss_excerpt"](source, body, "https://source.example/story")


LONG = "The council confirmed " + "additional verified details " * 9 + "in its report."


@pytest.mark.parametrize("source,expected", [
    (LONG, LONG),  # old 200-character boundary splits a word and a sentence
    ("A " + "verified " * 22 + "report was published.", "A " + "verified " * 22 + "report was published."),
    (LONG + "\n\nContinue reading...", LONG),
    ("A verified report. " * 10 + "\n\nContinue reading...", " ".join(["A verified report."] * 10)),
    ("The council said: “Work starts tomorrow.”", "The council said: “Work starts tomorrow.”"),
    ("Costs rose by 2.5% this year. The report is available.", "Costs rose by 2.5% this year. The report is available."),
    ("Dr. Smith met Mr. Jones at Acme Ltd. to discuss the plans.", "Dr. Smith met Mr. Jones at Acme Ltd. to discuss the plans."),
    ("A. B. Smith confirmed the investment.", "A. B. Smith confirmed the investment."),
    ("Work begins at 10 a.m. on Monday.", "Work begins at 10 a.m. on Monday."),
    ("First verified fact.\n\nSecond verified fact.\n\nRead more: https://source.example/story", "First verified fact. Second verified fact."),
    ("Full story...", ""),
    ("An unfinished preview...", ""),
    ("Continue...", ""),
    ("No sentence ending", ""),
    ("", ""),
])
def test_complete_excerpt(source, expected):
    assert excerpt(source) == expected


def test_accepted_body_fallback():
    assert excerpt("No complete source sentence", "The council approved the plan.\n\nUnfinished") == "The council approved the plan."


def test_no_safe_body_fallback():
    assert excerpt("Incomplete source", "Incomplete body...") == ""


def test_does_not_fill_remaining_budget_with_sentence_fragment():
    first = "The council has approved the housing plan."
    assert excerpt(first + " " + LONG) == first


def test_importer_only_changes_summary_not_raw_detection_or_routing():
    baseline = subprocess.check_output(["git", "show", "41444da:backend/server.py"], text=True)
    def normalized(source):
        tree = ast.parse(source)
        fn = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "_import_hybrid_news_internal")
        summary_assignments = []
        class RemoveExcerptOnly(ast.NodeTransformer):
            def visit_If(self, node):
                # The separately tested P0 source-format branch is an authorised
                # addition; all pre-existing importer routing remains pinned.
                if (isinstance(node.test, ast.Call)
                        and isinstance(node.test.func, ast.Name)
                        and node.test.func.id == "is_guardian_politics_liveblog"):
                    return None
                return self.generic_visit(node)

            def visit_Assign(self, node):
                if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "select_rss_excerpt":
                    summary_assignments.append(node.value)
                    return None
                return node
        fn = RemoveExcerptOnly().visit(fn)
        return ast.dump(fn, include_attributes=False), summary_assignments
    old, _ = normalized(baseline)
    current, assignments = normalized(SERVER.read_text())
    assert current == old  # includes title/body/metadata, classification, routing and calls
    assert sum(isinstance(v, ast.Call) and isinstance(v.func, ast.Name)
               and v.func.id == "select_rss_excerpt" for v in assignments) == 3
