import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pymongo import MongoClient


def load_env(path="backend/.env"):
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def article_url(article):
    base = "https://cheshiretoday.co.uk"
    article_id = str(article.get("id") or article.get("_id") or "")
    title = str(article.get("title") or "article").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", title).strip("-")[:80] or "article"
    return f"{base}/article/{article_id}/{slug}"


def title_keywords(title):
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "for", "to", "of", "in",
        "on", "at", "with", "as", "by", "and", "from", "this", "that", "will"
    }
    words = str(title or "").lower().split()
    return set(w.strip(".,:;!?()[]'\"") for w in words if len(w) > 3 and w not in stop_words)


towns = [
    "crewe", "macclesfield", "wilmslow", "chester", "warrington", "nantwich",
    "congleton", "northwich", "knutsford", "sandbach", "middlewich", "alsager",
    "winsford", "ellesmere port", "cheshire"
]

money_terms = [
    "mortgage", "rent", "council tax", "tax", "vat", "savings", "rates", "bills",
    "energy", "inflation", "budget", "cost", "prices", "wages", "pay", "pension"
]

business_terms = [
    "business", "jobs", "job", "workforce", "redundancy", "investment", "company",
    "startup", "factory", "employer", "retail", "hospitality", "growth", "market"
]

property_terms = [
    "property", "housing", "house", "home", "planning", "rent", "landlord",
    "mortgage", "development"
]

ai_terms = [
    "ai", "artificial intelligence", "chatgpt", "openai", "gemini", "automation",
    "software", "cyber", "data", "digital", "tech", "technology"
]

weak_terms = [
    "celebrity", "showbiz", "gaming", "xbox", "playstation", "nintendo",
    "sports", "sport", "football", "tv", "horror", "dinosaur", "squirrel",
    "osprey", "museum", "twins", "different dads", "underwater forests"
]

crime_terms = [
    "police", "court", "jailed", "assault", "murder", "stabbed", "crash",
    "arrest", "crime"
]


def text_blob(article):
    return " ".join([
        str(article.get("title") or ""),
        str(article.get("category") or ""),
        str(article.get("content") or "")[:700],
    ]).lower()

def has_term(blob, term):
    term = str(term or "").lower().strip()
    if not term:
        return False
    if " " in term:
        return term in blob
    return re.search(rf"\b{re.escape(term)}\b", blob) is not None


def has_any(blob, terms):
    return any(has_term(blob, term) for term in terms)


def is_local(article):
    blob = text_blob(article)
    return has_any(blob, towns)


def is_business(article):
    blob = text_blob(article)
    return has_any(blob, money_terms + business_terms + property_terms)


def is_tech(article):
    blob = text_blob(article)
    title = str(article.get("title") or "").lower()
    category = str(article.get("category") or "").lower()

    if has_any(blob, weak_terms):
        return False

    # Do not treat broad science/nature/oddity stories as useful AI/Tech.
    true_ai_tech_terms = [
        "ai", "artificial intelligence", "chatgpt", "openai", "gemini",
        "automation", "cyber", "software", "data centre", "cloud",
        "startup", "digital", "semiconductor", "chip", "microsoft", "google"
    ]

    return (
        has_any(category, ["ai", "technology"])
        or has_any(title, true_ai_tech_terms)
    )


def is_banned(article):
    blob = text_blob(article)
    category = str(article.get("category") or "").lower()
    if category in ["sports", "sport", "entertainment", "celebrity", "showbiz"]:
        return True
    return has_any(blob, weak_terms)


def score_article(article):
    blob = text_blob(article)
    title = str(article.get("title") or "")
    score = 0
    reasons = []

    if is_local(article):
        score += 30
        reasons.append("local/Cheshire relevance")
    if has_any(blob, money_terms):
        score += 25
        reasons.append("money/bills/tax impact")
    if has_any(blob, business_terms):
        score += 22
        reasons.append("business/jobs impact")
    if has_any(blob, property_terms):
        score += 18
        reasons.append("property/housing relevance")
    if is_tech(article):
        score += 18
        reasons.append("AI/tech usefulness")
    if any(ch.isdigit() for ch in title):
        score += 8
        reasons.append("specific number in headline")

    # Strong reader-impact phrasing.
    if has_any(blob, ["save", "savings", "advice", "retirement", "jobs", "job losses", "cost of living", "mortgage", "council tax"]):
        score += 18
        reasons.append("direct reader-impact angle")
    if len(title) <= 95:
        score += 5
        reasons.append("clear headline length")
    if has_any(blob, crime_terms):
        score -= 35
        reasons.append("crime/police/court penalty")
    if has_any(blob, weak_terms):
        score -= 40
        reasons.append("weak non-strategic topic penalty")

    return score, reasons


