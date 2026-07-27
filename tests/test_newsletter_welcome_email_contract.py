from backend.app.email_service import EmailService


def test_welcome_email_confirms_immediate_all_three_subscription(monkeypatch):
    service = EmailService()
    captured = {}

    def capture(to_email, subject, html_content, text_content=None):
        captured.update(
            to_email=to_email,
            subject=subject,
            html=html_content,
            text=text_content,
        )
        return True

    monkeypatch.setattr(service, "_send_email", capture)

    assert service.send_welcome_email("reader@example.com") is True
    combined = f"{captured['html']}\n{captured['text']}"
    assert "The Daily Brief" in combined
    assert "Monday to Saturday" in combined
    assert "The Weekly Roundup" in combined
    assert "on Sunday" in combined
    assert "Breaking News Alerts" in combined
    assert "Rare alerts for major incidents" in combined
    assert "active now" in combined
    assert "No confirmation click is required" in combined
    assert "tomorrow" not in combined.lower()
    assert "/newsletter/preferences" in captured["html"]
    assert "/unsubscribe" in captured["html"]
