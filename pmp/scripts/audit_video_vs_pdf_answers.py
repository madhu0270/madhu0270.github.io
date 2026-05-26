"""Find Andrew exam questions where PDF answer differs from YouTube explanation."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PMP_ROOT = Path(__file__).resolve().parents[1]
HTML = PMP_ROOT / "pmp-mock-andrew.html"
PDF_JSON = PMP_ROOT / "scripts" / "ar200_from_pdf.json"
VTT = PMP_ROOT / "scripts" / "yt_sub.en.vtt"
VIDEO_ID = "1sWpc6765AI"
DURATION_SEC = 6 * 3600 + 42 * 60 + 21

# Import timeline helpers from sync script
sys.path.insert(0, str(Path(__file__).parent))
from sync_video_timestamps import (  # noqa: E402
    build_timeline,
    extract_markers,
    format_video_time,
)

LETTERS = "ABCDEF"

ANSWER_PATTERNS = [
    re.compile(r"\banswer\s+(?:here\s+)?(?:is\s+)?(?:going\s+to\s+be\s+)?(?:option\s+)?([a-e])\b", re.I),
    re.compile(r"\bcorrect\s+answer\s+(?:is\s+)?(?:option\s+)?([a-e])\b", re.I),
    re.compile(r"\bthe\s+answer\s+(?:is\s+)?(?:option\s+)?([a-e])\b", re.I),
    re.compile(r"\b(?:pick|choose|select)\s+(?:option\s+)?([a-e])\b", re.I),
    re.compile(r"\boption\s+([a-e])\s+(?:is\s+)?(?:correct|right)\b", re.I),
    re.compile(r"\bletter\s+([a-e])\b", re.I),
    re.compile(r"\b(?:it'?s|its)\s+([a-e])\b", re.I),
]


def hms_to_seconds(h: str, m: str, s: str, ms: str = "0") -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms[:3]) / 1000.0


def parse_vtt_cues(path: Path) -> list[tuple[float, str]]:
    raw = path.read_text(encoding="utf-8")
    cues: list[tuple[float, str]] = []
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(
            r"^(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s+-->\s+(\d{2}):(\d{2}):(\d{2})\.(\d{3})",
            lines[i],
        )
        if m:
            start = hms_to_seconds(m.group(1), m.group(2), m.group(3), m.group(4))
            i += 1
            parts: list[str] = []
            while i < len(lines) and lines[i].strip() and not re.match(
                r"^\d{2}:\d{2}:\d{2}\.\d{3}\s+-->", lines[i]
            ):
                parts.append(lines[i])
                i += 1
            blob = " ".join(parts)
            plain = re.sub(r"<[^>]+>", " ", blob)
            plain = re.sub(r"\s+", " ", plain).strip().lower()
            if plain:
                cues.append((start, plain))
            continue
        i += 1
    return cues


def load_questions() -> list[dict]:
    text = HTML.read_text(encoding="utf-8")
    m = re.search(
        r"const QUESTIONS = (\[.*?\]);\s*\n\s*const PMP",
        text,
        re.DOTALL,
    )
    if not m:
        raise RuntimeError("QUESTIONS not found")
    return json.loads(m.group(1))


def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def option_keywords(opt: str, min_len: int = 5) -> list[str]:
    words = [w for w in normalize(opt).split() if len(w) >= min_len]
    # prefer distinctive phrases
    phrases = []
    n = normalize(opt)
    if len(n) >= 12:
        phrases.append(n[:40])
    for w in words[:6]:
        phrases.append(w)
    return phrases


def infer_from_transcript(segment: str, options: list[str]) -> int | None:
    """Return 0-based index if video segment strongly indicates an option."""
    seg = segment.lower()

    # Explicit letter patterns (late in segment = explanation portion)
    tail = seg[-2500:] if len(seg) > 2500 else seg
    for pat in ANSWER_PATTERNS:
        hits = pat.findall(tail)
        if hits:
            letter = hits[-1].upper()
            if letter in LETTERS[: len(options)]:
                return LETTERS.index(letter)

    # Keyword scoring on explanation tail (after options read aloud)
    scores = [0] * len(options)
    for i, opt in enumerate(options):
        for kw in option_keywords(opt):
            if len(kw) >= 8 and kw in tail:
                scores[i] += 3
            elif kw in tail:
                scores[i] += 1

    # Phrases tied to "answer" discussion
    answer_zone = tail
    for marker in (
        "answer here",
        "answer is going",
        "correct answer",
        "the answer",
        "going to be",
    ):
        idx = answer_zone.rfind(marker)
        if idx >= 0:
            answer_zone = answer_zone[idx:]
            break

    for i, opt in enumerate(options):
        core = normalize(opt)[:35]
        if core and core in answer_zone:
            scores[i] += 5

    best = max(scores) if scores else 0
    if best < 4:
        return None
    winners = [i for i, s in enumerate(scores) if s == best]
    if len(winners) != 1:
        return None
    return winners[0]


def infer_from_explanation(explanation: str, options: list[str]) -> int | None:
    if not explanation:
        return None
    exp = normalize(explanation)
    scores = [0] * len(options)
    for i, opt in enumerate(options):
        core = normalize(opt)
        if len(core) >= 15 and core[:30] in exp:
            scores[i] += 4
        for kw in option_keywords(opt, min_len=6):
            if kw in exp:
                scores[i] += 2
    best = max(scores) if scores else 0
    if best < 4:
        return None
    winners = [i for i, s in enumerate(scores) if s == best]
    return winners[0] if len(winners) == 1 else None


def build_segments(cues: list[tuple[float, str]], times: dict[int, int]) -> dict[int, str]:
    """Map question id -> transcript text from videoSeconds to next question."""
    segments: dict[int, str] = {}
    sorted_ids = sorted(times.keys())
    for idx, qid in enumerate(sorted_ids):
        start = float(times[qid])
        end = float(times[sorted_ids[idx + 1]]) if idx + 1 < len(sorted_ids) else float(DURATION_SEC)
        parts = [text for t, text in cues if start <= t < end]
        segments[qid] = " ".join(parts)
    return segments


def main() -> None:
    questions = load_questions()
    pdf_by_id = {q["id"]: q for q in json.loads(PDF_JSON.read_text(encoding="utf-8"))}
    markers = extract_markers(VTT, 200, False)
    times = build_timeline(200, markers, DURATION_SEC)
    cues = parse_vtt_cues(VTT)
    segments = build_segments(cues, times)

    mismatches: list[dict] = []

    for q in questions:
        qid = q["id"]
        if "correct" not in q:
            continue  # multi-select (correctIndices)
        pdf_correct = pdf_by_id.get(qid, {}).get("correct")
        html_correct = q["correct"]
        opts = q["options"]
        seg = segments.get(qid, "")
        video_idx = infer_from_transcript(seg, opts)
        expl_idx = infer_from_explanation(q.get("explanation", ""), opts)

        # Prefer transcript; fall back to explanation if it disagrees with PDF
        inferred = video_idx if video_idx is not None else expl_idx
        if inferred is None:
            continue
        if inferred == html_correct:
            continue
        # Only flag when PDF also disagrees with video, or explanation agrees with video
        pdf_agrees_html = pdf_correct == html_correct
        expl_agrees_video = expl_idx is not None and expl_idx == inferred
        if pdf_agrees_html and not expl_agrees_video and video_idx is None:
            continue

        mismatches.append(
            {
                "id": qid,
                "html": LETTERS[html_correct],
                "pdf": LETTERS[pdf_correct] if pdf_correct is not None else "?",
                "video": LETTERS[inferred],
                "video_time": q.get("videoTime"),
                "text": q["text"][:90] + "...",
                "video_idx": inferred,
                "source": "transcript" if video_idx == inferred else "explanation",
            }
        )

    print(f"Potential video/PDF mismatches: {len(mismatches)}\n")
    for m in mismatches:
        print(
            f"Q{m['id']:3d}  HTML={m['html']} PDF={m['pdf']} VIDEO={m['video']} "
            f"({m['source']}, {m['video_time']})"
        )
        print(f"       {m['text']}\n")

    out = PMP_ROOT / "scripts" / "video_pdf_mismatches.json"
    out.write_text(json.dumps(mismatches, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
