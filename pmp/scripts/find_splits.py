import json
import re
from pathlib import Path

from cleanup_question_text import get_common

html = Path(__file__).resolve().parents[1] / "pmp-mock-andrew.html"
qs = json.loads(re.search(r"const QUESTIONS = (\[.*?\]);\s*\n", html.read_text(encoding="utf-8"), re.S).group(1))
common = get_common()

seen = {}
for q in qs:
    for blob in [q["text"], *q["options"]]:
        for m in re.finditer(r"\b([a-z]{2,3})\s+([a-z]{2,})\b", blob, re.I):
            frag, rest = m.group(1), m.group(2)
            combo = (frag + rest).lower()
            if combo in common:
                seen.setdefault(m.group(0).lower(), []).append(q["id"])

for pat, ids in sorted(seen.items(), key=lambda x: -len(x[1])):
    print(f"{len(ids):3} Qs  {pat!r}  -> {pat.replace(' ', '')}")
