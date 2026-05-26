"""Detect questions with PDF split corruption (stem in option A, truncated text)."""
from __future__ import annotations

import json
import re
from pathlib import Path

PMP_ROOT = Path(__file__).resolve().parents[1]
HTML = PMP_ROOT / "pmp-mock-andrew.html"

STEM_IN_OPTION = re.compile(
    r"what (?:is the most effective|should the project manager|is the best|would be the best|"
    r"are the project manager|can the project manager)",
    re.I,
)
QUESTION_END = re.compile(r"[?.!]\s*$")


def looks_truncated(s: str) -> bool:
    s = s.strip()
    if QUESTION_END.search(s):
        return False
    parts = s.split()
    if not parts:
        return False
    last = parts[-1].rstrip(".,;:")
    if len(last) <= 5 and last.isalpha():
        allow = {"first", "next", "when", "that", "with", "from", "into", "over", "under", "after", "before", "there", "where", "while", "which", "whose"}
        if last.lower() not in allow:
            return True
    return False


def load_questions() -> list[dict]:
    text = HTML.read_text(encoding="utf-8")
    m = re.search(r"const QUESTIONS = (\[.*?\]);\s*\n\s*const", text, re.S)
    if not m:
        raise RuntimeError("QUESTIONS not found")
    return json.loads(m.group(1))


def scan(qs: list[dict]) -> list[tuple[int, list[str], str, str]]:
    issues: list[tuple[int, list[str], str, str]] = []
    for q in qs:
        qid = q["id"]
        stem = q["text"]
        opts = q["options"]
        flags: list[str] = []

        if looks_truncated(stem):
            flags.append("truncated_stem")
        if len(opts) not in (4, 5):
            flags.append(f"option_count_{len(opts)}")
        if opts and STEM_IN_OPTION.search(opts[0]):
            flags.append("stem_in_option_A")
        if opts and opts[0].rstrip().endswith("?") and not stem.rstrip().endswith("?"):
            flags.append("question_sentence_in_option_A")
        if opts and len(opts[0]) > len(stem) * 1.1 and "?" in opts[0] and not stem.rstrip().endswith("?"):
            flags.append("option_A_holds_question")
        if q.get("correct") == 0 and opts and STEM_IN_OPTION.search(opts[0]):
            flags.append("correct_keyed_to_stem_option")

        if flags:
            issues.append((qid, flags, stem, opts[0] if opts else ""))
    return issues


def main() -> None:
    qs = load_questions()
    issues = scan(qs)
    print(f"Total questions: {len(qs)}")
    print(f"Suspicious: {len(issues)}\n")
    for qid, flags, stem, opt_a in sorted(issues):
        print(f"Q{qid}: {', '.join(flags)}")
        print(f"  stem: {stem[:100]}{'...' if len(stem) > 100 else ''}")
        if opt_a:
            print(f"  optA: {opt_a[:100]}{'...' if len(opt_a) > 100 else ''}")
        print()


if __name__ == "__main__":
    main()
