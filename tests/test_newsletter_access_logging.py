"""Pinned Uvicorn protocol/formatter tests with an in-memory transport only."""

import asyncio
from io import StringIO
import logging
from pathlib import Path
from urllib.parse import parse_qs, unquote

import pytest
import uvicorn
from uvicorn.logging import AccessFormatter
from uvicorn.protocols.http.h11_impl import H11Protocol
from uvicorn.server import ServerState

from backend.app.newsletter_access_logging import (
    NewsletterAccessLogFilter, install_newsletter_access_log_filter,
)
from backend.app.newsletter_delivery import ONE_CLICK_PATH


@pytest.fixture
def access_output():
    logger = logging.getLogger("uvicorn.access")
    previous = (logger.handlers[:], logger.filters[:], logger.level, logger.propagate, logger.disabled)
    output = StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(AccessFormatter(
        '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
        use_colors=False,
    ))
    logger.handlers = [handler]
    logger.filters = []
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.disabled = False
    install_newsletter_access_log_filter()
    try:
        yield logger, output
    finally:
        logger.handlers, logger.filters, logger.level, logger.propagate, logger.disabled = previous


class MemoryTransport(asyncio.Transport):
    """No socket is created; Uvicorn writes response bytes into this test object."""
    def __init__(self):
        self.data = bytearray()
        self.closed = False
    def get_extra_info(self, name, default=None):
        return {"sockname": ("127.0.0.1", 8000), "peername": ("127.0.0.1", 12345)}.get(name, default)
    def write(self, data):
        self.data.extend(data)
    def close(self):
        self.closed = True
    def is_closing(self):
        return self.closed
    def pause_reading(self):
        pass
    def resume_reading(self):
        pass