load_env()
client = MongoClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]

cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

pipeline = [
    {"$match": {"$or": [
        {"publishedDate": {"$gte": cutoff}},
        {"publishedDate": {"$gte": cutoff.isoformat()}}
    ]}},
    {"$sort": {"publishedDate": -1}},
    {"$group": {
        "_id": "$title",
        "mongo_id": {"$first": "$_id"},
        "custom_id": {"$first": "$id"},
        "title": {"$first": "$title"},
        "content": {"$first": "$content"},
        "category": {"$first": "$category"},
        "author": {"$first": "$author"},
        "image": {"$first": "$image"},
        "publishedDate": {"$first": "$publishedDate"},
        "source": {"$first": "$source"}
    }},
    {"$sort": {"publishedDate": -1}},
    {"$limit": 80}
]

recent = list(db.articles.aggregate(pipeline))[:80]

if len(recent) < 5:
    fallback_pipeline = [
        {"$sort": {"publishedDate": -1}},
        {"$group": {
            "_id": "$title",
            "mongo_id": {"$first": "$_id"},
            "custom_id": {"$first": "$id"},
            "title": {"$first": "$title"},
            "content": {"$first": "$content"},
            "category": {"$first": "$category"},
            "author": {"$first": "$author"},
            "image": {"$first": "$image"},
            "publishedDate": {"$first": "$publishedDate"},
            "source": {"$first": "$source"}
        }},
        {"$sort": {"publishedDate": -1}},
        {"$limit": 20}
    ]
    fallback = list(db.articles.aggregate(fallback_pipeline))
    seen = {str(a.get("title") or "").strip().lower() for a in recent}
    for a in fallback:
        key = str(a.get("title") or "").strip().lower()
        if key and key not in seen:
            recent.append(a)
            seen.add(key)
        if len(recent) >= 10:
            break

for a in recent:
    if a.get("mongo_id"):
        a["id"] = str(a["mongo_id"])
    elif a.get("custom_id"):
        a["id"] = str(a["custom_id"])
    a.pop("mongo_id", None)
    a.pop("custom_id", None)

seen_titles = set()
seen_keyword_sets = []
unique_articles = []

for a in recent:
    title = str(a.get("title") or "")
    norm = title.lower().strip()[:50]
    kws = title_keywords(title)

    if norm in seen_titles:
        continue

    similar = False
    for prev in seen_keyword_sets:
        if kws and prev:
            overlap = len(kws & prev)
            similarity = overlap / min(len(kws), len(prev))
            if similarity > 0.5:
                similar = True
                break

    if not similar:
        seen_titles.add(norm)
        seen_keyword_sets.append(kws)
        unique_articles.append(a)

scored = []
for a in unique_articles:
    score, reasons = score_article(a)
    scored.append((score, reasons, a))

local_bucket = []
business_bucket = []
tech_bucket = []
national_bucket = []
rejected = []

for score, reasons, a in sorted(scored, key=lambda x: x[0], reverse=True):
    if is_banned(a):
        rejected.append((score, reasons, a, "banned/weak category"))
        continue
    if score < 30:
        rejected.append((score, reasons, a, "below newsletter quality threshold"))
        continue
    if is_local(a):
        local_bucket.append((score, reasons, a))
    elif is_business(a):
        business_bucket.append((score, reasons, a))
    elif is_tech(a):
        tech_bucket.append((score, reasons, a))
    else:
        national_bucket.append((score, reasons, a))

selected = (
    local_bucket[:3]
    + business_bucket[:2]
    + tech_bucket[:1]
    + national_bucket[:2]
)

print("DAILY BRIEF PREVIEW — READ ONLY")
print("recent_candidates=", len(recent))
print("unique_after_dedupe=", len(unique_articles))
print("selected=", len(selected))
print()
quality_sorted = [
    (score, reasons, a)
    for score, reasons, a in sorted(scored, key=lambda x: x[0], reverse=True)
    if score >= 45 and not is_banned(a)
]

