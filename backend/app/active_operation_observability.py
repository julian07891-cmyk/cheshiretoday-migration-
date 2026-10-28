"""Bounded process-local diagnostics, never a lock or release-clearance gate."""

import asyncio
import math
import re
import threading
import time
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import wraps
from types import MappingProxyType


COVERAGE_VERSION = "active_operations_v1"
OPERATION_TYPES = (
    "article_generation", "article_import", "article_maintenance", "daily_brief",
    "weekly_roundup", "manual_newsletter", "admin_ai", "provider_evidence",
)
REQUIRED_ENTRY_POINTS = MappingProxyType({
    "daily_article_generation": "article_generation",
    "trigger_daily_generation": "article_generation",
    "generate_articles": "article_generation",
    "_generate_articles_internal": "article_generation",
    "import_hybrid_news": "article_import",
    "_import_hybrid_news_internal": "article_import",
    "import_real_news": "article_import",
    "clear_and_refresh_news": "article_maintenance",
    "regenerate_recent_article_content": "article_maintenance",
    "regenerate_article_content": "article_maintenance",
    "_remove_duplicates_internal": "article_maintenance",
    "cap_visible_articles": "article_maintenance",
    "send_scheduled_news_digest": "daily_brief",
    "send_weekly_roundup_email": "weekly_roundup",
    "send_digest_now": "manual_newsletter",
    "send_digest_test": "manual_newsletter",
    "send_weekly_roundup_test": "manual_newsletter",
    "send_weekly_roundup_batch_test": "manual_newsletter",
    "send_breaking_news_alert": "manual_newsletter",
    "send_migration_announcement": "manual_newsletter",
    "send_site_update_part1": "manual_newsletter",
    "send_site_update_part2": "manual_newsletter",
    "admin_run_onboarding_emails": "manual_newsletter",
    "admin_send_campaign_email": "manual_newsletter",
    "admin_ai_review_article": "admin_ai",
    "admin_openai_rewrite_draft": "admin_ai",
    "admin_perplexity_rewrite_test": "admin_ai",
    "receive_resend_webhook": "provider_evidence",
})


class ActiveOperationRegistry:
    def __init__(self, *, instance_id, process_id, monotonic=time.monotonic,
                 utc_now=lambda: datetime.now(timezone.utc)):
        self._instance_id = (
            instance_id if isinstance(instance_id, str)
            and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", instance_id)
            and instance_id.lower() != "unknown" else None
        )
        self._process_id = process_id if type(process_id) is int and process_id > 0 else None
        self._monotonic = monotonic
        self._utc_now = utc_now
        self._counts = dict.fromkeys(OPERATION_TYPES, 0)
        self._owner = ContextVar("active_operation_owner", default=None)
        self._mutex = threading.RLock()
        self._checked_at = None
        self._coverage_reason = "incomplete_coverage"
        self._unavailable = False

    def mark_unavailable(self):
        # Sticky: a lost increment/decrement cannot be repaired by inspecting
        # wrappers. Only a new registry/process can restore trustworthy counts.
        with self._mutex:
            self._unavailable = True

    def confirm_coverage(self, entry_points, *, version):
        """Accept a caller-validated manifest; never clear an integrity failure."""
        try:
            with self._mutex:
                self._checked_at = None
                if version != COVERAGE_VERSION:
                    self._coverage_reason = "unsupported_coverage"
                elif entry_points != REQUIRED_ENTRY_POINTS:
                    self._coverage_reason = "incomplete_coverage"
                else:
                    checked_at = self._monotonic()
                    if not math.isfinite(checked_at):
                        raise ValueError("invalid diagnostic clock")
                    self._checked_at = checked_at
                    self._coverage_reason = "ok"
        except Exception:
            self.mark_unavailable()

    @contextmanager
    def track(self, kind):
        if kind not in OPERATION_TYPES:
            raise ValueError("unsupported operation type")
        try:
            task = asyncio.current_task()
        except RuntimeError:
            task = None
        # Retain only scalar identity, never a Task, request or business object.
        owner = (threading.get_ident(), id(task) if task is not None else None)
        if self._owner.get() == owner:
            yield
            return
        token = self._owner.set(owner)
        with self._mutex:
            self._counts[kind] += 1
        try:
            yield
        finally:
            try:
                with self._mutex:
                    self._counts[kind] -= 1
                    if self._counts[kind] < 0:
                        self._unavailable = True
            finally:
                self._owner.reset(token)

    def snapshot(self, *, max_age_seconds=30):
        data = {
            "scope": "process_local", "status": "unknown", "reason": "unavailable",
            "instance_id": self._instance_id, "process_id": self._process_id,
            "snapshot_at": None, "coverage_version": COVERAGE_VERSION,
            "coverage_age_seconds": None, "active_counts": None,
            "all_instances_covered": False,
        }
        try:
            now = self._utc_now()
            if not isinstance(now, datetime) or now.tzinfo is None:
                raise ValueError("invalid diagnostic timestamp")
            data["snapshot_at"] = now.astimezone(timezone.utc).isoformat()
            with self._mutex:
                if self._unavailable or not self._instance_id or not self._process_id:
                    return data
                data["reason"] = self._coverage_reason
                if self._checked_at is None:
                    return data
                age = self._monotonic() - self._checked_at
                if not math.isfinite(age) or age < 0 or not math.isfinite(max_age_seconds) or max_age_seconds < 0:
                    raise ValueError("invalid diagnostic age")
                data["coverage_age_seconds"] = age
                if age > max_age_seconds:
                    data["reason"] = "stale_coverage"
                    return data
                data.update(status="known", reason="ok", active_counts=dict(self._counts))
        except Exception:
            self.mark_unavailable()
            data.update(status="unknown", reason="unavailable", active_counts=None)
        return data


def _invalidate(registry):
    try:
        registry.mark_unavailable()
    except Exception:
        pass


def observe_operation(kind, registry_provider):
    """Wrap async work once; diagnostic failure never retries or masks it."""
    if kind not in OPERATION_TYPES:
        raise ValueError("unsupported operation type")

    def decorate(function):
        @wraps(function)
        async def observed(*args, **kwargs):
            registry = None
            context = None
            try:
                registry = registry_provider()
                context = registry.track(kind)
                context.__enter__()
            except Exception:
                _invalidate(registry)
                context = None
            try:
                return await function(*args, **kwargs)
            finally:
                if context is not None:
                    try:
                        # Registry exit only releases diagnostics. Do not inject
                        # business exceptions into a potentially failing observer.
                        context.__exit__(None, None, None)
                    except Exception:
                        _invalidate(registry)

        observed.__active_operation_type__ = kind
        observed.__active_operation_wrapper__ = observed
        observed.__active_operation_registry_provider__ = registry_provider
        return observed
    return decorate


def is_observed_operation(function, kind, registry_provider):
    return (
        getattr(function, "__active_operation_wrapper__", None) is function
        and getattr(function, "__active_operation_type__", None) == kind
        and getattr(function, "__active_operation_registry_provider__", None) is registry_provider
        and asyncio.iscoroutinefunction(getattr(function, "__wrapped__", None))
    )
