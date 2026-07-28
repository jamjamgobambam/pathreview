## Solution plan

**Issue:** [https://github.com/ascherj/pathreview/issues/147]

**Issue title:** [Resume section detection fails on text with leading whitespace
 #147]

### Understand
`_detect_sections()` in `ingestion/parsers/resume_parser.py` builds four regex
patterns per section keyword (e.g. `education`), anchored with `^` (start of
line, under `re.MULTILINE`) or `\n` (immediately after a newline). Neither
anchor allows for leading whitespace before the keyword. PDF text extraction
(via `pypdf`'s `extract_text()`) commonly preserves indentation, and
markdown resumes can be indented too, so an indented heading like
`    Education:` never matches `^education\s*[:|-]`. The result:
`detected_sections` comes back empty even when valid headings are present.

Expected behavior: a section heading should be recognized whether or not it
has leading horizontal whitespace (spaces or tabs) in front of it.
Actual behavior: any indentation in front of a heading causes that heading
to be silently skipped, with no error and no fallback detection.

### Map
- `ingestion/parsers/resume_parser.py` — `ResumeParser._detect_sections()`,
  specifically the `patterns = [...]` list built inside the `for section in
  SECTION_HEADERS` loop. This is the only place the fix needs to change
  production code.
- `tests/unit/test_resume_parser.py` — three existing failing tests
  (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`,
  `test_detect_sections`) that should pass once the fix lands, plus a new
  test I'll add for tab/mixed-indentation headings.
- `ingestion/parsers/resume_parser.py` — `_parse_pdf()` and `_parse_markdown()`
  indirectly, since they both call `_detect_sections()`; I'm not changing
  them, but I need to confirm neither one normalizes whitespace before
  calling it (which would mask the bug at a different layer).

### Plan
1. Update the four regex patterns in `_detect_sections()` so the
   line-start anchors (`^{section}` and `\n{section}`) allow optional
   leading horizontal whitespace, e.g. `^[ \t]*{section}\s*[:|-]` instead of
   `^{section}\s*[:|-]`. Use `[ \t]*`, not `\s*`, so the pattern can't cross
   a newline and accidentally anchor to a header several lines below.
2. Check whether the `\n{section}...` pattern variants are now fully
   redundant with the `^{section}...` variants given `re.MULTILINE` (since
   `^` already matches right after every `\n`), and simplify the `patterns`
   list if so, to avoid maintaining duplicate logic.
3. Re-run the three currently-failing tests
   (`pytest tests/unit/test_resume_parser.py -k "test_parse_single_column_resume_text or test_parse_resume_no_work_experience or test_detect_sections" -vv`)
   and confirm all three pass.
4. Add a new unit test in `tests/unit/test_resume_parser.py` covering
   tab-indented and mixed-indentation section headers (not just the plain
   spaces produced by triple-quoted strings), since none of the existing
   tests exercise tabs.
5. Run the full suite (`pytest tests/unit/test_resume_parser.py` and then
   the broader `pytest tests/unit`) to confirm the widened pattern doesn't
   introduce false positives elsewhere in the parser test suite.

### Inputs & outputs
**Input:** the `text: str` argument to `_detect_sections(self, text: str)` —
already lower-cased by the caller before pattern matching. This text
originates either from `_parse_pdf()` (raw `page.extract_text()` output,
joined across pages) or `_parse_markdown()` (output of `_strip_markdown()`),
both of which can contain leading spaces/tabs on section-heading lines.

**Output:** `list[str]` of detected, title-cased, de-duplicated section
names. No public signature changes — `_detect_sections` still takes `text`
and returns `list[str]`. After the fix, the same input that currently
produces `[]` should produce `['Education', 'Skills']` (per the issue's
repro example), without changing what's detected for non-indented resumes.

### Risks & unknowns
- **Risk (regex over-broadening):** if I use `\s*` instead of `[ \t]*` for
  the leading-whitespace fix, `\s` matches newlines too, so the pattern
  could skip blank lines and falsely anchor to a keyword several lines
  below the intended `^` position. Tied directly to the `patterns = [...]`
  list inside `_detect_sections()` — need to verify with a test that has a
  blank line before a section header.
- **Risk (false positives on indented body text):** widening the anchor
  could cause a section keyword appearing inside indented bullet/body text
  (e.g. `    - see skills matrix below`) to be misdetected as a `Skills`
  header. Need to confirm the trailing part of the pattern
  (`\s*[:|-]` / `\s*$`) still requires the line to look like an actual
  header and not just contain the word — I'll add a test case for this.
- **Unknown:** whether `pypdf`'s `extract_text()` in `_parse_pdf()`
  consistently represents indentation as spaces vs. tabs across different
  PDF producers — if it doesn't, my tab-indentation test may not reflect
  real-world PDF output faithfully.
- **Unknown:** whether `test_parse_multipage_pdf` (which mocks
  `PdfReader`/`extract_text`) would surface an indentation-related
  regression, since its mocked page text isn't indented — may need a
  follow-up test with indented mocked pages.

### Edge cases
1. Section header indented with tabs instead of spaces (e.g. `\tEducation:`).
2. Section header with mixed leading whitespace (e.g. two spaces + a tab, as
   might appear from nested PDF text-extraction artifacts).
3. Section keyword indented but appearing as part of body/bullet text, not
   an actual header (e.g. `    - discussed skills with the team`) — must
   **not** be detected as a `Skills` section.
4. Section header with both leading and trailing whitespace before the
   colon (e.g. `   Education   :`).
5. Resume text with no section headers at all, or empty text — should
   still return `[]` without raising, even with the widened pattern.