"""Reproduce issue #147: resume section detection fails on leading whitespace.

Run with: .venv/bin/python scripts/repro_issue_147.py

Prints detected sections for the same resume rendered flush-left, space-indented,
and tab-indented. Only the flush-left variant is detected today.
"""

from ingestion.parsers.resume_parser import ResumeParser

FLUSH_LEFT = """Jane Doe
Software Engineer

Experience:
- Software Engineer at TechCorp (2022-2024)

Education:
- B.S. Computer Science, State University (2022)

Skills: Python, JavaScript, React
"""

SPACE_INDENTED = "\n".join("  " + line if line else line for line in FLUSH_LEFT.splitlines())

TAB_INDENTED = "\n".join("\t" + line if line else line for line in FLUSH_LEFT.splitlines())

INDENTED_MARKDOWN = """
    # Jane Doe

    ## Experience
    - Software Engineer at TechCorp (2022-2024)

    ## Skills
    - Python, JavaScript
"""

EXPECTED = {"Experience", "Education", "Skills"}


def main() -> None:
    """Parse each resume variant and report which sections were detected."""
    parser = ResumeParser()

    cases = [
        ("flush-left (works today)", FLUSH_LEFT, EXPECTED),
        ("space-indented", SPACE_INDENTED, EXPECTED),
        ("tab-indented", TAB_INDENTED, EXPECTED),
        ("indented markdown", INDENTED_MARKDOWN, {"Experience", "Skills"}),
    ]

    for label, text, expected in cases:
        detected = set(parser.parse(text).metadata["detected_sections"])
        missing = expected - detected
        status = "OK  " if not missing else "BUG "
        print(
            f"{status} {label:28} detected={sorted(detected) or '[]'} missing={sorted(missing) or '[]'}"
        )


if __name__ == "__main__":
    main()