lead = quality_sorted[0] if quality_sorted else None
supporting = quality_sorted[1] if len(quality_sorted) > 1 else None
related = quality_sorted[2:5] if len(quality_sorted) > 2 else []

print()
print("QUALITY-FIRST RECOMMENDED DAILY BRIEF")
if lead:
    score, reasons, a = lead
    print(f"LEAD STORY | SCORE {score} | {a.get('category')} | {a.get('title')}")
    print(f"WHY: {', '.join(reasons) if reasons else 'no strong signal'}")
    print(f"URL: {article_url(a)}")
else:
    print("LEAD STORY | none strong enough")

if supporting:
    score, reasons, a = supporting
    print(f"SUPPORTING STORY | SCORE {score} | {a.get('category')} | {a.get('title')}")
    print(f"WHY: {', '.join(reasons) if reasons else 'no strong signal'}")
    print(f"URL: {article_url(a)}")
else:
    print("SUPPORTING STORY | none strong enough")

if related:
    print("RELATED / ALSO WORTH READING")
    for score, reasons, a in related:
        print(f"  SCORE {score} | {a.get('category')} | {a.get('title')}")
        print(f"  WHY: {', '.join(reasons) if reasons else 'no strong signal'}")
        print(f"  URL: {article_url(a)}")
else:
    print("RELATED / ALSO WORTH READING | none strong enough")

print()
print("SUBJECT LINE OPTIONS")
if lead:
    _, _, lead_article = lead
    lead_title = str(lead_article.get("title") or "").strip()
    lead_blob = text_blob(lead_article)

    if has_any(lead_blob, ["savings", "advice", "mortgage", "bills", "tax", "retirement", "pension"]):
        print("1. Money, savings and local impact: your Cheshire briefing")
        print("2. The money stories Cheshire readers should watch today")
        print("3. Cheshire Today: what today’s money headlines could mean for you")
    elif has_any(lead_blob, ["jobs", "job losses", "workforce", "business", "company", "employer"]):
        print("1. Jobs, business and local impact: your Cheshire briefing")
        print("2. The business stories Cheshire readers should watch today")
        print("3. Cheshire Today: what today’s business headlines could mean locally")
    elif has_any(lead_blob, ["property", "housing", "house", "home", "planning", "rent"]):
        print("1. Property, housing and local impact: your Cheshire briefing")
        print("2. The property stories Cheshire readers should watch today")
        print("3. Cheshire Today: what today’s housing headlines could mean locally")
    elif is_tech(lead_article):
        print("1. AI, technology and business: your Cheshire briefing")
        print("2. The tech stories Cheshire businesses should watch today")
        print("3. Cheshire Today: useful tech and business headlines")
    else:
        print("1. Your Cheshire briefing: the stories worth reading today")
        print("2. Cheshire Today: local, business and money headlines")
        print("3. What today’s headlines could mean for Cheshire")
else:
    print("No strong lead story available for subject-line generation")

print()

for label, bucket in [
    ("LOCAL", local_bucket[:3]),
    ("BUSINESS_FINANCE", business_bucket[:2]),
    ("AI_TECH", tech_bucket[:1]),
    ("NATIONAL_CONTEXT", national_bucket[:2]),
]:
    print(label)
    if not bucket:
        print("  none")
    for score, reasons, a in bucket:
        print(f"  SCORE {score} | {a.get('category')} | {a.get('title')}")
        print(f"  WHY: {', '.join(reasons) if reasons else 'no strong signal'}")
        print(f"  URL: {article_url(a)}")
    print()

print("TOP OVERALL CANDIDATES")
for score, reasons, a in sorted(scored, key=lambda x: x[0], reverse=True)[:10]:
    print(f"  SCORE {score} | {a.get('category')} | {a.get('title')}")
    print(f"  WHY: {', '.join(reasons) if reasons else 'no strong signal'}")

print()
print("REJECTED / LOW-VALUE SIGNALS")
for score, reasons, a, why in rejected[:10]:
    print(f"  SCORE {score} | {why} | {a.get('category')} | {a.get('title')}")
