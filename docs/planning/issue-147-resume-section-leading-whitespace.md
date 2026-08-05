# Issue 147 Plan: Resume Section Detection With Leading Whitespace

## Issue

- Link: https://github.com/ascherj/pathreview/issues/147
- Title: Resume section detection fails on text with leading whitespace
- Branch: `fix/147-resume-section-leading-whitespace`
- Tier: Tier 1

## Problem Summary

The resume parser misses valid section headers when extracted resume text contains indentation before headings such as `Education:` or `Skills:`. This is a realistic PDF extraction case because text extraction often preserves layout spacing. When those headers are missed, `detected_sections` can be incomplete even though the resume contains recognizable sections.

## Reproduction

Run the focused resume parser test after adding a regression case with indented headers:

```bash
python -m pytest tests/unit/test_resume_parser.py -k leading_whitespace
```

Minimal failing input:

```text
    John Smith
    john@example.com

    Education:
    - B.S. Computer Science

    Skills: Python
```

Expected result:

- `Education` is present in `detected_sections`
- `Skills` is present in `detected_sections`

Actual result before the fix:

- The parser does not detect these headers because the section regex only matches section names at the beginning of a line or immediately after `\n`, without allowing spaces before the header text.

## Root Cause

The affected code is `ResumeParser._detect_sections()` in `ingestion/parsers/resume_parser.py`. The existing patterns anchor section names with `^` or `\n` but do not permit leading whitespace before the section name. With `re.MULTILINE`, `^education` matches `Education:` only when `Education` starts at column 0.

The markdown stripping logic has a related edge case: indented markdown headings such as `    ## Skills` are not stripped by the previous heading regex.

## Solution Plan

1. Add a focused regression test in `tests/unit/test_resume_parser.py` that passes resume text with indented `Education:` and `Skills:` headings to `_detect_sections()`.
2. Update `_detect_sections()` so section header patterns allow optional leading whitespace with `^\s*`.
3. Keep matching constrained to line starts so normal body text that happens to contain words like "skills" is not treated as a section header.
4. Update markdown heading stripping to allow optional leading whitespace before `#` headings.
5. Run the targeted parser test file, then run broader unit checks if time allows.

## Test Plan

Primary check:

```bash
python -m pytest tests/unit/test_resume_parser.py
```

Regression covered:

- `test_detect_sections_with_leading_whitespace` verifies indented `Education:` and `Skills:` headings are detected.

Existing behavior covered:

- Standard section detection still works for non-indented `Experience:`, `Education:`, and `Skills:`.
- Markdown resume parsing still strips markdown syntax.
- Invalid content types and PDF parsing errors still raise clear `ValueError` exceptions.

## Risks

- The regex change could over-detect section names inside regular text if the pattern becomes too broad. To avoid this, the fix should keep the `^` line-start anchor and only add optional whitespace after the anchor.
- Section order is not guaranteed because `_detect_sections()` returns `list(set(detected))`; tests should assert membership instead of exact order.

## Loom Walkthrough Outline

1. Show the issue link and summarize the bug: indented resume section headers are missed.
2. Open `ingestion/parsers/resume_parser.py` and point to `_detect_sections()`.
3. Show the minimal reproduction input with leading spaces before `Education:` and `Skills:`.
4. Explain the intended fix: allow optional leading whitespace after the line-start anchor.
5. Show the regression test in `tests/unit/test_resume_parser.py`.
6. Run `python -m pytest tests/unit/test_resume_parser.py` and show the passing result.
