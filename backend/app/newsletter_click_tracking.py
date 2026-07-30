"""Validation for public newsletter click-tracking destinations."""

from ipaddress import ip_address
from urllib.parse import urlsplit


APPROVED_NEWSLETTER_CLICK_HOSTS = frozenset(
    {
        "cheshiretoday.co.uk",
        "www.cheshiretoday.co.uk",
    }
)


class UnsafeNewsletterClickDestination(ValueError):
    """Raised when a tracked newsletter link is not an approved public URL."""


def validate_newsletter_click_destination(destination: object) -> str:
    """Return an approved destination unchanged apart from surrounding whitespace."""
    if not isinstance(destination, str):
        raise UnsafeNewsletterClickDestination("Newsletter destination is invalid.")

    clean_destination = destination.strip()
    if not clean_destination or any(ord(char) <= 32 or ord(char) == 127 for char in clean_destination):
        raise UnsafeNewsletterClickDestination("Newsletter destination is invalid.")
    if "\\" in clean_destination:
        raise UnsafeNewsletterClickDestination("Newsletter destination is invalid.")

    try:
        parsed = urlsplit(clean_destination)
        hostname = parsed.hostname
        port = parsed.port
    except (TypeError, ValueError):
        raise UnsafeNewsletterClickDestination("Newsletter destination is invalid.") from None

    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        raise UnsafeNewsletterClickDestination("Newsletter destination is invalid.")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafeNewsletterClickDestination("Newsletter destination is invalid.")
    if hostname is None:
        raise UnsafeNewsletterClickDestination("Newsletter destination is invalid.")

    normalised_hostname = hostname.rstrip().lower()
    try:
        ip_address(normalised_hostname)
    except ValueError:
        pass
    else:
        raise UnsafeNewsletterClickDestination("Newsletter destination is invalid.")

    if normalised_hostname not in APPROVED_NEWSLETTER_CLICK_HOSTS:
        raise UnsafeNewsletterClickDestination("Newsletter destination is invalid.")

    allowed_port = 443 if parsed.scheme.lower() == "https" else 80
    if port is not None and port != allowed_port:
        raise UnsafeNewsletterClickDestination("Newsletter destination is invalid.")

    return clean_destination
