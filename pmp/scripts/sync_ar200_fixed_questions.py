"""Sync manually fixed questions from HTML back into ar200_from_pdf.json."""
from __future__ import annotations

import json
import re
from pathlib import Path

PMP_ROOT = Path(__file__).resolve().parents[1]
HTML = PMP_ROOT / "pmp-mock-andrew.html"
AR_JSON = PMP_ROOT / "scripts" / "ar200_from_pdf.json"
FIXED_IDS = (111, 117, 118, 124, 130)


def main() -> None:
    text = HTML.read_text(encoding="utf-8")
    qs = json.loads(
        re.search(r"const QUESTIONS = (\[.*?\]);\s*\n\s*const", text, re.DOTALL).group(1)
    )
    html_by = {q["id"]: q for q in qs}
    ar = json.loads(AR_JSON.read_text(encoding="utf-8"))

    for q in ar:
        qid = q["id"]
        if qid not in FIXED_IDS:
            continue
        h = html_by[qid]
        q["text"] = h["text"]
        q["options"] = h["options"]
        q["multi"] = False
        q.pop("correctIndices", None)
        q["correct"] = h["correct"]
        letters = "ABCDE"
        q["answerRaw"] = letters[h["correct"]]

    AR_JSON.write_text(json.dumps(ar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated ar200_from_pdf.json for questions: {list(FIXED_IDS)}")


if __name__ == "__main__":
    main()
