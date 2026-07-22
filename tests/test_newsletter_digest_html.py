from html.parser import HTMLParser
from pathlib import Path
import struct
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.email_service import EmailService, _email_story_excerpt


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
        {"id": "local-1", "title": "Chester <strong>update</strong>", "content": "A concise local update. More detail follows.", "category": "Local"},
        {"id": "business-1", "title": "Business & finance", "content": "Markets moved in early trading.", "category": "Business"},
        {"id": "tech-1", "title": "OpenAI <news>", "content": "A technology briefing for Cheshire firms.", "category": "Technology"},
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
    assert "A concise local update." in rendered
    assert 'data-email-cta="primary" href="https://cheshiretoday.co.uk/api/email/track/click/' in rendered


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


def test_digest_identity_preheaders_and_logo_asset_are_shared(monkeypatch):
    service = EmailService()
    daily = _capture_single_email(
        monkeypatch,
        service,
        "send_daily_brief",
        ["reader@example.com"],
        [
            {"id": "daily-1", "title": "Daily lead", "content": "Daily summary", "category": "Local"},
            {"id": "tech-1", "title": "Tech brief", "content": "Technology update", "category": "Technology"},
        ],
    )
    weekly = _capture_single_email(
        monkeypatch,
        service,
        "send_weekly_roundup",
        ["reader@example.com"],
        {"id": "weekly-1", "title": "Weekly lead", "content": "Weekly summary"},
        [],
    )

    for message in (daily, weekly):
        rendered = message["html"]
        assert 'data-email-shell="cheshire-today"' in rendered
        assert 'data-email-masthead="cheshire-today"' in rendered
        assert 'data-email-footer="cheshire-today"' in rendered
        assert 'src="https://cheshiretoday.co.uk/cheshire-today-email-logo.png"' in rendered
        assert 'width="150" height="51" alt="Cheshire Today"' in rendered
        assert 'font-size:23px;font-weight:700;line-height:27px;' in rendered
        assert "font-family:Georgia,'Times New Roman',serif;font-size:22px;line-height:28px;font-weight:700;" in rendered
        assert "logo-white.png" not in rendered
        assert "Local · Business · Finance" in rendered
        assert "https://cheshiretoday.co.uk/newsletter/preferences" in rendered
        assert "https://cheshiretoday.co.uk/unsubscribe" in rendered

    assert "Today's top Cheshire stories, business updates and market intelligence." in daily["html"]
    assert "The biggest Cheshire stories, business updates and ideas from the week." in weekly["html"]
    assert "display:none;max-height:0;overflow:hidden" in daily["html"]
    assert "display:none;max-height:0;overflow:hidden" in weekly["html"]


def test_weekly_icymi_excerpts_are_escaped_tracked_and_keep_order(monkeypatch):
    service = EmailService()
    icymi_articles = [
        {
            "id": f"icymi-{index}",
            "title": f"ICYMI story {index}",
            "content": f"Weekly <strong>excerpt {index}</strong>. Additional detail.",
        }
        for index in range(1, 7)
    ]
    message = _capture_single_email(
        monkeypatch,
        service,
        "send_weekly_roundup",
        ["reader@example.com"],
        {"id": "weekly-lead", "title": "Weekly lead", "content": "Lead summary"},
        icymi_articles,
    )

    rendered = message["html"]
    positions = [rendered.index(f"ICYMI story {index}") for index in range(1, 6)]
    assert positions == sorted(positions)
    assert "ICYMI story 6" not in rendered
    for index in range(1, 6):
        assert f"Weekly &lt;strong&gt;excerpt {index}&lt;/strong&gt;." in rendered
        story_position = rendered.index(f"ICYMI story {index}")
        assert "/api/email/track/click/" in rendered[max(0, story_position - 500):story_position]

    assert "Weekly <strong>excerpt 1</strong>." not in rendered
    assert "Weekly <strong>excerpt 1</strong>." not in message["text"]
    assert "ICYMI story 5" in message["text"]
    assert "ICYMI story 6" not in message["text"]


