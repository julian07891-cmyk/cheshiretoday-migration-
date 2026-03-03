import json, re, urllib.request

URL = "http://127.0.0.1:8000/api/articles?limit=120&with_total=1&include_archived=true"

with urllib.request.urlopen(URL) as r:
    d = json.loads(r.read().decode("utf-8", errors="replace"))

articles = d.get("articles", [])

rx_bad = re.compile(r"\bai", re.I)     # matches ai at start of a word (ai..., airline, airbase)
rx_good = re.compile(r"\bai\b", re.I)  # matches standalone word "AI"

false_hits = []

for x in articles:
    text = ((x.get("title", "") or "") + " " + (x.get("summary", "") or "")).lower()
    if rx_bad.search(text) and not rx_good.search(text):
        false_hits.append(
            (x.get("category"), x.get("source"), x.get("title", "")[:120])
        )

print("AI_PREFIX_FALSE_POSITIVE_CANDIDATES:", len(false_hits))
for cat, src, title in false_hits[:30]:
    print("-", cat, "|", src, "|", title)
