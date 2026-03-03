import sys
import json
import re
from collections import Counter

data = json.load(sys.stdin)
articles = data.get("articles", [])

print("returned:", len(articles))
print("total:", data.get("total"))

cats = Counter([a.get("category") for a in articles])
scopes = Counter([a.get("scope") for a in articles])

print("cats:", dict(cats))
print("scopes:", dict(scopes))

rx_ai = re.compile(
    r'(?:\bai\b|artificial\s+intelligence|chatgpt|openai|gemini|\bllm\b|gpt-?\d*|machine\s*learning|deep\s*learning|cybersecurity|ransomware|data\s*breach|cloud\s*comput(?:ing|e)|\bsaas\b|automation)',
    re.I
)

ai = [
    a for a in articles
    if rx_ai.search(
        (a.get("title","") + " " + a.get("summary","") + " " + (a.get("content") or ""))
    )
]

print("ai_signal_count:", len(ai))

for x in ai[:15]:
    print("-", x.get("category"), "|", x.get("scope"), "|", x.get("source"), "|", x.get("title"))
