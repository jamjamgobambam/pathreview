## Solution plan

**Issue:** Resume section detection fails on text with leading whitespace (#147)
https://github.com/ascherj/pathreview/issues/147

### Understand
The bug is in the resume parser's section-detection logic. `_detect_sections()`
in `ingestion/parsers/resume_parser.py` builds regex patterns that anchor
section headers (e.g. "Education", "Skills") strictly to the start of a line
using `^` or a preceding `\n`, with no tolerance for whitespace before the
header text. Expected behavior: `detected_sections` should list every section
header present, regardless of leading indentation (common in PDF-extracted
text). Actual behavior: when headers are indented, none of the four patterns
per section match, so `detected_sections` returns `[]` even though real
sections exist in the text. A correct implementation would strip or account
for leading whitespace before applying the anchor check, so indentation never
suppresses a real match.

### Map
- `ingestion/parsers/resume_parser.py` — `_detect_sections()` (lines 127–146),
  specifically the `patterns` list (lines 134–139), which is the exact code
  being changed
- `tests/unit/test_resume_parser.py` — contains the three related tests:
  `test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`,
  `test_detect_sections`; these define the expected passing behavior

### Plan
1. Modify the four regex patterns in `_detect_sections()` to allow optional
   leading whitespace after `^` and after `\n` (e.g. `^[ \t]*{section}\s*[:|-]`)
2. Remove the redundant `\n{section}` pattern variants, since `re.MULTILINE`
   already makes `^` match immediately after every `\n` — simplifies from 4
   patterns per section down to 2
3. Run `pytest tests/unit/test_resume_parser.py -k "no_work_experience or detect_sections" -v`
   and confirm both previously-failing tests now pass
4. Run the full file `pytest tests/unit/test_resume_parser.py -v` to confirm
   `test_parse_single_column_resume_text` and all other existing tests still pass
5. Run `make check` to confirm the change passes `ruff`, `black`, and `mypy`
   before opening a PR

### Inputs & outputs
**Input:** raw resume text (`str`) passed into `_detect_sections(text)` — this
text may come from PDF extraction (`_parse_pdf`) or Markdown parsing
(`_parse_markdown`), and may contain leading whitespace/indentation on any line.
**Output:** `detected_sections`, a `list[str]` of correctly-cased section names
(e.g. `["Education", "Skills"]`). The fix does not change the function
signature — only which inputs correctly produce non-empty output.

### Risks & unknowns
- Using `\s*` instead of `[ \t]*` for the leading-whitespace allowance risks
  matching across newlines unintentionally, since `\s` includes `\n` — need to
  test with `[ \t]*` specifically and verify in `test_detect_sections`
- Loosening the anchor could cause false positives if a section keyword
  appears as plain body text with only leading whitespace before it on its own
  line (e.g. a resume bullet that starts with the word "Skills" as prose, not
  a header) — need to check `tests/unit/test_resume_parser.py` for a case like
  this, and add one if missing
- Removing the redundant `\n{section}` patterns (step 2 above) changes the
  pattern list structure — need to re-verify all `SECTION_HEADERS` entries
  still match correctly after simplification, not just the two failing tests

### Edge cases
- Section header indented with tabs instead of spaces (e.g. `"\tEducation:"`)
- Section header with no trailing colon or dash, just the bare word on its
  own line (e.g. `"    Education"`)
- Empty string input — `_detect_sections("")` should return `[]` without
  raising an exception
- A section keyword appearing inside body text/prose rather than as an actual
  header (should NOT be falsely detected as a section)
- Multiple indentation levels within the same resume (e.g. some headers at
  4 spaces, others at 8 spaces due to inconsistent PDF extraction)