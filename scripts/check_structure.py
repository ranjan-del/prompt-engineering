#!/usr/bin/env python3
"""Structure check for the Prompt Engineering Handbook.

Verifies that every technique page exists, contains all the required
sections, and carries no unfilled scaffold markers. Exits non-zero on any
failure so it can gate CI.

This is the repo's only test suite. The handbook is prose, so there is
nothing to unit test, but the thing that actually rots in a documentation
repo is consistency: a page that quietly loses a section, an index link that
goes stale, a stub that never got filled in. Those are mechanically
checkable, so they are checked here.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FOLDERS = [
    "01-zero-shot",
    "02-few-shot",
    "03-chain-of-thought",
    "04-self-consistency",
    "05-react",
    "06-json-mode",
    "07-structured-output",
    "08-prompt-templates",
    "09-prompt-chaining",
    "10-evaluation",
]

# Ordered as the sections should appear on the page. The order is enforced
# too: a reader moving between technique pages should find the same shape
# every time, which is the whole promise of a handbook.
REQUIRED_SECTIONS = [
    "Theory",
    "When to Use It",
    "When Not to Use It",
    "Example Prompt",
    "Output",
    "Before and After",
    "Best Practices",
    "Common Mistakes",
]

# Markers that indicate an unfinished stub.
FORBIDDEN = ["TODO", "NotImplementedError", "_Placeholder", "Skeleton page"]

# House style: the handbook uses ':' or ',' instead of em dashes. Written as a
# unicode escape rather than the literal character so this file stays pure
# ASCII and does not trip the very check it defines.
EM_DASH = "\u2014"

# Every page carries substantive prose in eight sections, so anything under
# this is a section that got gutted rather than a page that is merely terse.
MIN_PAGE_CHARS = 4000


def heading_sequence(text: str) -> list[str]:
    """Return the level-2 headings of a page, in document order."""
    return [m.strip() for m in re.findall(r"^##\s+(.+)$", text, flags=re.MULTILINE)]


def check_page(folder: str) -> list[str]:
    errors: list[str] = []
    path = ROOT / folder / "README.md"
    if not path.is_file():
        return [f"{folder}/README.md is missing"]

    text = path.read_text(encoding="utf-8")
    headings = heading_sequence(text)
    heading_set = set(headings)

    for section in REQUIRED_SECTIONS:
        if section not in heading_set:
            errors.append(f"{folder}/README.md missing section: '## {section}'")

    # Only check ordering once every section is present, otherwise a single
    # missing heading reports itself twice and buries the real cause.
    if not errors:
        found = [h for h in headings if h in set(REQUIRED_SECTIONS)]
        if found != REQUIRED_SECTIONS:
            errors.append(
                f"{folder}/README.md sections are out of order: "
                f"expected {REQUIRED_SECTIONS}, found {found}"
            )

    for marker in FORBIDDEN:
        if marker in text:
            errors.append(f"{folder}/README.md still contains scaffold marker: '{marker}'")

    if EM_DASH in text:
        errors.append(f"{folder}/README.md contains an em dash (house style: use ':' or ',')")

    # Every technique should point back to the index so no page is a dead end.
    if "../README.md)" not in text:
        errors.append(f"{folder}/README.md has no link back to the handbook index")

    # A filled page should have real prose, not just headings.
    if len(text) < MIN_PAGE_CHARS:
        errors.append(
            f"{folder}/README.md is suspiciously short "
            f"({len(text)} chars, minimum {MIN_PAGE_CHARS})"
        )

    return errors


def check_index() -> list[str]:
    errors: list[str] = []
    readme = ROOT / "README.md"
    if not readme.is_file():
        return ["top-level README.md is missing"]

    text = readme.read_text(encoding="utf-8")
    for folder in FOLDERS:
        if f"{folder}/README.md)" not in text:
            errors.append(f"top-level README.md does not link to {folder}/README.md")

    if EM_DASH in text:
        errors.append("top-level README.md contains an em dash (house style: use ':' or ',')")

    # The README promises MIT and the licence has to actually be there.
    if not (ROOT / "LICENSE").is_file():
        errors.append("LICENSE is missing")

    return errors


def check_no_stray_folders() -> list[str]:
    """Catch a technique folder added on disk but never wired into FOLDERS."""
    known = set(FOLDERS)
    stray = sorted(
        p.name
        for p in ROOT.iterdir()
        if p.is_dir() and re.fullmatch(r"\d{2}-[a-z0-9-]+", p.name) and p.name not in known
    )
    return [f"technique folder '{name}' is not registered in FOLDERS" for name in stray]


def main() -> int:
    all_errors: list[str] = []
    for folder in FOLDERS:
        all_errors.extend(check_page(folder))
    all_errors.extend(check_index())
    all_errors.extend(check_no_stray_folders())

    if all_errors:
        print("Structure check FAILED:")
        for err in all_errors:
            print(f"  - {err}")
        print(f"\n{len(all_errors)} problem(s) found.")
        return 1

    checks = len(FOLDERS) * (len(REQUIRED_SECTIONS) + 4) + len(FOLDERS) + 3
    print(
        f"Structure check passed: {len(FOLDERS)} technique pages, "
        f"{len(REQUIRED_SECTIONS)} required sections each (present and in order), "
        f"no scaffold markers, no em dashes, index links and LICENSE verified "
        f"({checks} assertions)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
