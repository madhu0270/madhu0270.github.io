"""Fix PDF/OCR spacing and typos in PMP mock question text (and optional explanations)."""
from __future__ import annotations

import argparse
import json
import re
import urllib.request
from pathlib import Path

PMP_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HTML = PMP_ROOT / "pmp-mock-andrew.html"
ALL_MOCKS = [
    PMP_ROOT / "pmp-mock-andrew.html",
    PMP_ROOT / "pmp-mock-david.html",
    PMP_ROOT / "pmp-mock-mindset.html",
]

# Top-frequency English words (difficulty, organize, etc.) — excludes obscure 3-letter entries like "dif"
COMMON_WORDS_URL = (
    "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english.txt"
)


def load_common_words() -> set[str]:
    raw = urllib.request.urlopen(COMMON_WORDS_URL, timeout=30).read().decode("utf-8")
    words = {w.strip().lower() for w in raw.splitlines() if w.strip()}
    # Add PMP / project-management terms often missing from general lists
    words.update(
        {
            "stakeholder",
            "stakeholders",
            "backlog",
            "sprint",
            "sprints",
            "kanban",
            "scrum",
            "agile",
            "waterfall",
            "deliverable",
            "deliverables",
            "procurement",
            "charter",
            "roadmap",
            "workflow",
            "workflows",
            "onboarding",
            "offboarding",
            "escalation",
            "retrospective",
            "increment",
            "incremental",
            "difficulty",
            "difficulties",
            "effective",
            "effectively",
            "efficiency",
            "effort",
            "efforts",
            "organize",
            "organizes",
            "organized",
            "organizing",
            "affect",
            "affects",
            "affected",
            "affecting",
            "staff",
            "emergency",
            "emergencies",
            "targeted",
            "performance",
            "requirements",
            "implementation",
            "communication",
            "communications",
            "collaboration",
            "collaborative",
            "regulatory",
            "compliance",
            "mitigation",
            "contingency",
            "authorization",
            "prioritization",
            "prioritizing",
            "facilitate",
            "facilitates",
            "facilitated",
            "facilitating",
            "differentiate",
            "differentiates",
            "differentiated",
            "differences",
            "difference",
            "differs",
            "differ",
            "synergy",
            "officials",
            "official",
            "traffic",
            "emerged",
            "emerge",
            "emerges",
            "emerging",
        }
    )
    return words


COMMON: set[str] | None = None

# Short words that must stay separate (do not merge "with the", etc.)
SHORT_STANDALONE = {
    "a",
    "an",
    "as",
    "at",
    "be",
    "by",
    "do",
    "go",
    "he",
    "if",
    "in",
    "is",
    "it",
    "me",
    "my",
    "no",
    "of",
    "on",
    "or",
    "so",
    "to",
    "up",
    "us",
    "we",
    "am",
    "the",
    "and",
    "for",
    "are",
    "but",
    "not",
    "you",
    "all",
    "can",
    "had",
    "her",
    "was",
    "one",
    "our",
    "out",
    "get",
    "has",
    "him",
    "his",
    "how",
    "its",
    "may",
    "new",
    "now",
    "old",
    "see",
    "two",
    "way",
    "who",
    "did",
    "own",
    "say",
    "she",
    "too",
    "use",
    "any",
    "set",
    "per",
    "via",
    "yet",
}

