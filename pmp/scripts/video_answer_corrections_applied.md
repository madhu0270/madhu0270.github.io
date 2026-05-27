# Video-authoritative answer corrections (Andrew 200)

When the PDF answer key disagrees with Andrew Ramdayal's YouTube walkthrough (`1sWpc6765AI`), **the video is treated as correct** only for questions listed below. All other questions use the **PDF key**.

## Active mock overrides (not PDF)

| Q | PDF | Mock | Video time | Notes |
|---|-----|------|------------|-------|
| 9 | B | **C** | 20:00 | User-verified; matches embedded explanation |
| **101** | A | **B** | 3:35:33 | Consult project organization guidelines |
| **104** | B & D | **B & C** | 3:42:20 | Choose 2 — progressive elaboration + iterative planning |
| 128 | D | **A** | 4:28:37 | Collaborative session; bad `keyword_zone` had forced D |

Pinned in `apply_video_answer_fixes.py` (`MANUAL` / `MANUAL_MULTI`).

## Reverted to PDF (formerly video overrides)

Q26, Q34, Q42, Q48, Q77, Q80, Q99, Q108, Q109, Q110, Q111, Q127, Q155, Q183, Q185, Q194, Q199 — mock now matches `AR_200.pdf`.

Updated: `pmp-mock-andrew.html`, `scripts/ar200_from_pdf.json`, `ANSWER_KEYS.txt`

## Audit scripts

```bash
python scripts/extract_video_correct_answers.py
python scripts/find_explanation_answer_mismatches.py
python scripts/apply_video_answer_fixes.py
```
