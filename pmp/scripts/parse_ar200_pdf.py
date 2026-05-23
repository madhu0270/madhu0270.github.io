"""Parse AR_200.pdf into structured questions JSON."""
import re
import json
import sys
from pathlib import Path

import PyPDF2

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "AR_200.pdf"
OUT = ROOT / "scripts" / "ar200_from_pdf.json"


def letter_to_index(s: str) -> list[int]:
    """Parse answer like 'D', 'D & E', 'A, B and C' into 0-based indices."""
    s = s.strip().upper()
    s = re.sub(r"\s+AND\s+", " ", s)
    s = s.replace("&", " ")
    s = re.sub(r"[^A-E\s,]", "", s)
    parts = re.findall(r"[A-E]", s)
    return sorted({ord(p) - ord("A") for p in parts})


def is_multi_select(qtext: str) -> bool:
    t = qtext.lower()
    return bool(
        re.search(
            r"\(choose\s+(two|three|2|3)\)|choose\s+(two|three)|select\s+(two|three)|select\s+all\s+that",
            t,
        )
    )


def parse_pdf() -> list[dict]:
    reader = PyPDF2.PdfReader(str(PDF))
    text = "\n".join(p.extract_text() or "" for p in reader.pages)
    # normalize odd spaces
    text = text.replace("\u2019", "'").replace("\ufffd", "'")

    blocks = re.split(r"(?=Question\s+[\d\s]+)", text)
    questions = []

    for block in blocks:
        qm = re.match(
            r"Question\s+([\d\s]+)\s+(.*)",
            block,
            re.DOTALL | re.IGNORECASE,
        )
        if not qm:
            continue
        qnum_str = re.sub(r"\s+", "", qm.group(1))
        if not qnum_str.isdigit():
            continue
        qnum = int(qnum_str)
        rest = qm.group(2)

        am = re.search(
            r'["\s]*Answer\s+([\d\s]+)\s*:\s*([^"\n]+)',
            rest,
            re.IGNORECASE,
        )
        if not am:
            continue
        ans_qnum = int(re.sub(r"\s+", "", am.group(1)))
        if ans_qnum != qnum:
            continue
        ans_raw = am.group(2).strip().strip('"').strip()

        body = rest[: am.start()]
        lines = [ln.strip() for ln in body.split("\n") if ln.strip()]

        q_lines = []
        opt_lines = []
        in_opts = False
        for line in lines:
            if re.match(r"^[A-E]\.\s", line):
                in_opts = True
            if in_opts:
                opt_lines.append(line)
            else:
                q_lines.append(line)

        qtext = re.sub(r"\s+", " ", " ".join(q_lines)).strip()
        # remove stray leading artifacts
        qtext = re.sub(r"^[Llv]\s+", "", qtext)

        opts = []
        if opt_lines:
            combined = " ".join(opt_lines)
            # PDF typo: "8." used instead of "B." (e.g. Q77)
            combined = re.sub(r"\s8\.\s+", " B. ", combined, count=1)
            chunks = re.split(r"(?=[A-E]\.\s)", combined)
            for ch in chunks:
                ch = ch.strip()
                om = re.match(r"^[A-E]\.\s+(.*)", ch, re.DOTALL)
                if om:
                    opt_text = re.sub(r"\s+", " ", om.group(1).strip())
                    opts.append(opt_text)

        indices = letter_to_index(ans_raw)
        multi = is_multi_select(qtext) or len(indices) > 1

        entry = {
            "id": qnum,
            "text": qtext,
            "options": opts,
            "multi": multi,
            "answerRaw": ans_raw,
        }
        if multi:
            entry["correctIndices"] = indices
        else:
            entry["correct"] = indices[0] if indices else 0

        questions.append(entry)

    questions.sort(key=lambda x: x["id"])
    return questions


def main():
    qs = parse_pdf()
    print(f"Parsed {len(qs)} questions")
    multi = [q for q in qs if q.get("multi")]
    print(f"Multi-select: {len(multi)}")
    for q in multi:
        print(f"  Q{q['id']}: {q['answerRaw']} -> {q.get('correctIndices')}")

    missing = [q for q in qs if len(q["options"]) < 4]
    if missing:
        print(f"Warning: {len(missing)} questions with <4 options")
        for q in missing[:5]:
            print(f"  Q{q['id']}: {len(q['options'])} opts")

    OUT.write_text(json.dumps(qs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