# Explicit fixes for garbled PDF output (order matters for some)
EXPLICIT_SUBS = [
    (r"\s+\.\s+", ". "),  # "library . The" -> "library. The"
    (r"\s+,", ","),
    (r"\s+;", ";"),
    (r"\s+:", ":"),
    (r"\bproject'\s+s\b", "project's"),
    (r"\bproject\s+'\s*s\b", "project's"),
    (r"\{Choose", "(Choose"),
    (r"Choose two\.\)", "Choose two.)"),
    (r"\bL\s+What\b", "What"),
    (r"\bro\.\s*", ""),
    (r"SeqUENCi\s*ji\b", "sequence"),
    (r"\bur\s+gent\b", "urgent"),
    (r"\bman\s+ager\b", "manager"),
    (r"\bman\s+agement\b", "management"),
    (r"\borgan\s+ize\b", "organize"),
    (r"\borgan\s+ized\b", "organized"),
    (r"\ban Al\b", "an AI"),
    (r"\bAl-based\b", "AI-based"),
    (r"\bAl technology\b", "AI technology"),
    (r"\bAl\b", "AI"),
    (r"\bdif\s+ficult\b", "difficult"),
    (r"\bef\s+ficacy\b", "efficacy"),
    (r"\bnotices pattern\b", "notices a pattern"),
    (r"\boverseeing\s+software development project\b", "overseeing a software development project"),
    (r"\bcreating\s+new user authentication\b", "creating a new user authentication"),
    (r"\bexpress desire to\b", "express a desire to"),
    (r"\breceive request from\b", "receive a request from"),
    (r"\bwith Organizing\b", "with organizing"),
    (r"\btasked with Organizing\b", "tasked with organizing"),
    (r"\s+L\s*$", ""),
    (r"'\s+s\b", "'s"),
    (r"\s+8\.\s+Collaborate", " B. Collaborate"),  # Q77-style typo if present in stem
    (r"kick-of\s+f\b", "kick-off"),
    (r"\bkickof\s+f\b", "kickoff"),
    (r"\bkicks\s+of\s+f\b", "kicks off"),
    (r"\bcooling-of\s+f\b", "cooling-off"),
    (r"\bof\s+fshore\b", "offshore"),
    (r"\bof\s+f-guard\b", "off-guard"),
    (r"\bof\s+f\s+guard\b", "off guard"),
    (r"\bcaught\s+of\s+f\s+guard\b", "caught off guard"),
    (r"\bgo\s+of\s+f-course\b", "go off-course"),
    (r"\bface\s+toof\s+face\b", "face-to-face"),
    (r"\btoof\s+face\b", "to-face"),
    (r"\bor\s+ganizers\b", "organizers"),
    (r"\bor\s+ganizer\b", "organizer"),
    (r"face-\s+to-face", "face-to-face"),
    (r"sign-\s+off", "sign-off"),
    (r"follow-\s+up", "follow-up"),
    (r"check-\s+in", "check-in"),
    (r"well-\s+being", "well-being"),
    (r"decision-\s+making", "decision-making"),
    (r"cross-\s+functional", "cross-functional"),
    (r"long-\s+term", "long-term"),
    (r"short-\s+term", "short-term"),
    (r"mid-\s+year", "mid-year"),
    (r"end-\s+of", "end-of"),
    (r"real-\s+time", "real-time"),
    (r"high-\s+priority", "high-priority"),
    (r"low-\s+priority", "low-priority"),
    (r"best-\s+practice", "best-practice"),
    (r"state-\s+of-the-art", "state-of-the-art"),
    (r"  +", " "),
]

# Syllable fragments PDF often splits (fragment -> full word without space)
FRAGMENT_JOINS = {
    "dif": "difficulty",
    "ef": None,  # handled by iterative join
    "af": None,
    "Or": None,
    "staf": "staff",
    "emer": "emergency",
    "gani": None,
    "char": "charge",
    "perf": None,
    "conf": None,
    "comm": None,
    "deliv": None,
    "envi": None,
    "regul": None,
    "proc": None,
    "requ": None,
    "sched": None,
    "manag": None,
    "devel": None,
    "imple": None,
    "integr": None,
    "collab": None,
    "stake": None,
    "tar": "target",
    "geted": None,
}


def get_common() -> set[str]:
    global COMMON
    if COMMON is None:
        COMMON = load_common_words()
    return COMMON


def fix_internal_breaks(text: str) -> str:
    """Join 'dif ficulty' -> 'difficulty' when the join is a common word."""
    common = get_common()

    def repl(m: re.Match[str]) -> str:
        a, b = m.group(1), m.group(2)
        al = a.lower()
        # Keep real short words and longer standalone words separate
        if al in SHORT_STANDALONE:
            return m.group(0)
        if len(al) >= 4 and al in common:
            return m.group(0)
        combo = a + b
        cl = combo.lower()
        if cl not in common:
            return m.group(0)
        if a[0].isupper():
            return combo[0].upper() + combo[1:]
        return combo

    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\b([A-Za-z]{1,4})\s+([a-z]{2,})\b", repl, text)
    return text


def fix_hyphenation_breaks(text: str) -> str:
    """Join hyphenated syllable breaks: 'kick-of f' -> 'kick-off'."""
    return re.sub(
        r"(\w)-([a-z]{1,3})\s+([a-z]{2,})\b",
        lambda m: (
            m.group(1) + "-" + m.group(2) + m.group(3)
            if (m.group(1) + "-" + m.group(2) + m.group(3)).lower()
            in get_common()
            else m.group(0)
        ),
        text,
    )


