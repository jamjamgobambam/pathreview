## Solution plan

**Issue:** Resume section detection fails on text with leading whitespace — https://github.com/ascherj/pathreview/issues/147

### Understand
`_detect_sections` in `resume_parser.py` matches section headers ("Experience", "Education", "Skills") using regex patterns anchored with `^` or `\n` in MULTILINE mode. These anchors require the header text to start immediately at the beginning of a line. PDF extraction (and indented test fixtures) frequently introduce leading spaces or tabs before headers, so the anchor never lines up with the header text and the match silently fails — `_detect_sections` returns an empty or partial list instead of raising an error.

### Map
- `ingestion/parsers/resume_parser.py` — `_detect_sections` method, the four regex patterns built per section
- `tests/unit/test_resume_parser.py` — `test_detect_sections`, currently failing on the "education" (and likely "skills") assertion

### Plan
1. Update the four regex patterns in `_detect_sections` to allow optional leading whitespace after each anchor (`^\s*`, `\n\s*`) instead of `^`/`\n` directly.
2. Re-run `pytest tests/unit/test_resume_parser.py -k test_detect_sections` and confirm all three section assertions pass.
3. Run the full `test_resume_parser.py` file to check for regressions in other tests that rely on `_detect_sections`.
4. Manually test with a snippet using tabs instead of spaces for indentation, to confirm the fix isn't space-specific.

### Inputs & outputs
**Input:** raw resume text (`str`), which may have inconsistent leading whitespace per line due to PDF-to-text extraction.
**Output:** `list[str]` of detected section header names, deduplicated and title-cased.

### Risks & unknowns
- Loosening the anchor to `\s*` could theoretically match a header-like word buried mid-paragraph if it happens to follow a newline directly — need to confirm `SECTION_HEADERS` values are specific enough to avoid false positives.
- Unclear whether other parsing steps downstream of `_detect_sections` assume headers are unindented; worth checking callers of this method.
- Haven't confirmed whether real PDF extraction output uses spaces, tabs, or a mix — test fixtures only cover spaces so far.

### Edge cases
- Section header indented with tabs instead of spaces
- Header line with trailing whitespace before the colon (e.g. `Education :`)
- Multiple blank lines between the indentation and the header
- Empty string input to `_detect_sections`