@pytest.mark.parametrize("method,target,body,status,raises", [
    ("POST", ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET", b"List-Unsubscribe=One-Click", 200, False),
    ("POST", ONE_CLICK_PATH + "?token=%ZZ&unexpected=SYNTHETIC_SECRET", b"", 401, False),
    ("POST", ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET", b"wrong=body", 400, False),
    ("POST", ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET", b"", 500, True),
    ("GET", ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET", b"", 405, False),
    ("GET", ONE_CLICK_PATH + "/?token=SYNTHETIC_SECRET", b"", 307, False),
    ("GET", "/api/other?query=SYNTHETIC_SECRET", b"", 200, False),
    ("GET", ONE_CLICK_PATH + "-other?query=SYNTHETIC_SECRET", b"", 404, False),
    ("GET", ONE_CLICK_PATH.replace("one-click", "%6Fne-click") + "?token=SYNTHETIC_SECRET", b"", 405, False),
    *[("POST", origin + ONE_CLICK_PATH + suffix, body, status, False)
      for origin in ("https://cheshiretoday.co.uk", "http://synthetic.invalid",
                     "https://www.cheshiretoday.co.uk", "https://CheshireToday.CO.UK",
                     "https://cheshiretoday.co.uk:443", "https://alternate.invalid")
      for suffix, body, status in [
          ("?token=SYNTHETIC_SECRET", b"List-Unsubscribe=One-Click", 200),
          ("/?token=SYNTHETIC_SECRET", b"", 307),
          ("?token=%ZZ&unexpected=SYNTHETIC_SECRET", b"", 401),
          ("?token=SYNTHETIC_SECRET", b"wrong=body", 400),
      ]],
])
def test_real_h11_access_logging_preserves_asgi_request(access_output, method, target, body, status, raises):
    assert uvicorn.__version__ == "0.25.0"  # Matches backend/requirements.txt.
    received = []
    token_service = None
    if target.startswith("https://") and status == 200:
        from backend.app.newsletter_token_service import NewsletterTokenService
        token_service = NewsletterTokenService("D" * 43)
        signed = token_service.issue_direct_unsubscribe_token("123e4567-e89b-42d3-a456-426614174000", 1)
        target = target.replace("SYNTHETIC_SECRET", signed)

    async def app(scope, receive, send):
        received.append((scope["path"], scope["query_string"]))
        assert parse_qs(scope["query_string"].decode()) == parse_qs(target.partition("?")[2])
        if token_service is not None:
            original = parse_qs(scope["query_string"].decode())["token"][0]
            assert token_service.verify_direct_unsubscribe_token(original).token_version == 1
        request = await receive()
        assert request["body"] == body
        if raises:
            raise RuntimeError("synthetic endpoint failure")
        await send({"type": "http.response.start", "status": status, "headers": []})
        await send({"type": "http.response.body", "body": b"done"})

    async def exercise():
        config = uvicorn.Config(app, log_config=None, http="h11", ws="none",
                                lifespan="off", proxy_headers=False)
        state = ServerState()
        protocol = H11Protocol(config, state, {})
        transport = MemoryTransport()
        protocol.connection_made(transport)
        protocol.data_received(
            f"{method} {target} HTTP/1.1\r\nHost: synthetic.invalid\r\nConnection: close\r\nContent-Length: {len(body)}\r\n\r\n".encode()
            + body
        )
        await asyncio.gather(*list(state.tasks))
        protocol.connection_lost(None)
        assert f"HTTP/1.1 {status}".encode() in transport.data

    asyncio.run(exercise())
    assert len(received) == 1
    assert received[0][1] == target.partition("?")[2].encode()
    output = access_output[1].getvalue()
    assert str(status) in output and method in output
    path = unquote(target.partition("?")[0])
    if path.startswith(("https://", "http://")):
        path = "/" + path.split("://", 1)[1].partition("/")[2]
    if path in (ONE_CLICK_PATH, ONE_CLICK_PATH + "/"):
        assert "SYNTHETIC_SECRET" not in output
        assert "?" not in output and "token=" not in output and "%ZZ" not in output
    else:
        assert target in output


def test_idempotent_installation_and_no_global_logging_changes(access_output):
    logger, _ = access_output
    handlers = logger.handlers[:]
    for _ in range(3):
        install_newsletter_access_log_filter()
    # The server uses app.*; tests can use backend.app.*. Neither adds a duplicate.
    import sys
    backend_root = str(Path(__file__).parents[1] / "backend")
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)
    from app.newsletter_access_logging import install_newsletter_access_log_filter as alias_install
    alias_install()
    assert len(logger.filters) == 1
    assert logger.handlers == handlers
    assert logger.level == logging.INFO


def test_filter_leaves_unrelated_shapes_and_clears_cached_message():
    filter_ = NewsletterAccessLogFilter()
    record = logging.LogRecord("uvicorn.access", logging.INFO, "", 1,
                               '%s - "%s %s HTTP/%s" %d',
                               ("local", "POST", ONE_CLICK_PATH + "?token=SECRET", "1.1", 200), None)
    record.message = record.getMessage()
    assert filter_.filter(record)
    assert "SECRET" not in record.message + record.getMessage()
    for name, args in [("other", (1, 2, 3, 4, 5)), ("uvicorn.access", (1, 2))]:
        record = logging.LogRecord(name, logging.INFO, "", 1, "message", args, None)
        before = record.__dict__.copy()
        assert filter_.filter(record)
        assert record.__dict__ == before


def test_server_installs_filter_at_import_before_app_creation():
    import ast
    source = (Path(__file__).parents[1] / "backend/server.py").read_text()
    tree = ast.parse(source)
    calls = [node for node in tree.body if isinstance(node, ast.Expr)
             and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
             and node.value.func.id == "install_newsletter_access_log_filter"]
    assert len(calls) == 1
    assert calls[0].lineno < next(node.lineno for node in tree.body
                                if isinstance(node, ast.Assign)
                                and any(isinstance(t, ast.Name) and t.id == "app" for t in node.targets))


@pytest.mark.parametrize("shape", ["preformatted", "short", "list", "mapping", "missing", "target_type", "bytes", "format", "cached", "exception_cache"])
def test_sensitive_unexpected_records_never_emit_query(shape):
    target = ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET&other=PRIVATE"
    record = logging.LogRecord("uvicorn.access", 20, "", 1,
                               '%s - "%s %s HTTP/%s" %d',
                               ("local", "POST", target, "1.1", 200), None)
    if shape == "preformatted":
        record.msg, record.args = record.getMessage(), ()
    elif shape == "short":
        record.args = (target,)
    elif shape == "list":
        record.args = list(record.args)
    elif shape == "mapping":
        record.args = {"target": target}
    elif shape == "missing":
        record.msg, record.args = target, None
    elif shape == "target_type":
        record.args = ("local", "POST", {"target": target}, "1.1", 200)
    elif shape == "bytes":
        record.args = ("local", "POST", target.encode(), "1.1", 200)
    elif shape == "exception_cache":
        record.exc_text = "SYNTHETIC_SECRET"
    elif shape == "format":
        record.msg = "%s %s %s %s %d %s"
    else:
        record.args = ()
        record.msg = "cached record"
        record.message = target
    allowed = NewsletterAccessLogFilter().filter(record)
    assert allowed is (shape == "list")
    output = logging.Formatter().format(record) if allowed else ""
    assert "SYNTHETIC_SECRET" not in output and "PRIVATE" not in output


@pytest.mark.parametrize("target", [
    "/foo" + ONE_CLICK_PATH + "?token=KEEP",
    ONE_CLICK_PATH + "-other?token=KEEP",
    "/?next=" + ONE_CLICK_PATH + "?token=KEEP",
    "https://synthetic.invalid/other?token=KEEP",
    "https://synthetic.invalid/?next=" + ONE_CLICK_PATH + "?token=KEEP",
])
def test_lookalikes_and_unrelated_absolute_records_unchanged(target):
    for args in [(), (1, 2), [1, 2]]:
        record = logging.LogRecord("uvicorn.access", 20, "", 1, target, (), None)
        record.args = args
        before = record.__dict__.copy()
        assert NewsletterAccessLogFilter().filter(record)
        assert record.__dict__ == before


def test_sanitizer_failure_suppresses_sensitive_only(monkeypatch):
    from backend.app import newsletter_access_logging as module
    def fail(record):
        raise RuntimeError("SYNTHETIC_SECRET")
    monkeypatch.setattr(module, "_sanitize_record", fail)
    sensitive = logging.LogRecord("uvicorn.access", 20, "", 1,
                                  '%s - "%s %s HTTP/%s" %d',
                                  ("local", "POST", ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET", "1.1", 200), None)
    assert not module.NewsletterAccessLogFilter().filter(sensitive)
    unrelated = logging.LogRecord("uvicorn.access", 20, "", 1, "/other?q=KEEP", (), None)
    assert module.NewsletterAccessLogFilter().filter(unrelated)


def test_h11_protocol_rejection_does_not_emit_target(access_output, caplog):
    async def app(scope, receive, send):
        pytest.fail("Malformed protocol must not reach ASGI")
    async def exercise():
        config = uvicorn.Config(app, log_config=None, http="h11", ws="none",
                                lifespan="off", proxy_headers=False)
        protocol = H11Protocol(config, ServerState(), {})
        transport = MemoryTransport()
        protocol.connection_made(transport)
        protocol.data_received(
            ("POST https://cheshiretoday.co.uk" + ONE_CLICK_PATH +
             "?token=SYNTHETIC_SECRET HTTP/1.1\r\nHost: synthetic.invalid\r\n"
             "Content-Length: invalid\r\n\r\n").encode()
        )
        assert b"400 Bad Request" in transport.data
        protocol.connection_lost(None)
    asyncio.run(exercise())
    assert "SYNTHETIC_SECRET" not in access_output[1].getvalue() + caplog.text


@pytest.fixture
def two_handler_output(access_output):
    logger, first = access_output
    logger.handlers[0].setFormatter(logging.Formatter("%(message)s"))
    second = StringIO()
    handler = logging.StreamHandler(second)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return logger, (first, second)


@pytest.mark.parametrize("layout", [
    "request_target={target}", 'request_target="{target}"',
    "target=({target})", "({target})", "POST {target} HTTP/1.1",
    "target:{target}", "target=[{target}]", "target=<{target}>",
    "target='{target}'", '{{"request_target":"{target}"}}',
])
@pytest.mark.parametrize("origin", ["", "https://CheshireToday.CO.UK:443"])
@pytest.mark.parametrize("query", ["?token=SYNTHETIC_SECRET&unknown=%ZZ", ""])
def test_alternate_preformatted_targets_through_handlers(two_handler_output, layout, origin, query):
    logger, outputs = two_handler_output
    text = layout.format(target=origin + ONE_CLICK_PATH + query)
    record = logging.LogRecord(logger.name, 20, "", 1, text, (), None)
    before = record.__dict__.copy()
    assert NewsletterAccessLogFilter().filter(record) is (not query)
    assert record.__dict__ == before  # Inspection itself never mutates.
    logger.handle(record)
    for output in outputs:
        assert output.getvalue() == ("" if query else text + "\n")
        assert "SYNTHETIC_SECRET" not in output.getvalue()


@pytest.mark.parametrize("msg,args", [
    ("request_target=%s", (ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET",)),
    ("request_target=%s", ("https://alternate.invalid" + ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET",)),
    ("target=(/api/newsletter/%s?token=%s)", ("unsubscribe/one-click", "SYNTHETIC_SECRET")),
    ("POST %s%s%s HTTP/1.1", ("/api/newsletter/unsubscribe/", "one-click", "?unknown=SYNTHETIC_SECRET")),
    ("target=https://%s/api/newsletter/unsubscribe/%s?token=%s", ("alternate.invalid", "one-click", "SYNTHETIC_SECRET")),
    ("target=%(path)s?token=%(token)s", {"path": ONE_CLICK_PATH, "token": "SYNTHETIC_SECRET"}),
    ("target=/api/newsletter/unsubscribe/%(tail)s", {"tail": "one-click?token=SYNTHETIC_SECRET"}),
    ("%s", ( (ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET").encode(),)),
    ("target=%s", ((ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET").encode(),)),
    ("target=%r", (ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET",)),
    (("request_target=" + ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET").encode(), ()),
    ([ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET"], ()),
])
def test_effective_message_sensitive_targets_suppressed(two_handler_output, msg, args):
    logger, outputs = two_handler_output
    record = logging.LogRecord(logger.name, 20, "", 1, msg, (), None)
    record.args = args
    assert "SYNTHETIC_SECRET" in record.getMessage()
    before = record.__dict__.copy()
    assert not NewsletterAccessLogFilter().filter(record)
    assert record.__dict__ == before
    logger.handle(record)
    assert all(output.getvalue() == "" for output in outputs)


@pytest.mark.parametrize("target", [
    "/foo?next=" + ONE_CLICK_PATH + "?token=KEEP",
    "/foo?next=%2Fapi%2Fnewsletter%2Funsubscribe%2Fone-click%3Ftoken%3DKEEP",
    "/foo" + ONE_CLICK_PATH + "?token=KEEP",
    ONE_CLICK_PATH + "-other?token=KEEP", ONE_CLICK_PATH + "ed?token=KEEP",
    "https://alternate.invalid/foo?next=" + ONE_CLICK_PATH + "?token=KEEP",
    ONE_CLICK_PATH, ONE_CLICK_PATH + "/",
])
@pytest.mark.parametrize("layout", ["request_target=%s", "target=(%s)"])
def test_unrelated_effective_targets_preserved(two_handler_output, target, layout):
    logger, outputs = two_handler_output
    record = logging.LogRecord(logger.name, 20, "", 1, layout, (target,), None)
    before = record.__dict__.copy()
    assert NewsletterAccessLogFilter().filter(record)
    assert record.__dict__ == before
    logger.handle(record)
    assert all(output.getvalue() == layout % target + "\n" for output in outputs)


def test_sensitive_argument_used_only_in_unrelated_query_is_preserved(two_handler_output):
    logger, outputs = two_handler_output
    target = ONE_CLICK_PATH + "?token=KEEP"
    logger.info("request_target=(/foo?next=%s)", target)
    assert all(output.getvalue() == "request_target=(/foo?next=" + target + ")\n" for output in outputs)


@pytest.mark.parametrize("msg,args", [
    ("target=%s %s", (ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET",)),
    ("target=%d", (ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET",)),
    ("target=%(missing)s", {"path": ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET"}),
    ("target=" + ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET %", (1,)),
])
def test_malformed_sensitive_formats_suppressed(two_handler_output, msg, args):
    logger, outputs = two_handler_output
    record = logging.LogRecord(logger.name, 20, "", 1, msg, (), None)
    record.args = args
    with pytest.raises((TypeError, ValueError, KeyError)):
        record.getMessage()
    before = record.__dict__.copy()
    assert not NewsletterAccessLogFilter().filter(record)
    assert record.__dict__ == before
    logger.handle(record)
    assert all(output.getvalue() == "" for output in outputs)


@pytest.mark.parametrize("msg,args", [("%s %s", ("/other",)), ("%d", ("/other",)), (42, (1,))])
def test_unrelated_malformed_formats_unchanged(msg, args):
    record = logging.LogRecord("uvicorn.access", 20, "", 1, msg, args, None)
    before = record.__dict__.copy()
    assert NewsletterAccessLogFilter().filter(record)
    assert record.__dict__ == before


@pytest.mark.parametrize("fail_sanitizer", [False, True])
def test_standard_sensitive_record_two_handlers(two_handler_output, monkeypatch, fail_sanitizer):
    from backend.app import newsletter_access_logging as module
    logger, outputs = two_handler_output
    if fail_sanitizer:
        def fail(record):
            raise RuntimeError("SYNTHETIC_SECRET")
        monkeypatch.setattr(module, "_sanitize_record", fail)
    logger.info('%s - "%s %s HTTP/%s" %d', "local", "POST",
                ONE_CLICK_PATH + "?token=SYNTHETIC_SECRET&unknown=%ZZ", "1.1", 200)
    for output in outputs:
        assert output.getvalue() == ("" if fail_sanitizer else
            'local - "POST ' + ONE_CLICK_PATH + ' HTTP/1.1" 200\n')
        assert "SYNTHETIC_SECRET" not in output.getvalue()
