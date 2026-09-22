"""Redact native unsubscribe queries in Uvicorn 0.25 access records only.

This is not a Render/proxy/APM log control and never receives an ASGI scope.
"""

import logging
import re
from urllib.parse import unquote

from .newsletter_delivery import ONE_CLICK_PATH


_ACCESS_FORMAT = '%s - "%s %s HTTP/%s" %d'


def _sensitive_target(target: str) -> bool:
    # Uvicorn quotes scope.path, including the colon in h11 absolute-form URLs.
    # Split off the query BEFORE decoding: a URL inside another route's query
    # must never be mistaken for the request target. Host is not authorization.
    path = unquote(target.partition("?")[0])
    if re.match(r"(?i)^https?://", path):
        # Only the authority delimiter matters here; malformed authority details
        # must not stop privacy protection (urlsplit validates bracketed hosts).
        path = "/" + path.split("://", 1)[1].partition("/")[2]
    return path in (ONE_CLICK_PATH, ONE_CLICK_PATH + "/")


def _text_has_sensitive_query(text: str) -> bool:
    # Interpret complete whitespace-delimited fields, never search inside a URL
    # query. Peel only enclosing punctuation and field labels BEFORE the target.
    # Thus target=(/foo?next=/api/...) still identifies /foo, not its query value.
    for field in text.split():
        while True:
            field = field.lstrip("([{<\"'")
            if field.startswith(("b'", 'b"')):
                field = field[2:]
            if field.startswith("/") or re.match(r"(?i)^https?(?::|%3a)//", field):
                break
            label = re.match(r"[A-Za-z_][\w.-]*[\"']?[:=]", field)
            if label is None:
                break
            field = field[label.end():]
        field = field.rstrip(")]}>\"',;")
        if "?" in field and _sensitive_target(field):
            return True
    return False


def _contains_sensitive_target(value) -> bool:
    # Inspect built-in record shapes without invoking arbitrary object repr/str.
    if isinstance(value, bytes):
        value = value.decode("ascii", errors="replace")
    if isinstance(value, str):
        return _text_has_sensitive_query(value)
    if isinstance(value, (tuple, list)):
        return any(_contains_sensitive_target(part) for part in value)
    if isinstance(value, dict):
        return any(_contains_sensitive_target(part) for part in value.values())
    return False


def _sanitize_record(record) -> bool:
    args = record.args
    # Unknown sensitive layouts are suppressed, not guessed at. The supported
    # formatter receives a tuple even if another producer supplied a list.
    if (not isinstance(args, (tuple, list)) or len(args) != 5
            or not isinstance(args[2], str) or not _sensitive_target(args[2])
            or record.msg != _ACCESS_FORMAT or record.exc_info or record.exc_text
            or record.stack_info):
        return False
    record.args = (*args[:2], args[2].partition("?")[0], *args[3:])
    record.message = record.getMessage()
    # A prior formatter may have cached a request line separately.
    record.__dict__.pop("request_line", None)
    # Fail closed if another standard field still carries a sensitive target.
    return not _contains_sensitive_target((record.msg, record.args[:2], record.args[3:]))


class NewsletterAccessLogFilter(logging.Filter):
    _newsletter_one_click_query_filter = True

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name != "uvicorn.access":
            return True
        try:
            raw_sensitive = _contains_sensitive_target((
                record.msg, record.args, record.__dict__.get("message"),
                record.__dict__.get("request_line"),
            ))
            args = record.args
            # Preserve the precise pinned five-argument path (including list
            # equivalents). No generic reconstruction of alternate records.
            if (record.msg == _ACCESS_FORMAT and isinstance(args, (tuple, list))
                    and len(args) == 5 and isinstance(args[2], str)
                    and "?" in args[2] and _sensitive_target(args[2])):
                return _sanitize_record(record)
            if _contains_sensitive_target((record.__dict__.get("message"),
                                           record.__dict__.get("request_line"))):
                return False
            try:
                # getMessage performs str(msg) and normal %-formatting without
                # modifying the record. This joins split paths/queries too.
                effective = record.getMessage()
            except Exception:
                # Raw evidence remains important when formatting is malformed.
                # Never diagnose the failure using the record or exception.
                return not raw_sensitive
            # Inspect the completed target, not isolated substitutions: a URL
            # argument may legitimately be only another route's query value.
            return not _text_has_sensitive_query(effective)
        except Exception:
            # Unknown classification or failed sanitization cannot release the
            # original record. Never log the exception through this same logger.
            return False


def install_newsletter_access_log_filter() -> None:
    """Idempotent, including when the module is imported under two app aliases."""
    logger = logging.getLogger("uvicorn.access")
    if not any(getattr(item, "_newsletter_one_click_query_filter", False)
               for item in logger.filters):
        logger.addFilter(NewsletterAccessLogFilter())
