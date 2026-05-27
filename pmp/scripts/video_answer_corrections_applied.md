# Video-authoritative answer corrections (Andrew 200)

When the PDF answer key disagrees with Andrew Ramdayal's YouTube walkthrough (`1sWpc6765AI`), **the video is treated as correct**.

## Applied corrections (18 questions)

| Q | Was | Now | Video time |
|---|-----|-----|------------|
| 9 | C | **B** | 20:00 |
| 26 | B | **A** | 57:25 |
| 34 | A | **C** | 1:15:50 (explicit in video) |
| 42 | B | **C** | 1:29:48 |
| 48 | A | **C** | 1:42:42 |
| 77 | B | **A** | 2:40:25 |
| 80 | A | **D** | 2:45:31 |
| 99 | C | **A** | 3:30:59 |
| **101** | A | **B** | 3:35:33 (user-reported; consult organization guidelines) |
| **104** | B & D | **B & C** | 3:42:20 (Choose 2 — video says “B and C”; PDF key was wrong) |
| 108 | C | **A** | 3:49:56 |
| 109 | C | **A** | 3:51:51 |
| 110 | B | **C** | 3:53:45 |
| 127 | B | **D** | 4:26:38 |
| 155 | A | **B** | 5:18:44 |

**Q128** — reverted to **A** (collaborative session). A prior `keyword_zone` run wrongly changed A→D; Andrew’s explanation @ 4:28:37 supports A. Pinned in `apply_video_answer_fixes.py` `MANUAL`.
| 183 | D | **C** | 6:09:25 |
| 185 | C | **A** | 6:13:02 (explicit in video) |
| 194 | B | **D** | 6:29:18 |
| 199 | D | **C** | 6:38:20 |

Updated: `pmp-mock-andrew.html`, `scripts/ar200_from_pdf.json`

## Audit scripts

- `extract_video_correct_answers.py` — scan VTT explanation segments vs stored answers
- `find_explanation_answer_mismatches.py` — explanation text vs stored `correct`
- `apply_video_answer_fixes.py` — apply high-confidence + manual overrides

Re-run audit:

```bash
python scripts/extract_video_correct_answers.py
python scripts/find_explanation_answer_mismatches.py
python scripts/apply_video_answer_fixes.py
```
