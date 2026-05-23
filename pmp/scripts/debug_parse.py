import re
from pathlib import Path

import PyPDF2

PMP_ROOT = Path(__file__).resolve().parents[1]
r = PyPDF2.PdfReader(str(PMP_ROOT / "AR_200.pdf"))
text = "\n".join(p.extract_text() or "" for p in r.pages)
blocks = re.split(r"(?=Question\s+[\d\s]+)", text)
for block in blocks:
    qm = re.match(r"Question\s+([\d\s]+)\s+(.*)", block, re.DOTALL | re.I)
    if not qm:
        continue
    qnum = int(re.sub(r"\s+", "", qm.group(1)))
    if qnum not in [10, 11, 12, 109, 110, 111, 119, 120]:
        continue
    am = re.search(r'["\s]*Answer\s+(\d+)\s*:\s*([^"\n]+)', block, re.I)
    print("Q", qnum, "answer match", bool(am))
    if am:
        print("  ans num", am.group(1), "raw", repr(am.group(2)[:30]))
    else:
        # show tail of block
        print("  tail:", repr(block[-200:]))
