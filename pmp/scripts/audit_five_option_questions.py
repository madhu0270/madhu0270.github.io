"""Audit 5-option (A–E) questions in mock vs AR_200.pdf."""
from __future__ import annotations

import json
import re
from pathlib import Path

import PyPDF2

PMP_ROOT = Path(__file__).resolve().parents[1]
HTML = PMP_ROOT / "pmp-mock-andrew.html"
PDF = PMP_ROOT / "AR_200.pdf"
AR_JSON = PMP_ROOT / "scripts" / "ar200_from_pdf.json"


def norm(s: str) -> str:
    s = re.sub(r"\s+", " ", s.lower().strip())
    for a, b in [
        ("ef fective", "effective"),
        ("ef fort", "effort"),
        ("of f", "off"),
        ("staf f", "staff"),
        ("kick-of f", "kick-off"),
        ("emer ged", "emerged"),
        ("or ganize", "organize"),
        ("detail timeline", "detailed timeline"),
    ]:
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9 ?(),.-]", "", s)
    return s


def load_html_questions() -> list[dict]:
    text = HTML.read_text(encoding="utf-8")
    m = re.search(r"const QUESTIONS = (\[.*?\]);\s*\n\s*const", text, re.DOTALL)
    return json.loads(m.group(1))


def extract_pdf_question(qid: int, pdf_text: str) -> dict | None:
    m = re.search(
        rf"Question\s+{qid}\s+(.*?)Answer\s+{qid}\s*:\s*([^\n\"]+)",
        pdf_text,
        re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return None
    body = m.group(1)
    ans = m.group(2).strip().strip('"')
    lines = body.split("\n")
    q_lines, opt_lines = [], []
    in_opts = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r"^[A-E]\.\s", line):
            in_opts = True
        if in_opts:
            opt_lines.append(line)
        else:
            q_lines.append(line)
    qtext = re.sub(r"\s+", " ", " ".join(q_lines)).strip()
    qtext = re.sub(r"^[Llv]\s+", "", qtext)
    opts = []
    if opt_lines:
        combined = " ".join(opt_lines)
        combined = re.sub(r"\s8\.\s+", " B. ", combined, count=1)
        for ch in re.split(r"(?=[A-E]\.\s)", combined):
            ch = ch.strip()
            om = re.match(r"^[A-E]\.\s+(.*)", ch, re.DOTALL)
            if om:
                opts.append(re.sub(r"\s+", " ", om.group(1).strip()))
    return {"id": qid, "text": qtext, "options": opts, "answerRaw": ans}


def letter_to_indices(raw: str) -> list[int]:
    s = re.sub(r"\s+and\s+", " ", raw.strip().upper())
    s = s.replace("&", " ")
    parts = re.findall(r"[A-E]", s)
    return sorted({ord(p) - ord("A") for p in parts})


def main() -> None:
    qs = load_html_questions()
    ar = json.loads(AR_JSON.read_text(encoding="utf-8"))
    ar_by = {q["id"]: q for q in ar}
    reader = PyPDF2.PdfReader(str(PDF))
    pdf_text = "\n".join(p.extract_text() or "" for p in reader.pages)

    five_html = [q for q in qs if len(q["options"]) == 5]
    print(f"HTML questions with 5 options: {len(five_html)}")
    for q in five_html:
        print(f"  Q{q['id']}")

  # PDF: all questions with 5 options
    pdf_five = []
    for qid in range(1, 201):
        pq = extract_pdf_question(qid, pdf_text)
        if pq and len(pq["options"]) == 5:
            pdf_five.append(pq)
    print(f"\nPDF questions with 5 options: {len(pdf_five)}")
    for pq in pdf_five:
        print(f"  Q{pq['id']} answer={pq['answerRaw']}")

    print("\n--- Detailed audit (HTML vs PDF extract) ---")
    issues = []
    for h in five_html:
        qid = h["id"]
        pq = extract_pdf_question(qid, pdf_text)
        if not pq:
            issues.append((qid, "missing_from_pdf"))
            continue
        if len(pq["options"]) != 5:
            issues.append((qid, f"pdf_has_{len(pq['options'])}_opts"))
        pdf_idx = letter_to_indices(pq["answerRaw"])
        html_idx = sorted(h.get("correctIndices") or [])
        if pdf_idx != html_idx:
            issues.append((qid, "answer_mismatch", html_idx, pdf_idx, pq["answerRaw"]))
        if norm(h["text"]) != norm(pq["text"]):
            issues.append((qid, "stem_mismatch"))
        for i in range(min(5, len(h["options"]), len(pq["options"]))):
            if norm(h["options"][i]) != norm(pq["options"][i]):
                issues.append((qid, f"option_{chr(65+i)}_mismatch"))

    if not issues:
        print("All 5-option questions match PDF.")
    else:
        for row in issues:
            print(row)

    # Corrupt 5-option in PDF (split stem) not in HTML anymore
    corrupt_pdf = []
    for pq in pdf_five:
        qid = pq["id"]
        h = next((q for q in qs if q["id"] == qid), None)
        if h and len(h["options"]) == 4:
            corrupt_pdf.append(qid)
    if corrupt_pdf:
        print(f"\nPDF still 5-option but HTML fixed to 4: {corrupt_pdf}")


if __name__ == "__main__":
    main()
