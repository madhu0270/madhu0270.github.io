"""Add shared theme toggle to PMP HTML files."""
from pathlib import Path

PMP = Path(__file__).resolve().parents[1]
FILES = [
    PMP / "pmp-mock-andrew.html",
    PMP / "pmp-mock-david.html",
    PMP / "pmp-mock-mindset.html",
    PMP / "index.html",
]

HEAD_INJECT = """  <script>
    (function () {
      var t = localStorage.getItem("pmp-mock-theme");
      if (t === "light" || t === "dark") document.documentElement.setAttribute("data-theme", t);
    })();
  </script>
  <link rel="stylesheet" href="pmp-theme.css" />
"""

ROOT_BLOCK = """    :root {
      --bg: #0f1419;
      --surface: #1a2332;
      --surface2: #243044;
      --text: #e8eef4;
      --muted: #8b9cb3;
      --accent: #3b82f6;
      --accent-hover: #2563eb;
      --success: #22c55e;
      --danger: #ef4444;
      --warning: #f59e0b;
      --border: #334155;
    }
"""

REPLACEMENTS = [
    ("#1e3a5f", "var(--accent-soft)"),
    ("#2d3d52", "var(--btn-secondary-hover)"),
    ("#14532d33", "var(--success-soft)"),
    ("#14532d55", "var(--success-soft-solid)"),
    ("#14532d44", "var(--success-hero)"),
    ("#bbf7d0", "var(--success-text)"),
    ("#7f1d1d33", "var(--danger-soft)"),
    ("#7f1d1d55", "var(--danger-soft-solid)"),
    ("#7f1d1d44", "var(--danger-hero)"),
    ("#fecaca", "var(--danger-text)"),
    ("#fca5a5", "var(--danger-outline)"),
    ("rgba(15, 20, 25, 0.85)", "var(--overlay)"),
    ("rgba(15, 20, 25, 0.9)", "var(--overlay-strong)"),
    ("rgba(59, 130, 246, 0.08)", "var(--accent-soft-alpha)"),
    ("rgba(59, 130, 246, 0.12)", "var(--accent-badge-alpha)"),
    ("rgba(34, 197, 94, 0.15)", "var(--success-status-bg)"),
    ("rgba(234, 179, 8, 0.15)", "var(--warning-status-bg)"),
]

HEADER_OLD_EXAM = """    <div class="header-stats" id="headerStats" hidden>"""

HEADER_NEW_EXAM = """    <div class="header-end">
      <div class="header-stats" id="headerStats" hidden>"""

HEADER_CLOSE_EXAM = """      <span id="saveStatus" class="save-status" hidden aria-live="polite">Saved</span>
    </div>
  </header>"""

# Andrew/David have saveStatus line - need to find exact close pattern

THEME_BTN = """      <button type="button" class="theme-toggle" id="themeToggle" aria-label="Switch to light mode" title="Light mode">&#9728;</button>
    </div>
  </header>"""

SCRIPT_TAG = '  <script src="pmp-theme.js"></script>\n'


def patch_exam(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "pmp-theme.css" in text:
        print(f"skip {path.name} (already patched)")
        return

    if "<style>" in text and HEAD_INJECT.strip() not in text:
        text = text.replace("<style>", HEAD_INJECT + "  <style>", 1)

    if ROOT_BLOCK in text:
        text = text.replace(ROOT_BLOCK, "", 1)

    for old, new in REPLACEMENTS:
        text = text.replace(old, new)

    if HEADER_OLD_EXAM in text and "header-end" not in text:
        text = text.replace(HEADER_OLD_EXAM, HEADER_NEW_EXAM, 1)
        # Close header-end before </header>
        text = text.replace(
            '      <span id="saveStatus" class="save-status" hidden aria-live="polite">Saved</span>\n    </div>\n  </header>',
            '      <span id="saveStatus" class="save-status" hidden aria-live="polite">Saved</span>\n'
            + "      </div>\n"
            + '      <button type="button" class="theme-toggle" id="themeToggle" aria-label="Switch to light mode" title="Light mode">&#9728;</button>\n'
            + "    </div>\n  </header>",
            1,
        )

    if "</body>" in text and SCRIPT_TAG.strip() not in text:
        text = text.replace("</body>", SCRIPT_TAG + "</body>", 1)

    path.write_text(text, encoding="utf-8")
    print(f"patched {path.name}")


def patch_index(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "pmp-theme.css" in text:
        print(f"skip {path.name} (already patched)")
        return

    text = text.replace("<style>", HEAD_INJECT + "  <style>", 1)
    index_root = """    :root {
      --bg: #0f1419;
      --surface: #1a2332;
      --surface2: #243044;
      --text: #e8eef4;
      --muted: #8b9cb3;
      --accent: #3b82f6;
      --accent-hover: #2563eb;
      --success: #22c55e;
      --border: #334155;
    }
"""
    text = text.replace(index_root, "", 1)
    text = text.replace("rgba(59, 130, 246, 0.08)", "var(--accent-soft-alpha)")
    text = text.replace("rgba(59, 130, 246, 0.12)", "var(--accent-badge-alpha)")

    text = text.replace(
        "  <header>\n    <h1>",
        '  <header style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:1rem;">\n    <div>\n    <h1>',
        1,
    )
    text = text.replace(
        "    <p>Practice exams for personal study · Pass target 70%</p>\n  </header>",
        "    <p>Practice exams for personal study · Pass target 70%</p>\n    </div>\n"
        '    <button type="button" class="theme-toggle" id="themeToggle" aria-label="Switch to light mode" title="Light mode">&#9728;</button>\n'
        "  </header>",
        1,
    )
    text = text.replace("</body>", SCRIPT_TAG + "</body>", 1)
    path.write_text(text, encoding="utf-8")
    print(f"patched {path.name}")


def main():
    for f in FILES:
        if f.name == "index.html":
            patch_index(f)
        else:
            patch_exam(f)


if __name__ == "__main__":
    main()
