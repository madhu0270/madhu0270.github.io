"""Sync question videoSeconds/videoTime from YouTube captions."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PMP_ROOT = Path(__file__).resolve().parents[1]

CONFIGS = {
    "andrew": {
        "html": PMP_ROOT / "pmp-mock-andrew.html",
        "vtt": PMP_ROOT / "scripts" / "yt_sub.en.vtt",
        "video_id": "1sWpc6765AI",
        "duration_sec": 6 * 3600 + 42 * 60 + 21,
        "max_q": 200,
        "questions_after": "const PMP",
    },
    "mindset": {
        "html": PMP_ROOT / "pmp-mock-mindset.html",
        "vtt": PMP_ROOT / "scripts" / "yt_sub_mindset.en.vtt",
        "video_id": "-u0rO-YQr9c",
        "duration_sec": 2 * 3600 + 53 * 60 + 56,
        "max_q": 50,
        "questions_after": "const EXAM_CONFIG",
    },
}

WORD_NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}


def hms_to_seconds(h: str, m: str, s: str, ms: str = "0") -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms[:3]) / 1000.0


def format_video_time(seconds: int) -> str:
    h, rem = divmod(max(0, seconds), 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


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


def extract_markers(path: Path, max_q: int, mindset: bool) -> dict[int, float]:
    raw = path.read_text(encoding="utf-8")
    found: dict[int, float] = {}

    def record(qnum: int, sec: float) -> None:
        if 1 <= qnum <= max_q and (qnum not in found or sec < found[qnum]):
            found[qnum] = sec

    for start, plain in parse_vtt_cues(path):
        for m in re.finditer(r"question\s+number\s+(\d{1,3})\b", plain):
            record(int(m.group(1)), start)
        for m in re.finditer(
            r"question\s+number\s+(" + "|".join(WORD_NUMBERS) + r")\b",
            plain,
        ):
            record(WORD_NUMBERS[m.group(1)], start)
        for m in re.finditer(
            r"practice\s+question\s+number\s+(\d{1,3})\b",
            plain,
        ):
            record(int(m.group(1)), start)
        for m in re.finditer(
            r"question\s+(?:number\s+)?(\d{1,3})\s+(?:a|an|the|during|at|by|in|on|for|as)\b",
            plain,
        ):
            record(int(m.group(1)), start)
        for m in re.finditer(
            r"(?:let'?s\s+go|guys|answer|video|time|experts|perspectives)\s+question\s+(\d{1,3})\b",
            plain,
        ):
            record(int(m.group(1)), start)
        for m in re.finditer(r"up\s+to\s+question\s+(\d{1,3})\b", plain):
            record(int(m.group(1)), start)
        for m in re.finditer(r"all\s+right\s+(\d{1,3})\s+(?:a|during)\b", plain):
            record(int(m.group(1)), start)
        if mindset:
            for m in re.finditer(r"principle\s+number\s+(\d{1,3})\b", plain):
                record(int(m.group(1)), start)
            for m in re.finditer(r"principle\s+(\d{1,3})\b", plain):
                record(int(m.group(1)), start)
            for m in re.finditer(
                r"question\s+and\s+principle\s+(\d{1,3})\b",
                plain,
            ):
                record(int(m.group(1)), start)
            for m in re.finditer(
                r"next\s+principle\s+principle\s+(\d{1,3})\b",
                plain,
            ):
                record(int(m.group(1)), start)

    for line in raw.splitlines():
        if "<c>" not in line:
            continue
        for m in re.finditer(
            r"(?:^|>|\s)(\d{1,3})<(\d{2}):(\d{2}):(\d{2})\.(\d{3})><c>\s*a\s*</c><\d{2}:\d{2}:\d{2}\.\d{3}><c>\s*project\b",
            line,
            re.I,
        ):
            qnum = int(m.group(1))
            if qnum <= max_q:
                sec = hms_to_seconds(m.group(2), m.group(3), m.group(4), m.group(5))
                record(qnum, sec)

    cues = parse_vtt_cues(path)
    for i, (start, plain) in enumerate(cues):
        if not re.search(r"question\s+number\s*$", plain):
            continue
        if i + 1 >= len(cues):
            continue
        nxt = cues[i + 1][1].strip()
        wm = re.match(r"^(" + "|".join(WORD_NUMBERS) + r")\b", nxt)
        if wm and WORD_NUMBERS[wm.group(1)] <= max_q:
            record(WORD_NUMBERS[wm.group(1)], start)

    return found


def build_timeline(
    max_q: int, markers: dict[int, float], duration_sec: int
) -> dict[int, int]:
    anchor = dict(markers)
    anchor_ids = sorted(anchor.keys())
    if not anchor_ids:
        raise RuntimeError("No caption anchors found")

    times: dict[int, float] = {}
    for qid in range(1, max_q + 1):
        if qid in anchor:
            times[qid] = anchor[qid]
            continue
        prev_id = max((i for i in anchor_ids if i < qid), default=None)
        next_id = min((i for i in anchor_ids if i > qid), default=None)
        if prev_id is not None and next_id is not None:
            span = next_id - prev_id
            times[qid] = anchor[prev_id] + (anchor[next_id] - anchor[prev_id]) * (qid - prev_id) / span
        elif prev_id is not None:
            times[qid] = anchor[prev_id] + 90.0
        else:
            times[qid] = max(0.0, anchor[next_id] - 90.0 * (next_id - qid))

    last = 0.0
    out: dict[int, int] = {}
    for qid in range(1, max_q + 1):
        sec = max(times[qid], last + 2)
        sec = min(sec, float(duration_sec - 30))
        out[qid] = int(round(sec))
        last = sec
    return out


def patch_html(
    html_path: Path,
    times: dict[int, int],
    video_id: str,
    questions_after: str,
) -> None:
    text = html_path.read_text(encoding="utf-8")
    m = re.search(
        rf"(const QUESTIONS = )(\[.*?\])(;\s*\n\s*{re.escape(questions_after)})",
        text,
        re.DOTALL,
    )
    if not m:
        raise RuntimeError("QUESTIONS array not found")
    questions = json.loads(m.group(2))
    for q in questions:
        qid = q["id"]
        sec = times[qid]
        q["videoSeconds"] = sec
        q["videoTime"] = format_video_time(sec)
        q["videoId"] = video_id
        q["videoUrl"] = f"https://www.youtube.com/watch?v={video_id}&t={sec}s"
    new_json = json.dumps(questions, ensure_ascii=False, separators=(",", ":"))
    html_path.write_text(text[: m.start(2)] + new_json + text[m.end(2) :], encoding="utf-8")


def run(exam: str) -> None:
    cfg = CONFIGS[exam]
    if not cfg["vtt"].exists():
        raise SystemExit(f"Missing subtitles: {cfg['vtt']}")

    markers = extract_markers(cfg["vtt"], cfg["max_q"], exam == "mindset")
    times = build_timeline(cfg["max_q"], markers, cfg["duration_sec"])
    patch_html(cfg["html"], times, cfg["video_id"], cfg["questions_after"])

    print(f"[{exam}] Caption anchors: {len(markers)}")
    sample = [1, 5, 10, 26, 50] if exam == "mindset" else [1, 5, 14, 26, 50, 100, 200]
    for qid in sample:
        if qid <= cfg["max_q"]:
            print(f"  Q{qid}: {format_video_time(times[qid])} ({times[qid]}s)")
    print(f"Patched {cfg['html'].name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--exam",
        choices=("andrew", "mindset", "all"),
        default="andrew",
        help="Which mock exam to sync (default: andrew)",
    )
    args = parser.parse_args()
    if args.exam == "all":
        run("andrew")
        run("mindset")
    else:
        run(args.exam)


if __name__ == "__main__":
    main()
