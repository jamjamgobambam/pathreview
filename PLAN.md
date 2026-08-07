## Solution plan

**Issue:** Resume section detection fails on text with leading whitespace — https://github.com/ascherj/pathreview/issues/147

### Understand
`_detect_sections()` in `ingestion/parsers/resume_parser.py` anchors every section-heading pattern to `^` or `\n` with no allowance for leading spaces or tabs. Expected: an indented heading like `  Experience:` is detected. Actual: any leading whitespace makes the heading invisible, so an indented or formatted resume returns zero detected sections.

### Map
- `ingestion/parsers/resume_parser.py` → `_detect_sections()` (the regex patterns) — the fix lives here
- `tests/unit/test_resume_parser.py` → add new tests, modeled on the existing test structure

### Plan
1. **Write failing tests first** (this also serves as the reproduction commit): an indented heading, a tab-indented heading, and a false-positive guard (`"I have experience with..."` mid-sentence must NOT be detected as an Experience section).
2. Update the four regex patterns in `_detect_sections()` to allow optional leading whitespace (`[ \t]*`) right after each `^` / `\n` anchor — keeping the anchor in place.
3. Run the full unit test suite: confirm the new tests pass and the existing tests still pass (no regressions).
4. Verify the live before/after behavior on an indented resume string.

### Inputs & outputs
- **Input:** resume text (string) whose section headings may have leading spaces or tabs.
- **Output:** `_detect_sections()` returns the correct list of detected section names, now including indented headings — with unchanged behavior for non-indented headings and for section keywords used mid-sentence.

### Risks & unknowns
- Loosening the regex too much could cause false positives (e.g., a mid-sentence "experience"). Mitigation: keep the `^` / `\n` anchor and only add `[ \t]*` after it.
- Ensure the whitespace class covers both spaces and tabs (`[ \t]`).
- The existing patterns use `\s`, which also matches newlines; confirm the horizontal-only `[ \t]*` addition interacts cleanly with `re.MULTILINE`.

### Edge cases
- Indented headings (spaces and tabs)
- A heading on the very first line (no preceding newline)
- A section keyword used mid-sentence (must NOT be detected)
- Trailing punctuation on headings (`:`, `|`, `-`) continues to work
