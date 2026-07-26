"""Pure deterministic Local RSS editorial classification helpers.

This module deliberately has no database, application, network, route, model,
or scheduler dependency. Production importing and read-only shadow evaluation
share these helpers so their pre-rewrite classification policy cannot drift.
"""

from __future__ import annotations

import re


_CRIME_RE = re.compile(
    r"(cops?|police|officer|mugshot|murder(?:s)?|kill(?:ed|s)?|manslaughter|"
    r"homicide|stab(?:bing|bed|s)?|shoot(?:ing|s)?|firearm(?:s)?|gunman|"
    r"rape(?:d)?|sexual assault|sex(?:ual)? offence|indecent|pervert|predator|"
    r"groom(?:ed|ing)?|paedophile|pedophile|child\s+sex|online\s+predator|"
    r"cctv\s+appeal|stolen|theft|shoplift(?:ing|ed)?|\bassault(?:ed|s)?\b|"
    r"\battack(?:ed|s)?\b|robber(?:y|ies)|burglar(?:y|ies)|arson|charged|"
    r"arrest(?:ed)?|raid|drug raid|cannabis plants?|prosecut(?:ed|ion)|trial|"
    r"guilty|sentenc(?:ed|ing)|jailed|jail|prison|convict(?:ed|ion)|"
    r"inquest(?:s)?)",
    re.I,
)
_OBITUARY_RE = re.compile(
    r"(death notices?|funeral notices?|funeral arrangements|in memoriam|"
    r"death announcements?|passed away peacefully|loving memory|"
    r"beloved husband|beloved wife|beloved mum|beloved mom|beloved dad|"
    r"family announcement)",
    re.I,
)
_LOW_UTILITY_RE = re.compile(
    r"\b(celebrity|showbiz|reality\s*tv|love island|netflix|movie|film|album|"
    r"concert|music\s*video|book\s*launch|novel|brit awards|baftas|"
    r"royal fashion|gift guide|black friday|cyber monday|shopping deal|"
    r"must-have buys?|restaurant review|afternoon tea|food\s+festival|"
    r"arts\s+festival|music\s+festival|traffic\s+updates?|live\s+updates?|"
    r"rush[-\s]?hour\s+gridlock|gridlock|breakdowns?|crash\s+shuts?|"
    r"road\s+closed|road\s+closure|recap:|best\s+places\s+to\s+live|"
    r"market\s+town\s+named|charming\s+cottage|dream\s+home|period\s+home|"
    r"house\s+for\s+sale|farmhouse\s+for\s+sale|stunning\s+home|"
    r"property\s+of\s+the\s+week|inside\s+this\s+home|listed\s+for\s+sale)\b",
    re.I,
)
_PROMOTIONAL_RE = re.compile(
    r"\b(sponsored|advertorial|promotion|shopping\s+deal|gift\s+guide|"
    r"review|best\s+(?:shops?|restaurants?|attractions?))\b",
    re.I,
)
_ROUTINE_FIRE_RE = re.compile(
    r"\b(?:kitchen|shed|garage|bin|small)\s+(?:fire|blaze)\b|"
    r"\broutine\s+(?:house\s+)?(?:fire|blaze)\b",
    re.I,
)
_FIRE_PUBLIC_IMPACT_RE = re.compile(
    r"\b(?:major|serious|fatal|evacuat(?:e|ed|ion)|hospital|injur(?:y|ed|ies)|"
    r"school|care\s+home|industrial|factory|wildfire|public\s+safety)\b",
    re.I,
)
_LOW_VALUE_FEATURE_RE = re.compile(
    r"\bbest\s+(?:restaurants?|picnic\s+(?:places?|spots?))\b|"
    r"\btripadvisor\b|\b(?:caf[eé]|restaurant)\s+review\b|"
    r"\breview\s+of\s+(?:a|the)\s+(?:local\s+)?caf[eé]\b|"
    r"\b(?:house|home|cottage|farmhouse|property)\s+for\s+sale\b|"
    r"\bproperty\s+of\s+the\s+week\b",
    re.I,
)
_ROUTINE_ROAD_CLOSURE_RE = re.compile(
    r"\b(?:road\s+clos(?:ed|ure)|lane\s+closure)\b",
    re.I,
)
_SIGNIFICANT_TRANSPORT_IMPACT_RE = re.compile(
    r"\b(?:major|significant|severe|emergency|multi-day|weeks?|overnight|"
    r"utility\s+works?|infrastructure|diversion|disruption|motorway|"
    r"bridge|rail|bus)\b",
    re.I,
)
_MATERIAL_CHANGE_RE = re.compile(
    r"\b(new|open(?:s|ed|ing)?|reopen(?:s|ed|ing)?|investment|invests?|"
    r"major\s+refurbishment|refurbish(?:es|ed|ment)?|redevelopment|"
    r"regeneration|expansion|expand(?:s|ed|ing)?|upgrade(?:s|d)?|"
    r"improvement(?:s)?|funding|jobs?)\b",
    re.I,
)
_HIGH_VALUE_SECTOR_RE = re.compile(
    r"\b(supermarket|store|retail|restaurant|hotel|pub|hospitality|park|"
    r"attraction|tourism|visitor|heritage|leisure\s+centre)\b",
    re.I,
)
_USEFUL_LOCAL_RE = re.compile(
    r"\b(planning|application|approved|refused|development|homes?|housing|"
    r"green\s+belt|brownfield|affordable\s+homes?|council|councillors?|"
    r"committee|consultation|public\s+meeting|local\s+plan|regeneration|"
    r"town\s+centre|high\s+street|business|jobs?|employer|investment|funding|"
    r"grant|factory|warehouse|retail|startup|expansion|"
    r"relocat(?:e|es|ed|ion)|school|academy|college|ofsted|education|pupils?|"
    r"students?|nhs|hospital|gp|health|care\s+home|social\s+care|energy|"
    r"bills?|water|transport|rail|bus|roadworks?|infrastructure|tax|rent|"
    r"mortgage|landlord|tenant|cost\s+of\s+living|economy|economic|charity|"
    r"community\s+fund|inequality|public\s+interest)\b",
    re.I,
)
_REASON_PATTERNS = (
    ("Community feature", r"\b(community|charity|volunteer|neighbourhood|fundraiser)\b"),
    ("Human-interest", r"\b(human[-\s]?interest|resident|family|personal\s+story)\b"),
    ("Lifestyle", r"\b(lifestyle|best\s+places?|food|drink|restaurant\s+review|afternoon\s+tea)\b"),
    ("Entertainment", r"\b(entertainment|concert|festival|theatre|cinema|music|show)\b"),
    ("Tourism", r"\b(tourism|tourist|visitor)\b"),
    ("Local attraction", r"\b(attraction|park|heritage|museum|zoo)\b"),
    ("Hospitality", r"\b(restaurant|hotel|pub|hospitality)\b"),
    ("Retail feature", r"\b(retail|supermarket|store|shop)\b"),
)


