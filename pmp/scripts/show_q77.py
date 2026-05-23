from pathlib import Path

import PyPDF2

PMP_ROOT = Path(__file__).resolve().parents[1]
r = PyPDF2.PdfReader(str(PMP_ROOT / "AR_200.pdf"))
text = "\n".join(p.extract_text() or "" for p in r.pages)
i = text.find("Question 77")
print(text[i : i + 1200])
