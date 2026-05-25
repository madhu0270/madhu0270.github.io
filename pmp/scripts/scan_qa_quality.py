"""Report likely typos / PDF artifacts remaining in question text and options only."""
import json
import re
from pathlib import Path

html = Path(__file__).resolve().parents[1] / "pmp-mock-andrew.html"
qs = json.loads(
    re.search(r"const QUESTIONS = (\[.*?\]);\s*\n", html.read_text(encoding="utf-8"), re.S).group(1)
)

checks = [
    ("split ef/dif/af", r"\b(ef|dif|af)\s+[a-z]"),
    ("split of/traf/emer", r"\b(of|traf|emer|syner|char|staf|lar)\s+[a-z]"),
    ("apostrophe space", r"'\s+s\b"),
    ("space before punct", r"\s+[.,;:]"),
    ("double space", r"  +"),
    ("garbled Seq", r"SeqUENCi"),
    ("stray brace choose", r"\{Choose"),
    ("broken AI", r"\bAl\b"),
]

for label, pat in checks:
    hits = []
    for q in qs:
        for where, blob in [("text", q["text"])] + [(f"opt{i}", o) for i, o in enumerate(q["options"])]:
            if re.search(pat, blob):
                hits.append((q["id"], where))
    if hits:
        print(f"{label}: {len(hits)}")
        print("  sample:", hits[:8])
