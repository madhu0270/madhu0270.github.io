"""Apply video-authoritative answer corrections to HTML and PDF JSON."""
from __future__ import annotations

import json
import re
from pathlib import Path

PMP_ROOT = Path(__file__).resolve().parents[1]
HTML = PMP_ROOT / "pmp-mock-andrew.html"
PDF_JSON = PMP_ROOT / "scripts" / "ar200_from_pdf.json"
VIDEO_ANSWERS = PMP_ROOT / "scripts" / "video_authoritative_answers.json"
EXPL_MISMATCHES = PMP_ROOT / "scripts" / "explanation_mismatches.json"

# User-verified + always prefer video when listed here
MANUAL: dict[int, int] = {
    9: 2,  # C — professional development (user-verified; matches embedded explanation)
    101: 1,  # B — consult project organization guidelines (user-requested)
    128: 0,  # A — collaborative session (video @ 4:28:37; bad keyword_zone had forced D)
    # PDF key (pinned; do not re-apply video overrides)
    26: 1,
    34: 0,
    42: 1,
    48: 0,
    77: 1,
    80: 0,
    99: 2,
    108: 2,
    109: 2,
    110: 1,
    111: 0,
    127: 1,
    155: 0,
    183: 3,
    185: 2,
    194: 1,
    199: 3,
}

# Multi-select (Choose 2): qid -> sorted 0-based indices
MANUAL_MULTI: dict[int, list[int]] = {
    104: [1, 2],  # B & C — progressive elaboration + iterative planning (video @ 3:42:20)
}


def load_questions() -> list[dict]:
    text = HTML.read_text(encoding="utf-8")
    m = re.search(r"const QUESTIONS = (\[.*?\]);\s*\n\s*const PMP", text, re.DOTALL)
    return json.loads(m.group(1))


def build_correction_map(questions: list[dict]) -> dict[int, int]:
    by_id = {q["id"]: q for q in questions}
    corrections = dict(MANUAL)
    for qid in MANUAL_MULTI:
        corrections.pop(qid, None)

    expl_agree: dict[int, int] = {}
    if EXPL_MISMATCHES.exists():
        for row in json.loads(EXPL_MISMATCHES.read_text(encoding="utf-8")):
            expl_agree[row["id"]] = row["inferred_idx"]

    if VIDEO_ANSWERS.exists():
        for row in json.loads(VIDEO_ANSWERS.read_text(encoding="utf-8")):
            qid = row["id"]
            idx = row["to_index"]
            q = by_id.get(qid)
            if not q or "correct" not in q:
                continue
            if idx < 0 or idx >= len(q["options"]):
                continue
            margin = row.get("margin", 0)
            method = row.get("method", "")
            expl_match = expl_agree.get(qid) == idx
            if method == "explicit_letter":
                pass
            elif margin >= 12:
                pass
            elif margin >= 8 and expl_match:
                pass
            elif margin >= 5 and expl_match:
                pass
            else:
                continue
            if qid in MANUAL:
                continue
            corrections[qid] = idx

    corrections.update(MANUAL)

    return corrections


def apply(questions: list[dict], corrections: dict[int, int]) -> int:
    n = 0
    by_id = {q["id"]: q for q in questions}
    for qid, idx in sorted(corrections.items()):
        q = by_id.get(qid)
        if not q or "correct" not in q or q["correct"] == idx:
            continue
        old = q["correct"]
        q["correct"] = idx
        print(f"Q{qid}: {chr(65 + old)} -> {chr(65 + idx)}")
        n += 1
    for qid, indices in sorted(MANUAL_MULTI.items()):
        q = by_id.get(qid)
        if not q or not is_multi(q):
            continue
        old = sorted(q.get("correctIndices") or [])
        new = sorted(indices)
        if old == new:
            continue
        q["correctIndices"] = new
        old_s = " & ".join(chr(65 + i) for i in old) or "?"
        new_s = " & ".join(chr(65 + i) for i in new)
        print(f"Q{qid}: {old_s} -> {new_s}")
        n += 1
    return n


def is_multi(q: dict) -> bool:
    return q.get("multi") is True and isinstance(q.get("correctIndices"), list)


def write_html(questions: list[dict]) -> None:
    text = HTML.read_text(encoding="utf-8")
    m = re.search(
        r"(const QUESTIONS = )(\[.*?\])(;\s*\n\s*const PMP)",
        text,
        re.DOTALL,
    )
    if not m:
        raise RuntimeError("QUESTIONS not found")
    new_json = json.dumps(questions, ensure_ascii=False, separators=(",", ":"))
    HTML.write_text(text[: m.start(2)] + new_json + text[m.end(2) :], encoding="utf-8")


def write_pdf(corrections: dict[int, int]) -> int:
    data = json.loads(PDF_JSON.read_text(encoding="utf-8"))
    by_id = {q["id"]: q for q in data}
    n = 0
    for qid, idx in corrections.items():
        q = by_id.get(qid)
        if not q or q.get("correct") == idx:
            continue
        q["correct"] = idx
        q["answerRaw"] = chr(65 + idx)
        n += 1
    for qid, indices in MANUAL_MULTI.items():
        q = by_id.get(qid)
        if not q:
            continue
        new = sorted(indices)
        if sorted(q.get("correctIndices") or []) == new:
            continue
        q["correctIndices"] = new
        q["answerRaw"] = " & ".join(chr(65 + i) for i in new)
        n += 1
    PDF_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return n


def main() -> None:
    questions = load_questions()
    corrections = build_correction_map(questions)
    print(f"Applying {len(corrections)} video-authoritative answer(s):\n")
    html_n = apply(questions, corrections)
    if html_n:
        write_html(questions)
    pdf_n = write_pdf(corrections)
    print(f"\nUpdated {html_n} in HTML, {pdf_n} in ar200_from_pdf.json")


if __name__ == "__main__":
    main()
