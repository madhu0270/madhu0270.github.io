"""Merge PDF questions into pmp-mock-andrew.html, preserving explanations."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "pmp-mock-andrew.html"
PDF_JSON = ROOT / "scripts" / "ar200_from_pdf.json"


def load_html_questions():
    text = HTML.read_text(encoding="utf-8")
    m = re.search(r"const QUESTIONS = (\[.*?\]);\s*\n", text, re.DOTALL)
    if not m:
        raise SystemExit("QUESTIONS array not found")
    return json.loads(m.group(1)), text, m


def merge_question(html_q: dict, pdf_q: dict) -> dict:
    out = {
        "id": pdf_q["id"],
        "text": pdf_q["text"],
        "options": pdf_q["options"],
    }
    if pdf_q.get("multi"):
        out["multi"] = True
        out["correctIndices"] = pdf_q["correctIndices"]
    else:
        out["correct"] = pdf_q["correct"]

    for key in ("explanation", "videoUrl", "videoId", "videoSeconds", "videoTime"):
        if key in html_q and html_q[key]:
            out[key] = html_q[key]
    return out


def main():
    html_qs, full_text, match = load_html_questions()
    pdf_qs = json.load(open(PDF_JSON, encoding="utf-8"))
    html_by_id = {q["id"]: q for q in html_qs}

    merged = []
    for pq in sorted(pdf_qs, key=lambda x: x["id"]):
        hq = html_by_id.get(pq["id"], {})
        merged.append(merge_question(hq, pq))

    new_json = json.dumps(merged, ensure_ascii=False, separators=(",", ":"))
    new_text = full_text[: match.start(1)] + new_json + full_text[match.end(1) :]
    HTML.write_text(new_text, encoding="utf-8")

    multi = sum(1 for q in merged if q.get("multi"))
    print(f"Wrote {len(merged)} questions ({multi} multi-select) to {HTML}")


if __name__ == "__main__":
    main()
