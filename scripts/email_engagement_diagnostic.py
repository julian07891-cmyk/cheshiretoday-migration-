import hashlib
import os
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


def email_hash(email):
    return hashlib.sha256((email or "").strip().lower().encode()).hexdigest()[:8]


def aware(dt):
    if not dt:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            return None
    if getattr(dt, "tzinfo", None) is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


load_env()

client = MongoClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]

now = datetime.now(timezone.utc)
cutoffs = {
    "7d": now - timedelta(days=7),
    "14d": now - timedelta(days=14),
    "30d": now - timedelta(days=30),
}

sub_query = {
    "$and": [
        {"email": {"$exists": True, "$ne": ""}},
        {"$or": [{"daily_brief": True}, {"preferences.daily_brief": True}]},
        {"$or": [{"active": {"$ne": False}}, {"active": {"$exists": False}}]},
    ]
}

subs = list(db.subscribers.find(sub_query, {"email": 1, "created_at": 1, "source": 1, "active": 1, "daily_brief": 1, "preferences": 1}))
unique = {}
for s in subs:
    email = (s.get("email") or "").strip().lower()
    if email:
        unique[email] = s

analytics = list(db.email_analytics.find({}, {"tracking_id": 1, "opens": 1, "clicks": 1, "last_opened": 1, "last_clicked": 1}))

engaged_by_window = {k: set() for k in cutoffs}
clicked_by_window = {k: set() for k in cutoffs}

for a in analytics:
    tid = str(a.get("tracking_id") or "")
    if not tid:
        continue

    # tracking_id format ends with the 8-char email hash for recipient-specific Daily Brief links/pixels
    h = tid.rsplit("_", 1)[-1]
    if len(h) != 8:
        continue

    last_opened = aware(a.get("last_opened"))
    last_clicked = aware(a.get("last_clicked"))

    for label, cutoff in cutoffs.items():
        opened = last_opened and last_opened >= cutoff and (a.get("opens") or 0) > 0
        clicked = last_clicked and last_clicked >= cutoff and (a.get("clicks") or 0) > 0
        if opened or clicked:
            engaged_by_window[label].add(h)
        if clicked:
            clicked_by_window[label].add(h)

subscriber_hashes = {email_hash(email): email for email in unique}
protected = set()

# Protect very recent subscribers from any future suppression decision.
recent_cutoff = now - timedelta(days=30)
for email, s in unique.items():
    created = aware(s.get("created_at"))
    if created and created >= recent_cutoff:
        protected.add(email_hash(email))

print("EMAIL ENGAGEMENT DIAGNOSTIC — READ ONLY")
print("unique_active_daily_brief_subscribers=", len(unique))
print("subscriber_hashes=", len(subscriber_hashes))
print("email_analytics_docs=", len(analytics))
print("protected_recent_30d=", len(protected))

for label in ["7d", "14d", "30d"]:
    engaged = subscriber_hashes.keys() & engaged_by_window[label]
    clicked = subscriber_hashes.keys() & clicked_by_window[label]
    cold = set(subscriber_hashes.keys()) - engaged_by_window[label] - protected
    print()
    print(label)
    print("engaged_open_or_click=", len(engaged))
    print("clicked=", len(clicked))
    print("cold_no_open_or_click_excluding_recent_30d=", len(cold))

print()
print("RECOMMENDATION")
print("Do not deactivate from this script. Use this only to assess whether a controlled suppression tool is justified later.")
