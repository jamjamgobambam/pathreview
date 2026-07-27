## Solution plan

**Issue:** Resume section detection fails on text with leading whitespace
(#147) — https://github.com/ascherj/pathreview/issues/147

### Understand
`_detect_sections()` in `ingestion/parsers/resume_parser.py` matches section
headers (Education, Skills, etc.) using regex patterns anchored directly to
`^` (start of line) or `\n` (newline), with no whitespace allowed between the
anchor and the header word. PDF-extracted resume text commonly has leading
indentation on each line, so `"    Education:"` never matches `^education`.
Expected: `detected_sections` contains every section header present in the
text, regardless of indentation. Actual: `detected_sections` returns `[]`
whenever lines are indented.

### Map
- `ingestion/parsers/resume_parser.py` — `_detect_sections()` (lines 127–146),
  specifically the `patterns` list (lines 134–139)
- `tests/unit/test_resume_parser.py` — `test_parse_single_column_resume_text`,
  `test_parse_resume_no_work_experience`, `test_detect_sections`

### Plan
1. Update the four regex patterns in `_detect_sections()` to allow optional
   leading whitespace (`\s*`) between each anchor (`^` / `\n`) and the section
   name.
2. Re-run the repro script from the issue and confirm `detected_sections`
   returns `['Education', 'Skills']` instead of `[]`.
3. Run the three named failing tests and confirm they pass.
4. Run the full test suite for this file to check for regressions in
   previously-passing tests.
5. Manually test with a resume that has *no* indentation, to confirm the fix
   doesn't break the existing non-indented case.

### Inputs & outputs
Input: raw resume text (string), possibly with leading whitespace on each
line. Output: unchanged — still a `list[str]` of detected section names.
The fix only changes which lines are matched, not the return format.

### Risks & unknowns
- `\s*` is broad and also matches tabs/multiple spaces — need to confirm this
  doesn't cause false positives on text where "education" appears mid-sentence
  with leading whitespace but isn't actually a header (e.g. inside a bullet
  point). Will check test suite for such cases.
- Not yet sure whether `_strip_markdown()` (used in `_parse_markdown`) already
  strips leading whitespace before `_detect_sections()` is called — if so, the
  markdown path might behave differently from the PDF path and needs separate
  verification.

### Edge cases
- Section header with tabs instead of spaces for indentation
- Section header with trailing whitespace after the colon
- Text with no indentation at all (must still work, regression check)
- Empty text input
- Section name appearing indented but not actually as a header (false
  positive risk noted above)