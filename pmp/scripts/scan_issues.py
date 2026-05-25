import json
import re

text = open("../pmp-mock-andrew.html", encoding="utf-8").read()
qs = json.loads(re.search(r"const QUESTIONS = (\[.*?\]);\s*\n", text, re.S).group(1))

patterns = [
    r"ef\s+f",
    r"dif\s+f",
    r"af\s+f",
    r"of\s+f",
    r"traf\s+f",
    r"emer\s+g",
    r"syner\s+g",
    r"Or\s+g",
    r"staf\s+f",
    r"char\s+g",
    r"'\s+s\b",
    r"\s+\.",
    r"\{Choose",
    r"SeqUENCi",
    r"\bro\.",
    r"gy and",
    r"fic flow",
    r"ged between",
]

for pat in patterns:
    hits = []
    for q in qs:
        fields = [("text", q["text"])] + [(f"opt{i}", o) for i, o in enumerate(q["options"])]
        for field_name, field in fields:
            if re.search(pat, field, re.I):
                hits.append((q["id"], field_name, re.search(pat, field).group(0)))
    if hits:
        print(pat, ":", len(hits))
        for h in hits[:5]:
            print(" ", h)
