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
            def visit_Name(self, node):
                if node.id == "active_record_count":
                    return ast.Call(
                        func=ast.Name(id="len", ctx=ast.Load()),
                        args=[ast.Name(id="existing_articles", ctx=ast.Load())],
                        keywords=[],
                    )
                if node.id == "archived_record_count":
                    return ast.Call(
                        func=ast.Name(id="len", ctx=ast.Load()),
                        args=[ast.Name(id="archived_existing_articles", ctx=ast.Load())],
                        keywords=[],
                    )
                return node

            def visit_FunctionDef(self, node):
                if node.name == "record_nub_pre_rewrite_rejection":
                    return None
                return self.generic_visit(node)

            def visit_For(self, node):
                if (
                    isinstance(node.iter, ast.Name)
                    and node.iter.id == "local_articles"
                    and any(
                        isinstance(child, ast.Attribute)
                        and child.attr == "append"
                        and isinstance(child.value, ast.Name)
                        and child.value.id == "cheshire_with_images"
                        for child in ast.walk(node)
                    )
                ):
                    return ast.parse(
                        "cheshire_with_images = [a for a in local_articles "
                        "if a.get('image') and a.get('title')]"
                    ).body[0]
                return self.generic_visit(node)

            def visit_If(self, node):
                # The separately tested P0 source-format branch is an authorised
                # addition; all pre-existing importer routing remains pinned.
                if (isinstance(node.test, ast.Call)
                        and isinstance(node.test.func, ast.Name)
                        and node.test.func.id in {
                            "is_guardian_politics_liveblog",
                            "has_conflicting_local_location_detail",
                        }):
                    return None
                if (
                    isinstance(node.test, ast.Name)
                    and node.test.id == "manual_review_without_ai"
                ):
                    node.body = [
                        child
                        for child in node.body
                        if isinstance(child, ast.Assign)
                        and any(
                            isinstance(target, ast.Name)
                            and target.id == "detailed_content"
                            for target in child.targets
                        )
                    ]
                    return self.generic_visit(node)
                if (
                    isinstance(node.test, ast.Name)
                    and node.test.id == "is_nub_candidate"
                    and any(
                        isinstance(child, ast.Name)
                        and child.id == "is_effectively_identical_nub_rewrite"
                        for child in ast.walk(node)
                    )
                ):
                    return ast.parse(
                        "ai_rewrite_used = bool((detailed_content or '').strip() "
                        "and detailed_content != original_content)"
                        ).body[0]
                node = self.generic_visit(node)
                if not node.body:
                    return None
                return node

            def visit_Assign(self, node):
                assigned_names = {
                    target.id
                    for target in node.targets
                    if isinstance(target, ast.Name)
                }
                if assigned_names & {
                    "active_record_count",
                    "archived_record_count",
                    "is_nub_candidate",
                    "nub_pipeline_counters",
                    "public_cap_reached",
                    "ai_budget_unavailable",
                    "preview_source_content",
                }:
                    return None
                if (
                    "cheshire_with_images" in assigned_names
                    and isinstance(node.value, ast.List)
                    and not node.value.elts
                ):
                    return None
                if (
                    assigned_names & {
                        "a",
                        "existing_articles",
                        "archived_existing_articles",
                    }
                    and isinstance(node.value, ast.Constant)
                    and node.value.value is None
                ):
                    return None
                if (
                    "manual_review_without_ai" in assigned_names
                    and any(
                        isinstance(child, ast.Name)
                        and child.id == "public_cap_reached"
                        for child in ast.walk(node.value)
                    )
                ):
                    node.value = ast.parse(
                        "(public_import_limit is not None and "
                        "public_imported >= public_import_limit) or "
                        "not ai_budget_available(0.05)"
                    ).body[0].value
                if (
                    "ai_rewrite_used" in assigned_names
                    and any(
                        isinstance(child, ast.Name)
                        and child.id == "is_nub_candidate"
                        for child in ast.walk(node.value)
                    )
                ):
                    node.value = ast.parse(
                        "bool((detailed_content or '').strip() and "
                        "detailed_content != original_content)"
                    ).body[0].value
                if (
                    len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == "rewrite_result"
                    and isinstance(node.value, ast.Await)
                ):
                    node.targets[0].id = "detailed_content"
                    for child in ast.walk(node.value):
                        if (
                            isinstance(child, ast.Attribute)
                            and child.attr == "generate_article_content_with_evidence"
                        ):
                            child.attr = "generate_article_content"
                    return node
                if (
                    len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == "detailed_content"
                    and isinstance(node.value, ast.Attribute)
                    and isinstance(node.value.value, ast.Name)
                    and node.value.value.id == "rewrite_result"
                    and node.value.attr == "content"
                ):
                    return None
                if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "select_rss_excerpt":
                    if (
                        node.value.args
                        and isinstance(node.value.args[0], ast.Name)
                        and node.value.args[0].id == "preview_source_content"
                    ):
                        node.value.args[0] = ast.Name(
                            id="original_content",
                            ctx=ast.Load(),
                        )
                    summary_assignments.append(node.value)
                    return None
                return node

            def visit_Expr(self, node):
                if (
                    isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Attribute)
                    and isinstance(node.value.func.value, ast.Name)
                    and node.value.func.value.id == "nub_pipeline_counters"
                    and node.value.func.attr in {"increment", "log"}
                ):
                    return None
                if (
                    isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id == "record_nub_pre_rewrite_rejection"
                ):
                    return None
                if (
                    isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id == "log_source_evidence_diagnostic"
                ):
                    return None
                return self.generic_visit(node)
        fn = RemoveExcerptOnly().visit(fn)
        return ast.dump(fn, include_attributes=False), summary_assignments
    old, _ = normalized(baseline)
    current, assignments = normalized(SERVER.read_text())
    assert current == old  # includes title/body/metadata, classification, routing and calls
    assert sum(isinstance(v, ast.Call) and isinstance(v.func, ast.Name)
               and v.func.id == "select_rss_excerpt" for v in assignments) == 3
