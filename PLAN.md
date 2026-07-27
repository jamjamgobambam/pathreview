## Solution plan

**Issue:** [Resume section detection fails on text with leading whitespace (#147)](https://github.com/ascherj/pathreview/issues/147)

### Understand

`_detect_sections()` in `ingestion/parsers/resume_parser.py` builds four regex
patterns per section name, all anchored directly to `^` or `\n` with the section
name immediately following (`^{section}\s*$`, `^{section}\s*[:|-]`,
`\n{section}\s*$`, `\n{section}\s*[:|-]`). None of these tolerate any characters
between the line start and the section name. PDF-extracted text (and, as it turns
out, plain indented text in general — including Python triple-quoted test fixtures)
commonly has leading whitespace on every line, so a header like `    Education:`
never matches `^Education`. Expected behavior: sections are detected regardless of
leading indentation. Actual behavior: `detected_sections` comes back `[]` whenever
headers are indented, confirmed via the issue's repro snippet and the three named
failing tests.

### Map

- `ingestion/parsers/resume_parser.py::_detect_sections` (lines 127–146) — the only
  place the fix needs to happen; the four regex pattern strings need to tolerate
  optional leading whitespace between the anchor and the section name.
- `tests/unit/test_resume_parser.py` — three existing tests already cover this
  (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`,
  `test_detect_sections`); may add one new test for an edge case not already covered
  (see Edge cases below).
- No changes expected to `_parse_pdf`, `_parse_markdown`, `_strip_markdown`, or
  `base.py` — they call `_detect_sections` as-is and the fix is internal to pattern
  matching, not to how text is extracted or stripped.

### Plan

1. Update the four regex patterns in `_detect_sections` to allow optional leading
   whitespace (`[ \t]*`) between the `^`/`\n` anchor and the section name.
2. Re-run the three named failing tests to confirm they pass.
3. Run the full `tests/unit/test_resume_parser.py` suite to make sure nothing else
   regresses (markdown-stripping tests, PDF multipage test, invalid-content tests).
4. Add one new test case for an indentation edge case not already covered (e.g. a
   document with headers indented at different, inconsistent depths, or
   tab-indented headers) to guard against regressing this fix later.
5. Run the full project test suite (not just this file) to check for unrelated
   breakage, then update `JOURNAL.md` with the final PR link.

### Inputs & outputs

Input: resume text as a `str` (from PDF extraction or markdown), potentially with
leading whitespace/indentation on any line. Output: unchanged in shape —
`_detect_sections` still returns a `list[str]` of title-cased section names; the fix
only changes which lines are eligible to match, not the return type or the rest of
`ParseResult`.

### Risks & unknowns

- Loosening the anchor could introduce false positives if a section-name word
  appears indented mid-sentence rather than as an actual header (e.g. a line reading
  "  see the education section above" contains "education" preceded by whitespace).
  Need to check whether the existing `\s*[:|-]` / `\s*$` suffix requirement already
  guards against this well enough, or whether it needs tightening at the same time.
- Under `re.MULTILINE`, `^` already matches the start of every line, so the
  `\n{section}` pattern variants may already be partially redundant with the
  `^{section}` variants once whitespace tolerance is added. Want to confirm this
  during the fix rather than assume it, but avoid an unrelated cleanup/refactor of
  the pattern list beyond what's needed to close this issue.
- Real PDF extraction can occasionally produce unicode whitespace (e.g. non-breaking
  spaces) that plain `[ \t]` won't match. Likely out of scope for this issue, but
  worth a one-line note in the PR description if not addressed.

### Edge cases

- Section header indented with tabs instead of spaces.
- Section header with varying trailing punctuation (`Education`, `Education:`,
  `Education -`) at different indentation levels.
- A section-name word appearing indented within body text rather than as a header
  (false-positive risk called out above).
- Multiple sections indented at different depths within the same document
  (realistic for inconsistent PDF extraction).
- Empty-string or whitespace-only input — existing behavior (no crash, empty
  `detected_sections`) should be preserved.
