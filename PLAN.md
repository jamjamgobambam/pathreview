# Solution plan

**Issue:** [Resume section detection fails on text with leading whitespace (#147)](https://github.com/ascherj/pathreview/issues/147)

### Understand

`ResumeParser._detect_sections()` (`ingestion/parsers/resume_parser.py`) is
supposed to scan resume text and return which known sections (Education,
Skills, Experience, etc.) are present, by matching each section keyword
against regex patterns anchored to the start of a line.

**Expected behavior:** Given text containing a line like `"Education:"`,
`_detect_sections()` should return `["Education"]` (and similarly for other
section headers), regardless of whether that line has leading whitespace.

**Actual behavior:** When a line has leading whitespace before the section
keyword (e.g. `"    Education:"` — common in PDF-extracted text, and also
produced naturally by indented triple-quoted strings in the tests), none of
the four regex patterns match, so the section is silently dropped and
`detected_sections` comes back empty.

**Root cause:** all four patterns anchor directly on `^` or `\n` immediately
followed by the section keyword, with nothing between the anchor and the
keyword to absorb leading spaces/tabs:

```python
patterns = [
    rf"^{re.escape(section)}\s*$",
    rf"^{re.escape(section)}\s*[:|-]",
    rf"\n{re.escape(section)}\s*$",
    rf"\n{re.escape(section)}\s*[:|-]",
]
```

### Map

Files/functions I expect to touch:

- `ingestion/parsers/resume_parser.py` — `_detect_sections()`, specifically the
  `patterns` list (lines ~134-139). This is the only place the anchoring logic
  lives.
- `tests/unit/test_resume_parser.py` — no new test file needed; the three
  existing failing tests (`test_parse_single_column_resume_text`,
  `test_parse_resume_no_work_experience`, `test_detect_sections`) already
  cover the indented-text case and should pass once the fix lands. I may add
  one more small test case for a tab-indented line, since none of the existing
  fixtures use tabs specifically.

Nothing outside `ingestion/parsers/` should need changes — `_parse_pdf` and
`_parse_markdown` both just call `_detect_sections()` and don't do any of
their own anchoring.

### Plan

1. Update each pattern in `_detect_sections()` to allow optional leading
   whitespace between the line-start anchor and the section keyword — e.g.
   inserting `[ \t]*` right after `^` and after `\n` in all four patterns.
2. Re-run the three failing unit tests locally to confirm they now pass
   (`.venv/bin/pytest tests/unit/test_resume_parser.py -v -k "test_parse_single_column_resume_text or test_parse_resume_no_work_experience or test_detect_sections"`).
3. Run the full resume parser test file to confirm nothing else regressed
   (`.venv/bin/pytest tests/unit/test_resume_parser.py -v`).
4. Add a small additional test case covering tab-indented section headers
   (not just space-indented), since the issue only mentions spaces explicitly.
5. Run `make check` (lint, format, typecheck) before opening the PR.

### Inputs & outputs

- **Input:** raw resume text (`str`) as produced by `_parse_pdf` (via
  `pypdf` extraction) or `_parse_markdown` (after markdown stripping) — may
  contain lines with leading spaces or tabs before a section keyword.
- **Output:** unchanged shape — `_detect_sections()` still returns
  `list[str]` of title-cased section names (e.g. `["Education", "Skills"]`).
  The fix only changes *which* inputs produce a non-empty result; it doesn't
  change the return type or calling contract.

### Risks & unknowns

- Loosening the anchors slightly increases the chance of a false-positive
  match if a section keyword appears indented mid-sentence rather than as a
  real header — need to keep the whitespace class narrow (`[ \t]*`, not
  `\s*`, which would also swallow newlines and could bridge across lines).
- Not fully sure yet how much leading whitespace real-world PDF extraction
  produces (a few spaces vs. many, spaces vs. tabs vs. non-breaking spaces) —
  the fix targets normal spaces/tabs; unusual whitespace characters (e.g. `\xa0`)
  are out of scope unless a test surfaces them.
- Need to double check the fix doesn't break detection when a section keyword
  legitimately appears with no leading whitespace (regression risk on the
  currently-passing tests).

### Edge cases

- Section header with leading spaces: `"    Education:"` (the case in the
  issue).
- Section header with leading tabs: `"\tSkills: Python"`.
- Section header with no leading whitespace (must still work, e.g.
  `"Education:"` unindented).
- Section keyword appearing indented but *not* as a header, e.g. inside a
  bullet point (`"    - Studied Education policy"`) — should ideally not be
  a false positive, though this is already an existing limitation of the
  keyword-based approach, not something introduced by this fix.
- Empty text / text with no section headers at all — should still return `[]`
  without error (existing behavior, must not regress).