def apply_pdf_word_fixes(text: str) -> str:
    """Join known PDF split words (ef fort, dif ficulty, of ficials, …)."""
    rules = [
        (r"\bof\s+ficials\b", "officials"),
        (r"\bof\s+ficial\b", "official"),
        (r"\btraf\s+fic\b", "traffic"),
        (r"\bsyner\s+gy\b", "synergy"),
        (r"\bemer\s+ged\b", "emerged"),
        (r"\bemer\s+ging\b", "emerging"),
        (r"\bemer\s+ges\b", "emerges"),
        (r"\bemer\s+ge\b", "emerge"),
        (r"\bemer\s+gency\b", "emergency"),
        (r"\baf\s+fecting\b", "affecting"),
        (r"\baf\s+fected\b", "affected"),
        (r"\baf\s+fects\b", "affects"),
        (r"\baf\s+fect\b", "affect"),
        (r"\bef\s+forts\b", "efforts"),
        (r"\bef\s+fort\b", "effort"),
        (r"\bef\s+fectively\b", "effectively"),
        (r"\bef\s+fective\b", "effective"),
        (r"\bef\s+ficiencies\b", "efficiencies"),
        (r"\bef\s+ficiency\b", "efficiency"),
        (r"\bef\s+iciency\b", "efficiency"),
        (r"\bdif\s+ferentiate\b", "differentiate"),
        (r"\bdif\s+ferentiated\b", "differentiated"),
        (r"\bdif\s+ferences\b", "differences"),
        (r"\bdif\s+ference\b", "difference"),
        (r"\bdif\s+fers\b", "differs"),
        (r"\bdif\s+fer\b", "differ"),
        (r"\bdif\s+ficulty\b", "difficulty"),
        (r"\bOr\s+ganize\b", "Organize"),
        (r"\bOr\s+ganizes\b", "Organizes"),
        (r"\bOr\s+ganized\b", "Organized"),
        (r"\bOr\s+ganizing\b", "Organizing"),
        (r"\bOr\s+ganization\b", "Organization"),
        (r"\bchar\s+ge\b", "charge"),
        (r"\bstaf\s+f\b", "staff"),
        (r"\bperf\s+ormance\b", "performance"),
        (r"\bperf\s+orm\b", "perform"),
        (r"\bconf\s+lict\b", "conflict"),
        (r"\bconf\s+licts\b", "conflicts"),
        (r"\bcomm\s+unication\b", "communication"),
        (r"\bdeliv\s+erable\b", "deliverable"),
        (r"\bdeliv\s+erables\b", "deliverables"),
        (r"\bsched\s+ule\b", "schedule"),
        (r"\bsched\s+ules\b", "schedules"),
        (r"\bimple\s+ment\b", "implement"),
        (r"\bimple\s+mentation\b", "implementation"),
        (r"\bintegr\s+ation\b", "integration"),
        (r"\bintegr\s+ate\b", "integrate"),
        (r"\bregul\s+atory\b", "regulatory"),
        (r"\bproc\s+urement\b", "procurement"),
        (r"\brequire\s+ments\b", "requirements"),
        (r"\brequire\s+ment\b", "requirement"),
        (r"\btar\s+geted\b", "targeted"),
        (r"\btar\s+get\b", "target"),
        (r"\benviron\s+mental\b", "environmental"),
        (r"\benviron\s+ment\b", "environment"),
        (r"\blar\s+ge\b", "large"),
        (r"\blar\s+ger\b", "larger"),
        (r"\blar\s+gest\b", "largest"),
        (r"\bof\s+ficers\b", "officers"),
        (r"\bof\s+ficer\b", "officer"),
        (r"\bof\s+fice\b", "office"),
        (r"\bof\s+fer\b", "offer"),
        (r"\bof\s+fers\b", "offers"),
        (r"\bof\s+fered\b", "offered"),
        (r"\bof\s+fering\b", "offering"),
        (r"\bor\s+ganizational\b", "organizational"),
        (r"\bor\s+ganisation\b", "organisation"),
        (r"\bor\s+ganize\b", "organize"),
        (r"\bor\s+ganized\b", "organized"),
        (r"\bor\s+ganizing\b", "organizing"),
        (r"\bor\s+ganization\b", "organization"),
        (r"\bdif\s+ferent\b", "different"),
        (r"\bdif\s+ferently\b", "differently"),
        (r"\bef\s+fectiveness\b", "effectiveness"),
        (r"\ban\s+alysis\b", "analysis"),
        (r"\ban\s+alyses\b", "analyses"),
    ]
    for pat, rep in rules:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)
    return text


