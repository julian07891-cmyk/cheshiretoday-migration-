"""Immutable approved asset locations and checksums for social composition."""

from pathlib import Path
from typing import Final


_REPOSITORY_ROOT: Final[Path] = Path(__file__).resolve().parents[2]

MASTER_SVG_PATH: Final[Path] = (
    _REPOSITORY_ROOT
    / "docs/brand-assets/social/facebook/templates/local-news-facebook.svg"
)
APPROVED_LOGO_PATH: Final[Path] = (
    _REPOSITORY_ROOT / "frontend/public/cheshire-today-email-logo.png"
)

APPROVED_MASTER_SHA256: Final[str] = (
    "c18d61bef5844703235643d1007454920f8cdf17a2d96ed3814cefebcc196994"
)
APPROVED_LOGO_SHA256: Final[str] = (
    "62ac198ca449ee4b6fb09ba2019153b0f8281320f39c4114a45a76278cc6d348"
)