def test_story_excerpts_truncate_at_complete_words_with_one_clean_ellipsis():
    assert _email_story_excerpt({"summary": "Alpha beta gamma delta"}, limit=12) == "Alpha beta…"
    assert _email_story_excerpt({"summary": "Alpha beta… gamma delta"}, limit=11) == "Alpha beta…"
    assert _email_story_excerpt({"summary": "Alpha beta; gamma delta"}, limit=11) == "Alpha beta…"
    assert _email_story_excerpt({"summary": "Extraordinarilylongfirsttoken second"}, limit=10) == "Extraordinarilylongfirsttoken…"

    natural = "A concise sentence ends naturally."
    assert _email_story_excerpt({"summary": natural}) == natural


def test_phase_4b_cta_and_daily_secondary_contracts_are_unchanged(monkeypatch):
    service = EmailService()
    daily = _capture_single_email(
        monkeypatch,
        service,
        "send_daily_brief",
        ["reader@example.com"],
        [
            {"id": "daily-lead", "title": "Daily lead", "content": "Lead summary", "category": "Local"},
            {"id": "daily-local", "title": "Daily secondary", "content": "Secondary excerpt. More detail.", "category": "Local"},
            {"id": "daily-tech", "title": "Technology secondary", "content": "Technology excerpt.", "category": "Technology"},
        ],
    )
    weekly = _capture_single_email(
        monkeypatch,
        service,
        "send_weekly_roundup",
        ["reader@example.com"],
        {"id": "weekly-lead", "title": "Weekly lead", "content": "Weekly summary"},
        [],
    )

    cta_style = (
        'data-email-cta="primary" href="https://cheshiretoday.co.uk/api/email/track/click/'
    )
    assert cta_style in daily["html"]
    assert cta_style in weekly["html"]
    assert "Read the full story →" in daily["html"]
    assert "Read the full story →" in weekly["html"]
    assert "Daily secondary" in daily["html"]
    assert "Secondary excerpt." in daily["html"]
    assert "https://cheshiretoday.co.uk/article/daily-local/daily-secondary" in daily["text"]


def test_email_logo_asset_has_verified_dimensions_and_modest_size():
    logo_path = Path(__file__).resolve().parents[1] / "frontend/public/cheshire-today-email-logo.png"
    image = logo_path.read_bytes()
    assert image[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", image[16:24]) == (360, 122)
    assert len(image) < 100_000


def test_daily_and_weekly_plain_text_use_clean_canonical_links(monkeypatch):
    service = EmailService()
    daily = _capture_single_email(
        monkeypatch,
        service,
        "send_daily_brief",
        ["reader@example.com"],
        [
            {"id": "daily-1", "title": "Daily lead", "content": "Daily summary", "category": "Local"},
            {"id": "tech-1", "title": "Tech brief", "content": "Technology update", "category": "Technology"},
        ],
    )
    weekly = _capture_single_email(
        monkeypatch,
        service,
        "send_weekly_roundup",
        ["reader@example.com"],
        {"id": "weekly-1", "title": "Weekly lead", "content": "Weekly summary"},
        [{"id": "weekly-2", "title": "Another weekly story"}],
    )

    assert "https://cheshiretoday.co.uk/article/daily-1/daily-lead" in daily["text"]
    assert "https://cheshiretoday.co.uk/article/tech-1/tech-brief" in daily["text"]
    assert "https://cheshiretoday.co.uk/article/weekly-1/weekly-lead" in weekly["text"]
    assert "https://cheshiretoday.co.uk/article/weekly-2/another-weekly-story" in weekly["text"]
    for message in (daily, weekly):
        assert message["text"]
        assert "/api/email/track/" not in message["text"]
        assert "Manage preferences: https://cheshiretoday.co.uk/newsletter/preferences" in message["text"]
        assert "Unsubscribe: https://cheshiretoday.co.uk/unsubscribe" in message["text"]
        assert "reader@example.com" not in message["text"]


def test_admin_weekly_control_reuses_existing_authenticated_endpoint():
    repository = Path(__file__).resolve().parents[1]
    admin_source = (repository / "frontend/src/components/AdminDashboard.jsx").read_text()
    server_source = (repository / "backend/server.py").read_text()

    assert 'data-testid="send-test-weekly-roundup-button"' in admin_source
    assert "/api/send-weekly-roundup-test?test_email=${encodeURIComponent(testEmail)}" in admin_source
    assert 'method: \'POST\'' in admin_source
    assert "getAuthHeaders()" in admin_source
    assert '@api_router.post("/send-weekly-roundup-test")' in server_source
    assert admin_source.count("/api/send-weekly-roundup-test?") == 1


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
