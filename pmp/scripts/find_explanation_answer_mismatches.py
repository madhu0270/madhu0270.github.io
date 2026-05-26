"""Find questions where explanation text implies a different answer than `correct`."""
from __future__ import annotations

import json
import re
from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / "pmp-mock-andrew.html"
LETTERS = "ABCDEF"


def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_questions() -> list[dict]:
    text = HTML.read_text(encoding="utf-8")
    m = re.search(r"const QUESTIONS = (\[.*?\]);\s*\n\s*const PMP", text, re.DOTALL)
    return json.loads(m.group(1))


def score_explanation(explanation: str, options: list[str]) -> list[int]:
    exp = normalize(explanation)
    # focus on answer-reveal portion
    for marker in (
        "answer here",
        "answer is going",
        "correct answer",
        "the answer",
        "answer will be",
        "answer would be",
        "so the answer",
    ):
        i = exp.rfind(marker)
        if i >= 0:
            exp = exp[i:]
            break

    scores = [0] * len(options)
    for i, opt in enumerate(options):
        nopt = normalize(opt)
        # long phrase match
        for length in (50, 40, 30, 20):
            chunk = nopt[:length]
            if len(chunk) >= 18 and chunk in exp:
                scores[i] += 8
                break
        # distinctive words
        words = [w for w in nopt.split() if len(w) >= 7]
        for w in words[:8]:
            if w in exp:
                scores[i] += 2
    return scores


def main() -> None:
    questions = load_questions()
    hits = []
    for q in questions:
        if "correct" not in q:
            continue
        exp = q.get("explanation") or ""
        if len(exp) < 80:
            continue
        scores = score_explanation(exp, q["options"])
        best = max(scores)
        if best < 6:
            continue
        winners = [i for i, s in enumerate(scores) if s == best]
        if len(winners) != 1:
            continue
        inferred = winners[0]
        if inferred == q["correct"]:
            continue
        hits.append(
            {
                "id": q["id"],
                "stored": LETTERS[q["correct"]],
                "inferred": LETTERS[inferred],
                "videoTime": q.get("videoTime"),
                "text": q["text"][:85] + "...",
                "inferred_idx": inferred,
                "scores": scores,
            }
        )

    print(f"Explanation vs stored correct mismatches: {len(hits)}\n")
    for h in sorted(hits, key=lambda x: x["id"]):
        print(
            f"Q{h['id']:3d} stored={h['stored']} explanation->{h['inferred']} "
            f"({h['videoTime']}) scores={h['scores']}"
        )
        print(f"     {h['text']}\n")

    out = Path(__file__).parent / "explanation_mismatches.json"
    out.write_text(json.dumps(hits, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
