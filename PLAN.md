## Solution plan

**Issue:** [Resume section detection fails on text with leading whitespace #147](https://github.com/ascherj/pathreview/issues/147)

### Understand

`_detect_sections()` in `ingestion/parsers/resume_parser.py` (lines 127–146) builds four regex patterns per section header:

```
^<header>\s*$
^<header>\s*[:|-]
\n<header>\s*$
\n<header>\s*[:|-]
```

These patterns require the header word to appear immediately after `^` (start of line under `re.MULTILINE`) or immediately after `\n`, with no intervening characters. When text is extracted from a PDF, lines commonly begin with leading spaces or tabs (e.g. `    Education:`). The word-start anchors never match that indented text, so `detected_sections` is always empty for PDF-sourced resumes with indentation.

**Expected:** `_detect_sections('    Education:\n    Skills: Python')` → `['Education', 'Skills']`
**Actual:** `[]`

### Map

Files that need to change:

- `ingestion/parsers/resume_parser.py` — `_detect_sections()` method, specifically the four pattern strings built at lines 134–139. This is the only file that requires a code change.

Files involved in testing:

- `tests/unit/test_resume_parser.py` — `test_detect_sections`, `test_parse_resume_no_work_experience`, and `test_parse_single_column_resume_text` are the three tests currently failing; they must pass after the fix.
- `tests/conftest.py` — may define the `sample_resume_text` fixture used by `test_parse_single_column_resume_text`; verify it uses indented text.

### Plan

1. **Update the four regex patterns in `_detect_sections()`** to allow optional leading whitespace before the header word. Change `^{section}` → `^\s*{section}` and `\n{section}` → `\n\s*{section}` in the pattern list at lines 134–139 of `resume_parser.py`.

2. **Verify all three failing tests pass** by running `python -m pytest tests/unit/test_resume_parser.py -v`. Confirm `test_detect_sections`, `test_parse_resume_no_work_experience`, and `test_parse_single_column_resume_text` all go green.

3. **Confirm previously passing tests are not broken** by running the full unit test suite (`python -m pytest tests/unit/ -v`) and checking that no regressions are introduced — particularly `test_parse_multipage_pdf`, `test_parse_markdown_resume`, and `test_strip_markdown_syntax`.

4. **Check for false-positive risk** (see Risks below): search the test fixtures and sample data for any sentence that contains a section keyword mid-sentence (e.g. "She has experience with Python") to verify the updated patterns do not match those lines as section headers.

### Inputs & outputs

**Input to `_detect_sections(text: str)`:** a plain-text string extracted from a PDF or markdown resume, potentially with leading whitespace on every line.

**Output:** a `list[str]` of detected section names in title case (e.g. `["Education", "Skills", "Experience"]`).

**What changes:** only the four compiled regex strings inside `_detect_sections()`. The method signature, return type, and all callers (`_parse_pdf`, `_parse_markdown`) remain unchanged. The `SECTION_HEADERS` constant is not touched.

### Risks & unknowns

- **False positives on mid-sentence keywords** (`resume_parser.py` line 134–139): a sentence like "She has relevant experience with distributed systems" could match the `experience` pattern if the line starts with whitespace and the word appears right after the indentation. The trailing `\s*$` and `\s*[:|-]` suffixes on the patterns reduce (but do not eliminate) this risk. After patching, run the failing tests and manually inspect any unexpected detections in `test_parse_multipage_pdf`.

- **`re.MULTILINE` interaction** (`resume_parser.py` line 141): `^` with `re.MULTILINE` matches at the start of each logical line, so `^\s*{section}` is correct. Switching to `\n\s*` patterns is redundant once `^` works — need to verify whether both pattern families are still needed or if the `\n`-anchored variants can be removed to avoid duplicate detections.

- **`sample_resume_text` fixture content** (`tests/conftest.py`): `test_parse_single_column_resume_text` relies on a shared fixture that may or may not use indented text. If it doesn't use indentation, this test may already pass before the fix and is not the right signal; need to inspect the fixture.

### Edge cases

- **All-whitespace prefix lines** (e.g. `\t\tSkills:`): tabs instead of spaces before the header — `\s*` covers both, but verify with a tab-indented fixture.
- **Header with no trailing delimiter** (e.g. `    Experience` on a line by itself with no colon): the `^\s*{section}\s*$` pattern must match this; confirm the `$` anchor under `re.MULTILINE` terminates at `\n`.
- **Mixed indentation depth** (some lines indented 2 spaces, others 8): `\s*` is greedy and matches any amount, so all depths are handled uniformly.
- **Section keyword appears inside a URL or email** (e.g. `skills@company.com`): the pattern has no word-boundary guard — `skills` inside that email would match. Consider whether a `\b` or end-of-token anchor is needed after `\s*{section}`.
- **Empty string input** to `_detect_sections("")`: should return `[]` without error; the regex search will simply find no matches.
