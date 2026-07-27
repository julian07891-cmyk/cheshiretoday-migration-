import json
import re
from pathlib import Path

from backend import server


FRONTEND_CONTRACT = (
    Path(__file__).resolve().parents[1]
    / "frontend"
    / "src"
    / "constants"
    / "newsletterSignup.js"
)


def test_frontend_and_backend_signup_consent_wording_match_exactly():
    source = FRONTEND_CONTRACT.read_text(encoding="utf-8")
    match = re.search(
        r"NEWSLETTER_SIGNUP_CONSENT\s*=\s*(\"(?:[^\"\\]|\\.)*\")\s*;",
        source,
    )
    assert match, "Frontend consent constant must remain a single JSON string."
    frontend_consent = json.loads(match.group(1))

    assert frontend_consent == server.NEWSLETTER_SIGNUP_CONSENT_TEXT
