import os
import re
from pathlib import Path

# Load .env
envp = Path("backend/.env")
env = {}
if envp.exists():
    for line in envp.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")

mongo_uri = (
    env.get("MONGO_URL")
    or env.get("MONGODB_URI")
    or env.get("MONGODB_URL")
    or os.environ.get("MONGO_URL")
    or os.environ.get("MONGODB_URI")
    or os.environ.get("MONGODB_URL")
)

db_name = (
    env.get("MONGO_DB")
    or env.get("MONGODB_DB")
    or env.get("DB_NAME")
    or os.environ.get("MONGO_DB")
    or "cheshire_today"
)

if not mongo_uri:
    raise SystemExit("ERROR: No Mongo URI found.")

phrase_re = re.compile(r"\n*Read the full story at the source\s*:?\s*.*$", re.I | re.S)
url_re = re.compile(r"https?://\S+", re.I)

def clean(text):
    if not isinstance(text, str) or not text:
        return text
    text = phrase_re.sub("", text)
    text = url_re.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

from pymongo import MongoClient

client = MongoClient(mongo_uri)
col = client[db_name]["articles"]

changed = 0
for doc in col.find({}, {"_id": 1, "summary": 1, "content": 1}):
    new_summary = clean(doc.get("summary", ""))
    new_content = clean(doc.get("content", ""))
    if new_summary != doc.get("summary", "") or new_content != doc.get("content", ""):
        col.update_one(
            {"_id": doc["_id"]},
            {"$set": {"summary": new_summary, "content": new_content}},
        )
        changed += 1

print("CLEAN COMPLETE | documents updated:", changed)
