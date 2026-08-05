## Solution plan

**Issue:** Resume section detection fails on text with leading whitespace — https://github.com/ascherj/pathreview/issues/147

### Understand
`_detect_sections()` in `ingestion/parsers/resume_parser.py` builds regex patterns that anchor a section header directly after `^` or `\n` (e.g. `^experience\s*$`). Expected behavior: a line like `"    Experience"` (indented, as many PDF extractions produce) should still be recognized as an `Experience` header. Actual behavior: because the patterns don't account for leading whitespace, indented headers never match, and `_detect_sections()` returns an empty list even when every expected section is present in the text.

### Map
- `ingestion/parsers/resume_parser.py` — `_detect_sections()` (lines ~127-146), the method whose regex patterns need to change.
- `tests/unit/test_resume_parser.py` — `test_detect_sections()` (lines ~126-144), an existing test that already fails against the current code (its sample text is indented); may add a dedicated indentation test alongside it.

### Plan
1. Update the four regex patterns in `_detect_sections()` to allow optional leading whitespace before the header, e.g. `^{section}` → `^[ \t]*{section}` and `\n{section}` → `\n[ \t]*{section}`.
2. Re-run `test_detect_sections` to confirm it now passes against the current sample (indented) text.
3. Add a new unit test that isolates the indentation case specifically (e.g. a resume where every header is indented with spaces) to guard against regressions distinct from the existing mixed test.
4. Add a test asserting that indented body/bullet text that isn't a header (e.g. `"    - Built an app using Python"`) is still NOT misdetected as a section header, to confirm the fix isn't overly permissive.
5. Run the full suite (`make test-unit`) to confirm nothing else regressed.

### Inputs & outputs
- Input: `text: str` — resume text already extracted from a PDF or markdown source, passed into `_detect_sections(text)`.
- Output: `list[str]` — deduplicated, title-cased section names detected in the text (e.g. `["Experience", "Education"]`).
- The fix only changes the matching logic inside `_detect_sections`; the method's input/output contract stays the same.

### Risks & unknowns
- Being too permissive with whitespace could cause indented non-header lines to be misclassified as headers if they happen to start with a section-header word — need to confirm the existing `\s*$` / `\s*[:|-]` suffix constraints still prevent this after the change.
- Different PDF extraction outputs (via `pypdf`) may use tabs, multiple spaces, or non-breaking spaces for indentation — unsure whether `\s`/`[ \t]` covers all real-world cases without testing against actual PDF-extracted samples.
- Unsure whether indentation should ever be significant (e.g. distinguishing a top-level header from a sub-header) elsewhere in the codebase — need to check nothing downstream relies on headers only being flush-left.

### Edge cases
- Header indented with tabs instead of spaces.
- Header preceded by blank or whitespace-only lines.
- Mixed resume where some headers are indented and others are flush-left.
- Indented text that looks header-like but is actually body/bullet content (false-positive risk).
- Resume with no indentation at all (regression check — must keep matching flush-left headers).
