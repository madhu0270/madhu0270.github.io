import json, re
from pathlib import Path
from audit_five_option_questions import load_html_questions, extract_pdf_question
import PyPDF2

PMP_ROOT = Path(__file__).resolve().parents[1]
reader = PyPDF2.PdfReader(str(PMP_ROOT / "AR_200.pdf"))
pdf_text = "\n".join(p.extract_text() or "" for p in reader.pages)
qs = {q["id"]: q for q in load_html_questions()}

for qid in [5, 16, 91, 125, 140, 158, 179]:
    h, p = qs[qid], extract_pdf_question(qid, pdf_text)
    print("=" * 60, f"Q{qid}")
    print("STEM HTML:", h["text"])
    print("STEM PDF:", p["text"])
    print("ANSWER PDF:", p["answerRaw"])
    for i in range(max(len(h["options"]), len(p["options"]))):
        ho = h["options"][i] if i < len(h["options"]) else "(missing)"
        po = p["options"][i] if i < len(p["options"]) else "(missing)"
        print(f"\n{chr(65+i)} HTML: {ho}")
        print(f"{chr(65+i)} PDF:  {po}")