def cleanup_string(s: str) -> str:
    if not s or not isinstance(s, str):
        return s
    s = s.replace("\u2019", "'").replace("\ufffd", "'")
    for pat, rep in EXPLICIT_SUBS:
        s = re.sub(pat, rep, s)
    s = apply_pdf_word_fixes(s)
    s = fix_hyphenation_breaks(s)
    s = fix_internal_breaks(s)
    s = re.sub(r"  +", " ", s).strip()
    # Space before punctuation cleanup
    s = re.sub(r"\s+([.,;:!?])", r"\1", s)
    s = re.sub(r"([.,;:!?])([A-Za-z])", r"\1 \2", s)
    return s.strip()


def cleanup_question(q: dict, *, include_explanations: bool = False) -> dict:
    q = dict(q)
    q["text"] = cleanup_string(q.get("text", ""))
    q["options"] = [cleanup_string(o) for o in q.get("options", [])]
    if include_explanations:
        if q.get("explanation"):
            q["explanation"] = cleanup_string(q["explanation"])
        if q.get("principle"):
            q["principle"] = cleanup_string(q["principle"])
    return q


def load_questions(html_path: Path) -> tuple[list[dict], str, re.Match[str]]:
    text = html_path.read_text(encoding="utf-8")
    m = re.search(r"(const QUESTIONS = )(\[.*?\])(;\s*\n)", text, re.DOTALL)
    if not m:
        raise SystemExit(f"QUESTIONS array not found in {html_path}")
    return json.loads(m.group(2)), text, m


def collect_fields(q: dict, include_explanations: bool) -> list[str]:
    fields = [q["text"], *q.get("options", [])]
    if include_explanations:
        if q.get("explanation"):
            fields.append(q["explanation"])
        if q.get("principle"):
            fields.append(q["principle"])
    return fields


def process_html(html_path: Path, include_explanations: bool = False) -> None:
    qs, full_text, m = load_questions(html_path)
    cleaned = [cleanup_question(q, include_explanations=include_explanations) for q in qs]

    suspicious = []
    for q in cleaned:
        for field in collect_fields(q, include_explanations):
            for match in re.finditer(
                r"\b([a-z]{2,3})\s+([a-z]{3,})\b", field, re.IGNORECASE
            ):
                a = match.group(1).lower()
                combo = (match.group(1) + match.group(2)).lower()
                if a not in get_common() and combo not in get_common():
                    suspicious.append((q["id"], match.group(0)))

    new_json = json.dumps(cleaned, ensure_ascii=False, separators=(",", ":"))
    new_text = full_text[: m.start(2)] + new_json + full_text[m.end(2) :]
    html_path.write_text(new_text, encoding="utf-8")

    scope = "questions, options" + (", explanations" if include_explanations else "")
    print(f"Cleaned {len(cleaned)} items ({scope}) in {html_path.name}")
    print(f"  Remaining uncommon split patterns: {len(suspicious)}")
    for item in suspicious[:15]:
        print(f"    Q{item[0]}: {item[1]!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean PDF/OCR typos in PMP mock HTML files.")
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Mock HTML file(s) under pmp/ (default: pmp-mock-andrew.html)",
    )
    parser.add_argument(
        "--all-mocks",
        action="store_true",
        help="Process Andrew, David, and Mindset mocks",
    )
    parser.add_argument(
        "--explanations",
        action="store_true",
        help="Also clean explanation and principle text",
    )
    args = parser.parse_args()

    if args.all_mocks:
        targets = ALL_MOCKS
    elif args.files:
        targets = [f if f.is_absolute() else PMP_ROOT / f for f in args.files]
    else:
        targets = [DEFAULT_HTML]

    for html_path in targets:
        if not html_path.exists():
            raise SystemExit(f"File not found: {html_path}")
        process_html(html_path, include_explanations=args.explanations)


if __name__ == "__main__":
    main()