def local_editorial_text(article: dict) -> str:
    tags = article.get("tags") or []
    if not isinstance(tags, (list, tuple, set)):
        tags = [tags]
    return " ".join(
        [
            str(article.get("category") or ""),
            " ".join(str(tag) for tag in tags),
            str(article.get("title") or ""),
            str(article.get("summary") or ""),
            str(article.get("content") or ""),
        ]
    ).lower()


def is_crime_like(article: dict) -> bool:
    category = str(article.get("category") or "").lower()
    title = str(article.get("title") or "").lower()
    source_url = str(article.get("source_url") or "").lower()
    if "/audio/" in source_url or "podcast" in title:
        return False
    if "court" in category or "crime" in category:
        return True
    text = " ".join(
        [
            title,
            str(article.get("summary") or "").lower(),
            str(article.get("content") or "").lower(),
        ]
    )
    return bool(_CRIME_RE.search(text))


def is_obituary_like(article: dict) -> bool:
    return bool(_OBITUARY_RE.search(str(article.get("title") or "").lower()))


def is_low_utility_article(article: dict) -> bool:
    text = " ".join(
        str(article.get(field) or "").lower()
        for field in ("category", "title", "summary", "content")
    )
    return bool(_LOW_UTILITY_RE.search(text))


def should_reject_before_local_manual_review(article: dict) -> bool:
    """Reject narrow low-value formats without weakening public-interest gates."""
    text = local_editorial_text(article)
    if _ROUTINE_FIRE_RE.search(text) and not _FIRE_PUBLIC_IMPACT_RE.search(text):
        return True
    if _LOW_VALUE_FEATURE_RE.search(text):
        return True
    return bool(
        _ROUTINE_ROAD_CLOSURE_RE.search(text)
        and not _SIGNIFICANT_TRANSPORT_IMPACT_RE.search(text)
    )


def is_high_value_local_civic_economic_article(article: dict) -> bool:
    text = local_editorial_text(article)
    return bool(
        not _PROMOTIONAL_RE.search(text)
        and _MATERIAL_CHANGE_RE.search(text)
        and _HIGH_VALUE_SECTOR_RE.search(text)
    )


def local_manual_review_editorial_reason(article: dict) -> str:
    text = local_editorial_text(article)
    for label, pattern in _REASON_PATTERNS:
        if re.search(pattern, text, re.I):
            return f"Local RSS article needs manual review: {label}"
    return "Local RSS article needs manual review: Soft local news"


def is_useful_local_article(article: dict) -> bool:
    if is_crime_like(article) or is_obituary_like(article):
        return False
    if is_high_value_local_civic_economic_article(article):
        return True
    if is_low_utility_article(article):
        return False
    text = " ".join(
        str(article.get(field) or "").lower()
        for field in ("title", "summary", "content")
    )
    return bool(_USEFUL_LOCAL_RE.search(text))
