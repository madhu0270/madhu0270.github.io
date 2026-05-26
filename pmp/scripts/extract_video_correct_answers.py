"""Extract correct answers from YouTube explanation segments (authoritative over PDF)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PMP_ROOT = Path(__file__).resolve().parents[1]
HTML = PMP_ROOT / "pmp-mock-andrew.html"
VTT = PMP_ROOT / "scripts" / "yt_sub.en.vtt"
OUT = PMP_ROOT / "scripts" / "video_authoritative_answers.json"

sys.path.insert(0, str(Path(__file__).parent))
from sync_video_timestamps import build_timeline, extract_markers  # noqa: E402

LETTERS = "ABCDEF"
DURATION_SEC = 6 * 3600 + 42 * 60 + 21

ANSWER_ZONE_MARKERS = [
    "answer here is going to be",
    "answer is going to be",
    "answer here is",
    "correct answer is",
    "the answer is",
    "the answer will be",
    "so the answer",
    "answer would be",
]

EXPLICIT_LETTER = re.compile(
    r"\b(?:answer|correct|pick|choose|select|option|letter)\s+(?:is\s+)?(?:option\s+)?([a-e])\b",
    re.I,
)


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


def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def score_zone(zone: str, options: list[str]) -> list[int]:
    zone = zone[-280:]
    zone_words = set(zone.split())
    scores = [0] * len(options)
    for i, opt in enumerate(options):
        nopt = normalize(opt)
        for n in (50, 40, 35, 28):
            chunk = nopt[:n]
            if len(chunk) >= 16 and chunk in zone:
                scores[i] += 12
                break
        opt_words = [w for w in nopt.split() if len(w) >= 5]
        overlap = sum(1 for w in opt_words if w in zone_words)
        scores[i] += overlap * 4
        if "organization" in zone and any(
            w in nopt for w in ("guidelines", "policy", "policies", "governance", "consult")
        ):
            scores[i] += 10
        if re.search(r"organization\s+(wants|guidelines|policy|policies)", zone):
            if "organization" in nopt and any(
                w in nopt for w in ("guidelines", "consult", "policy", "policies")
            ):
                scores[i] += 15
        if "assessment" in zone and "assessment" in nopt and "exclusively" in nopt:
            scores[i] += 8
        for w in [w for w in nopt.split() if len(w) >= 8]:
            if w in zone:
                scores[i] += 3
    return scores


def infer_answer(segment: str, options: list[str]) -> tuple[int | None, int, str]:
    """Return (index, margin, method)."""
    seg = segment.lower()

    # 1) Explicit letter after answer markers
    zone = seg
    best_marker_pos = -1
    for marker in ANSWER_ZONE_MARKERS:
        p = seg.rfind(marker)
        if p > best_marker_pos:
            best_marker_pos = p
            zone = seg[p : p + 500]
    if best_marker_pos < 0:
        zone = seg[-800:]

    for m in EXPLICIT_LETTER.finditer(zone):
        letter = m.group(1).upper()
        if letter in LETTERS[: len(options)]:
            idx = LETTERS.index(letter)
            return idx, 99, "explicit_letter"

    scores = score_zone(zone, options)
    best = max(scores)
    second = sorted(scores, reverse=True)[1] if len(scores) > 1 else 0
    margin = best - second
    winners = [i for i, s in enumerate(scores) if s == best]
    if best >= 10 and margin >= 5 and len(winners) == 1:
        return winners[0], margin, "keyword_zone"
    return None, margin, "low_confidence"


def load_questions() -> list[dict]:
    text = HTML.read_text(encoding="utf-8")
    m = re.search(r"const QUESTIONS = (\[.*?\]);\s*\n\s*const PMP", text, re.DOTALL)
    return json.loads(m.group(1))


def build_segments(cues, times):
    segments = {}
    ids = sorted(times.keys())
    for idx, qid in enumerate(ids):
        start = float(times[qid])
        end = float(times[ids[idx + 1]]) if idx + 1 < len(ids) else float(DURATION_SEC)
        segments[qid] = " ".join(txt for t, txt in cues if start <= t < end)
    return segments


def main() -> None:
    questions = [q for q in load_questions() if "correct" in q]
    markers = extract_markers(VTT, 200, False)
    times = build_timeline(200, markers, DURATION_SEC)
    cues = parse_vtt_cues(VTT)
    segments = build_segments(cues, times)

    corrections: list[dict] = []
    for q in questions:
        qid = q["id"]
        seg = segments.get(qid, "")
        inferred, margin, method = infer_answer(seg, q["options"])
        if inferred is None or inferred == q["correct"]:
            continue
        corrections.append(
            {
                "id": qid,
                "from": LETTERS[q["correct"]],
                "to": LETTERS[inferred],
                "to_index": inferred,
                "margin": margin,
                "method": method,
                "videoTime": q.get("videoTime"),
                "text": q["text"][:80] + "...",
            }
        )

    OUT.write_text(json.dumps(corrections, indent=2), encoding="utf-8")
    print(f"High-confidence video corrections: {len(corrections)}")
    for c in corrections:
        print(
            f"Q{c['id']:3d} {c['from']}->{c['to']} margin={c['margin']} "
            f"{c['method']} ({c['videoTime']})"
        )


if __name__ == "__main__":
    main()
