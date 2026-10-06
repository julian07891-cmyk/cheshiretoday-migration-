"""Shared binary editorial eligibility for public and Admin article lists."""

import re


_ECON_HINT = re.compile(
    r"\b(tax|budget|inflation|interest\s*rate|rates|mortgage|rent|wages|jobs|growth|economy|economic|"
    r"business|finance|markets?|prices?|bills?|energy|housing|trade|tariff|investment)\b",
    re.I,
)
_NOISE_KW = re.compile(
    r"\b(the\s+papers|on\s+ropes|nightmare\s+for|grop(?:e|ing)|pitch\s+invader)\b",
    re.I,
)
_DEVOLVED_OR_REGIONAL_KW = re.compile(
    r"\b(scotland|scottish|glasgow|edinburgh|wales|welsh|cardiff|northern\s+ireland|belfast)\b",
    re.I,
)
_UK_WIDE_SCOPE_KW = re.compile(
    r"\b(uk|united\s+kingdom|britain|british|westminster|uk\s+government|"
    r"british\s+government|bank\s+of\s+england|house\s+of\s+commons|downing\s+street|"
    r"national\s+grid)\b",
    re.I,
)


def is_uk_feed_noise(article: dict) -> bool:
    cat = (article.get("category") or "").lower()
    src = (article.get("source") or "").lower()
    url = (article.get("source_url") or "").lower()
    title = (article.get("title") or "").lower()
    summary = (article.get("summary") or "").lower()
    text_meta = f"{title} {summary}"

    if "sport" in cat or "sport" in src or "/sport/" in url or "skysports" in url:
        return True
    if "/watch/" in url or "/video" in url or "watch video" in title:
        return True
    if _NOISE_KW.search(text_meta):
        return True

    # Exclude devolved/regional-only coverage, but retain stories carrying an
    # explicit UK-wide institutional or geographic scope signal.
    if _DEVOLVED_OR_REGIONAL_KW.search(text_meta) and not _UK_WIDE_SCOPE_KW.search(text_meta):
        return True

    if ("uk news" in cat) and re.search(
        r"\b(mp|labour|conservative|tory|starmer|reeves|parliament|byelection|election)\b",
        title,
        re.I,
    ):
        if not _ECON_HINT.search(text_meta):
            return True

    if cat == "uk news":
        impact_kw = re.compile(
            r"\b(nhs|hospital|gp|doctor|schools?|education|council|planning|housing|rent|mortgage|"
            r"tax|budget|inflation|interest\s*rate|rates|jobs|wages|economy|economic|business|"
            r"finance|markets?|prices?|bills?|energy|transport|rail|road|roadworks|investment|"
            r"trade|tariff|regulation|regulator|ofgem|ofwat|boe|bank of england)\b",
            re.I,
        )
        uk_fuel_supply_impact = (
            re.search(r"\b(uk|britain|british)\b", text_meta)
            and re.search(
                r"\b(?:(?:emergency|strategic)\s+(?:diesel|petrol|fuel)\s+"
                r"(?:reserves?|stockpiles?)|(?:diesel|petrol|fuel)\s+"
                r"(?:shortages?|supply\s+(?:security|disruptions?|threats?)))\b",
                text_meta,
            )
        )
        if not _ECON_HINT.search(text_meta) and not impact_kw.search(text_meta) and not uk_fuel_supply_impact:
            return True

    return False


def is_public_editorial_noise(article: dict) -> bool:
    cat = (article.get("category") or "").lower()
    url = (article.get("source_url") or "").lower()
    title = (article.get("title") or "").lower()
    summary = (article.get("summary") or "").lower()
    text_meta = f"{title} {summary}"

    if "/audio/" in url or "podcast" in title or "podcast" in summary:
        return True
    if "/video" in url or "/watch/" in url or "watch video" in title:
        return True
    if "/gallery/" in url:
        return True
    if re.search(r"\b(letter|letters|cartoon|opinion|editorial)\b", title, re.I):
        return True
    if re.search(
        r"\b(celebrity|showbiz|reality\s*tv|love island|netflix|concert|album|music\s*video|bts|kris jenner|kardashian)\b",
        text_meta,
        re.I,
    ):
        return True
    if re.search(
        r"\b(cocaine|drugs?|gangs?|devastating diagnosis|started to ache|lost everything|"
        r"hit-and-run|knocked off|smash between|train station crash|emergency services respond|"
        r"in pictures|pictures from|anniversary celebrations|"
        r"horror m56 crash|two in hospital after horror|chester zoo celebrates|aardvark|"
        r"lake study|cancel climate impact|ill health in old age|roblox|"
        r"keep your home.*cool|video doorbells|football club could become home|"
        r"fastest growing sport|five engines called|discarded cigarette|firefighters deal|city centre incident|"
        r"pokemon|alton towers|period drama|free to watch|animal park|tiger cubs?|hedgehogs?|"
        r"x limits|freeloaders|airbus gets hpc|hpc-as-a-service|zte showcases|brazil|"
        r"typhoon jets|swinney|first minister vote|swatch|starbucks korea|tank day|"
        r"elon musk has lost|new high street crime unit|st brelade|iran hints it could interfere|"
        r"vmware quietly debuts|mace wants to make power bills)\b",
        text_meta,
        re.I,
    ):
        return True
    if cat in {"science", "tech", "business", "uk news"} and re.search(
        r"\b(letter|letters|cartoon|podcast)\b", text_meta, re.I
    ):
        return True
    return False


def is_local_public_editorial_noise(article: dict) -> bool:
    url = (article.get("source_url") or "").lower()
    title = (article.get("title") or "").lower()
    summary = (article.get("summary") or "").lower()
    text_meta = f"{title} {summary}"

    if "/audio/" in url or "podcast" in text_meta:
        return True
    if "/video" in url or "/watch/" in url or "watch video" in title:
        return True
    if "/gallery/" in url or "in pictures" in title or "pictures from" in title:
        return True
    if re.search(r"\b(letter|letters|cartoon|opinion|editorial)\b", title, re.I):
        return True
    return False


def is_public_article_editorially_eligible(article: dict, *, filtering_enabled: bool = True) -> bool:
    """Return binary editorial eligibility; rank-dependent sensitive caps stay separate."""
    if article.get("force_live") is True or not filtering_enabled:
        return True
    if article.get("is_local_source") is True:
        return not is_local_public_editorial_noise(article)
    return not is_uk_feed_noise(article) and not is_public_editorial_noise(article)
