import json, re, sys, urllib.request

URL = "http://127.0.0.1:8000/api/articles?limit=120&with_total=1&include_archived=true"

with urllib.request.urlopen(URL) as r:
    d = json.loads(r.read().decode("utf-8", errors="replace"))

a = d.get("articles", [])
rx = re.compile(
    r"\b(ai|artificial intelligence|chatgpt|openai|gemini|llm|gpt-?\d*|prompt|"
    r"machine\s*learning|deep\s*learning|neural|chip|gpu|nvidia|amd|intel|semiconductor|"
    r"cybersecurity|ransomware|malware|phishing|hack(?:ed|ing)?|data\s*breach|breach|"
    r"cloud\s*comput(?:ing|e)|saas|robot|automation)\b",
    re.I,
)

def is_ai(x):
    cat = str(x.get("category", "")).lower()
    sec = str(x.get("section", "")).lower()

    if sec.startswith("ai-"):
        return ("sec", sec)

    if ("ai" in cat) or ("tech" in cat):
        return ("cat", cat)

    t = (str(x.get("title", "")) + " " + str(x.get("summary", "")) + " " + str(x.get("content", ""))).lower()
    m = rx.search(t)
    return ("rx", m.group(0)) if m else None

hits = []
for x in a:
    if x.get("is_local_source") is True:
        why = is_ai(x)
        if why:
            hits.append((why[0], why[1], x.get("category"), x.get("title", "")[:140]))

print("ARTICLES_RETURNED:", len(a))
print("LOCAL_MATCHING_isAiTech:", len(hits))
for w, v, c, t in hits[:80]:
    print(f"- via={w}::{v} | cat={c!r} | title={t}")
