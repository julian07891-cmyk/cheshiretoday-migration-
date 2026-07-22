from html.parser import HTMLParser
from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.email_service import EmailService


class _BalancedHTMLParser(HTMLParser):
    _VOID_ELEMENTS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in self._VOID_ELEMENTS:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        return

    def handle_endtag(self, tag):
        if not self.stack:
            self.errors.append(f"unexpected closing tag: {tag}")
            return
        opened = self.stack.pop()
        if opened != tag:
            self.errors.append(f"closed {tag} while {opened} was open")


def _assert_balanced_html(rendered_html):
    parser = _BalancedHTMLParser()
    parser.feed(rendered_html)
    parser.close()
    assert parser.errors == []
    assert parser.stack == []


def _capture_single_email(monkeypatch, service, method_name, *args, **kwargs):
    captured = []

    def capture_email(to_email, subject, html_content, text_content=None):
        captured.append(
            {
                "to": to_email,
                "subject": subject,
                "html": html_content,
                "text": text_content,
            }
        )
        return True

    def capture_batch(messages):
        captured.extend(messages)
        return len(messages)

    monkeypatch.setattr(service, "_send_email", capture_email)
    monkeypatch.setattr(service, "_send_resend_batch", capture_batch)

    count, _ = getattr(service, method_name)(*args, **kwargs)
    assert count == 1
    assert len(captured) == 1
    return captured[0]


def test_daily_brief_renders_balanced_html_and_escapes_dynamic_content(monkeypatch):
    service = EmailService()
    articles = [
        {
            "id": "hero-1",
            "title": '<script>alert("hero")</script> & Cheshire',
            "content": '<b>unsafe hero summary</b> & detail',
            "image": 'https://images.example.com/hero.jpg" onerror="alert(1)',
            "category": "Local",
        },
        {"id": "local-1", "title": "Chester <strong>update</strong>", "category": "Local"},
        {"id": "business-1", "title": "Business & finance", "category": "Business"},
        {"id": "tech-1", "title": "OpenAI <news>", "category": "Technology"},
        {"id": "other-1", "title": "National > local", "category": "UK"},
    ]

    message = _capture_single_email(
        monkeypatch,
        service,
        "send_daily_brief",
        ["reader@example.com"],
        articles,
        weather={"temp": "8<9", "condition": "Cloud & sun", "location": "Chester <city>"},
        travel={"m6_status": "Clear <today>", "rail_status": "Normal & punctual"},
        photo_of_day={
            "image_url": 'https://images.example.com/photo.jpg" onerror="alert(2)',
            "caption": "The Dee <at dusk>",
            "credit": "Reader & guest",
        },
    )

    rendered = message["html"]
    _assert_balanced_html(rendered)
    assert "<script>" not in rendered
    assert "<strong>update</strong>" not in rendered
    assert ' onerror="alert(' not in rendered
    assert "&lt;script&gt;alert(\"hero\")&lt;/script&gt; &amp; Cheshire" in rendered
    assert "&lt;b&gt;unsafe hero summary&lt;/b&gt; &amp; detail" in rendered
    assert "hero.jpg&quot; onerror=&quot;alert(1)" in rendered
    assert "The Dee &lt;at dusk&gt;" in rendered
    assert "Reader &amp; guest" in rendered
    assert "/api/email/track/open/" in rendered
    assert "https://cheshiretoday.co.uk/newsletter/preferences" in rendered
    assert "https://cheshiretoday.co.uk/unsubscribe" in rendered


def test_weekly_roundup_uses_verified_text_masthead_and_balanced_html(monkeypatch):
    service = EmailService()
    message = _capture_single_email(
        monkeypatch,
        service,
        "send_weekly_roundup",
        ["reader@example.com"],
        {
            "id": "big-1",
            "title": "Big <Read> & analysis",
            "content": '<script>alert("summary")</script> This week in Cheshire.',
            "image": 'https://images.example.com/big.jpg" onerror="alert(3)',
        },
        [{"id": "icymi-1", "title": "ICYMI <unsafe> & useful"}],
        property_of_week={
            "title": "Home <script>",
            "price": "£250,000 & offers",
            "location": "Chester <centre>",
            "image_url": 'https://images.example.com/home.jpg" onerror="alert(4)',
            "url": 'https://property.example.com/home?x=1&y=2" onclick="alert(5)',
        },
        food_review={
            "title": "Cafe <Review>",
            "venue": "Cafe & Kitchen",
            "rating": 4,
            "image_url": 'https://images.example.com/food.jpg" onerror="alert(6)',
            "url": 'https://food.example.com/review?x=1&y=2" onclick="alert(7)',
        },
    )

    rendered = message["html"]
    _assert_balanced_html(rendered)
    assert "CHESHIRE TODAY" in rendered
    assert "logo-white.png" not in rendered
    assert ' onerror="' not in rendered
    assert "<script>" not in rendered
    assert "Big &lt;Read&gt; &amp; analysis" in rendered
    assert "&lt;script&gt;alert(\"summary\")&lt;/script&gt;" in rendered
    assert "ICYMI &lt;unsafe&gt; &amp; useful" in rendered
    assert "Home &lt;script&gt;" in rendered
    assert "Cafe &lt;Review&gt;" in rendered
    assert "&quot; onclick=&quot;alert(" in rendered
    assert "/api/email/track/open/" in rendered


def test_digest_rendering_is_offline_and_preserves_send_contract(monkeypatch):
    service = EmailService()
    provider_calls = []

    def capture_batch(messages):
        provider_calls.append(messages)
        return len(messages)

    monkeypatch.setattr(service, "_send_resend_batch", capture_batch)
    service.resend_enabled = True

    count, tracking_id = service.send_weekly_roundup(
        ["reader@example.com"],
        {"id": "big-1", "title": "A verified weekly story", "content": "Summary"},
        [],
    )

    assert count == 1
    assert tracking_id
    assert len(provider_calls) == 1
    assert len(provider_calls[0]) == 1
    assert provider_calls[0][0]["to"] == "reader@example.com"
    assert provider_calls[0][0]["subject"].startswith("📰 The Weekly Roundup")
