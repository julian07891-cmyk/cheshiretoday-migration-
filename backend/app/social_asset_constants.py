"""Immutable approved asset locations and checksums for social composition."""

from pathlib import Path
from types import MappingProxyType
from typing import Final


_REPOSITORY_ROOT: Final[Path] = Path(__file__).resolve().parents[2]

MASTER_SVG_PATH: Final[Path] = (
    _REPOSITORY_ROOT
    / "docs/brand-assets/social/facebook/templates/local-news-facebook.svg"
)
NEWSLETTER_MASTER_SVG_PATH: Final[Path] = (
    _REPOSITORY_ROOT
    / "docs/brand-assets/social/facebook/templates/newsletter-facebook.svg"
)
APPROVED_LOGO_PATH: Final[Path] = (
    _REPOSITORY_ROOT / "frontend/public/cheshire-today-email-logo.png"
)

APPROVED_MASTER_SHA256: Final[str] = (
    "c18d61bef5844703235643d1007454920f8cdf17a2d96ed3814cefebcc196994"
)
APPROVED_NEWSLETTER_MASTER_SHA256: Final[str] = (
    "9fe17491b56314ccb7aa00f3d0dae92417838717af03319760b05e20298b3b5e"
)
APPROVED_LOGO_SHA256: Final[str] = (
    "62ac198ca449ee4b6fb09ba2019153b0f8281320f39c4114a45a76278cc6d348"
)

FACEBOOK_GRAPHIC_MASTERS: Final = MappingProxyType({
    name: (
        _REPOSITORY_ROOT
        / f"docs/brand-assets/social/facebook/templates/{filename}-facebook.svg",
        checksum,
    )
    for name, filename, checksum in (
        ("business", "business", "ed457cd294ca8e6f3750783c79b36dc45e42608f03ea592b02863e6b09257d3c"),
        ("property", "property", "67d0bd6ef2efad3595c10c5856b1504d7d3ca28d3e76acdcc3bd36dae1a46096"),
        ("ai-tech", "ai-tech", "8d1b7886c1e599cda84616b6bba5cf873409a80b7815307a15296a30aea1c748"),
        ("breaking-news", "breaking-news", "776cace37bc6adf2e3c22d6f9d2814b49ca3bb04c037c34db0996db561c03afe"),
        ("event", "event", "c8f185bfd514ccacafabf08daa73d901c57434afdea4d67771b741d2712e691a"),
        ("quote", "quote", "8c626ee7b14959af5f4477b6417d5165ab28f528ef36945195053aa9ba8c2b08"),
        ("poll", "poll", "d3afae2f31d709d35da04715de1006628710636a00a4c63fc36b2e332d07c566"),
    )
})

INSTAGRAM_GRAPHIC_MASTERS: Final = MappingProxyType({
    ("story", "top-story"): (
        _REPOSITORY_ROOT
        / "docs/brand-assets/social/stories/templates/top-story.svg",
        "4f2a807f1b3d6e6ca747d7c81706e8c976962466003a5b989f07b3bb3be00685",
    ),
})
INSTAGRAM_GRAPHIC_FORMATS: Final = frozenset(INSTAGRAM_GRAPHIC_MASTERS)
