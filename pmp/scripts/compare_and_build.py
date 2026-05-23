"""Compare HTML QUESTIONS with PDF parse and build merge script output."""
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
    return json.loads(m.group(1))


def main():
    html_qs = load_html_questions()
    pdf_qs = json.load(open(PDF_JSON, encoding="utf-8"))
    pdf_by_id = {q["id"]: q for q in pdf_qs}

    print(f"HTML: {len(html_qs)} questions")
    print(f"PDF: {len(pdf_qs)} questions")

    html_ids = {q["id"] for q in html_qs}
    pdf_ids = {q["id"] for q in pdf_qs}
    print("In HTML not PDF:", sorted(html_ids - pdf_ids)[:30], "... total", len(html_ids - pdf_ids))
    print("In PDF not HTML:", sorted(pdf_ids - html_ids))

    mismatches = []
    for hq in html_qs:
        pid = hq["id"]
        if pid not in pdf_by_id:
            continue
        pq = pdf_by_id[pid]
        html_correct = hq.get("correctIndices") or [hq["correct"]]
        pdf_correct = pq.get("correctIndices") or [pq["correct"]]
        if sorted(html_correct) != sorted(pdf_correct):
            mismatches.append(
                {
                    "id": pid,
                    "html": html_correct,
                    "pdf": pdf_correct,
                    "pdfRaw": pq.get("answerRaw"),
                }
            )

    print(f"Answer mismatches (where PDF parsed): {len(mismatches)}")
    for m in mismatches[:25]:
        print(f"  Q{m['id']}: html={m['html']} pdf={m['pdf']} ({m['pdfRaw']})")


if __name__ == "__main__":
    main()
