#!/usr/bin/env python3
"""Structure check for the Prompt Engineering Handbook.

Verifies that every technique page exists, contains the five required
sections, and carries no unfilled scaffold markers. Exits non-zero on any
failure so it can gate CI.
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

REQUIRED_SECTIONS = [
    "Theory",
    "Example Prompt",
    "Output",
    "Best Practices",
    "Common Mistakes",
]

# Markers that indicate an unfinished stub.
FORBIDDEN = ["TODO", "NotImplementedError", "_Placeholder", "Skeleton page"]


def check_page(folder: str) -> list[str]:
    errors: list[str] = []
    path = ROOT / folder / "README.md"
    if not path.is_file():
        return [f"{folder}/README.md is missing"]

    text = path.read_text(encoding="utf-8")
    headings = {m.strip() for m in re.findall(r"^##\s+(.+)$", text, flags=re.MULTILINE)}

    for section in REQUIRED_SECTIONS:
        if section not in headings:
            errors.append(f"{folder}/README.md missing section: '## {section}'")

    for marker in FORBIDDEN:
        if marker in text:
            errors.append(f"{folder}/README.md still contains scaffold marker: '{marker}'")

    # A filled page should have real prose, not just headings.
    if len(text) < 800:
        errors.append(f"{folder}/README.md is suspiciously short ({len(text)} chars)")

    return errors


def check_index() -> list[str]:
    errors: list[str] = []
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    for folder in FOLDERS:
        if f"{folder}/README.md)" not in text:
            errors.append(f"top-level README.md does not link to {folder}/README.md")
    return errors


def main() -> int:
    all_errors: list[str] = []
    for folder in FOLDERS:
        all_errors.extend(check_page(folder))
    all_errors.extend(check_index())

    if all_errors:
        print("Structure check FAILED:")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print(f"Structure check passed: {len(FOLDERS)} pages, "
          f"{len(REQUIRED_SECTIONS)} sections each, no scaffold markers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
