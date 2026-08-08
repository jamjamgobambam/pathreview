"""Reproduce GitHub issue #147: resume section detection with leading whitespace.

Run from repo root:
    python scripts/reproduce_issue_147.py

Without the regex fix, indented headers match nothing and detected_sections
is []. With the fix (optional \\s* after ^ / \\n), Education and Skills appear.
"""

from __future__ import annotations

import re

from ingestion.parsers.resume_parser import SECTION_HEADERS, ResumeParser

# Exact sample from https://github.com/ascherj/pathreview/issues/147
SAMPLE = (
    "\n    John Smith\n    john@example.com\n\n"
    "    Education:\n    - B.S. Computer Science\n\n"
    "    Skills: Python\n"
)


def detect_sections_broken(text: str) -> list[str]:
    """Pre-fix patterns: headers must start at column 0 (no leading whitespace)."""
    detected: list[str] = []
    text_lower = text.lower()

    for section in SECTION_HEADERS:
        patterns = [
            rf"^{re.escape(section)}\s*$",
            rf"^{re.escape(section)}\s*[:|-]",
            rf"\n{re.escape(section)}\s*$",
            rf"\n{re.escape(section)}\s*[:|-]",
        ]
        for pattern in patterns:
            if re.search(pattern, text_lower, re.MULTILINE):
                detected.append(section.title())
                break

    return list(set(detected))


def main() -> None:
    broken = detect_sections_broken(SAMPLE)
    fixed = ResumeParser().parse(SAMPLE).metadata["detected_sections"]

    print("Issue #147 reproduction")
    print(f"  broken (old regex): {broken}")
    print(f"  current parser:     {fixed}")
    print("  expected:            ['Education', 'Skills'] (order may vary)")
    print()
    if broken == [] and {"Education", "Skills"}.issubset(set(fixed)):
        print("Reproduction confirmed: old patterns miss indented headers;")
        print("current _detect_sections handles leading whitespace.")
    else:
        print("Unexpected result — check resume_parser._detect_sections patterns.")


if __name__ == "__main__":
    main()
