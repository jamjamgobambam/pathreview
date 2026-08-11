## Solution plan

**Issue:** [Resume section detection fails on text with leading whitespace](https://github.com/ascherj/pathreview/issues/147)

### Understand

**Root cause:** `_detect_sections()` in `ingestion/parsers/resume_parser.py` builds four regex patterns per section header — two anchored with `^` and two anchored with `\n`:

```python
rf"^{re.escape(section)}\s*$"
rf"^{re.escape(section)}\s*[:|-]"
rf"\n{re.escape(section)}\s*$"
rf"\n{re.escape(section)}\s*[:|-]"
```

Text extracted from PDFs via `pypdf` commonly preserves indentation, so lines arrive as `"    Experience:"` or `"\t Skills"`. None of the four patterns match because the section name is preceded by whitespace, so `detected_sections` always comes back empty.

A related bug exists in `_strip_markdown()`: the header-stripping regex `^#+\s+` also requires `#` at column 0, so markdown headers with leading whitespace are not stripped.

**Expected:** `_detect_sections()` returns a non-empty list when section headers are indented. `_strip_markdown()` removes `#` headers regardless of leading whitespace.  
**Actual:** `_detect_sections()` returns `[]` for any indented text; `_strip_markdown()` leaves `#` headers in place when they have leading whitespace.

**Confirmed locally:** 5 tests fail — `test_detect_sections`, `test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, `test_parse_markdown_resume`, `test_strip_markdown_syntax`.

### Map

Files to change:
- `ingestion/parsers/resume_parser.py`
  - `_detect_sections()` (lines 134–138): update 4 regex patterns — `^` → `^\s*`, `\n` → `\n\s*`
  - `_strip_markdown()` (line 102): update header pattern `^#+\s+` → `^\s*#+\s+`

Files to read but not change:
- `tests/unit/test_resume_parser.py` — 5 failing tests already cover the bug; no new tests needed unless a tab-indented edge case is uncovered
- `tests/conftest.py` — `sample_resume_text` fixture uses 4-space indentation, which is the exact input that triggers the bug

### Plan

1. **Update `_detect_sections()` patterns** — In `ingestion/parsers/resume_parser.py`, replace the four pattern strings inside the `patterns` list:
   - `rf"^{re.escape(section)}\s*$"` → `rf"^\s*{re.escape(section)}\s*$"`
   - `rf"^{re.escape(section)}\s*[:|-]"` → `rf"^\s*{re.escape(section)}\s*[:|-]"`
   - `rf"\n{re.escape(section)}\s*$"` → `rf"\n\s*{re.escape(section)}\s*$"`
   - `rf"\n{re.escape(section)}\s*[:|-]"` → `rf"\n\s*{re.escape(section)}\s*[:|-]"`

2. **Update `_strip_markdown()` header pattern** — In the same file, change the header-removal regex from `r"^#+\s+"` to `r"^\s*#+\s+"` (`re.MULTILINE` is already applied).

3. **Run the 5 failing tests** — Confirm all pass: `pytest tests/unit/test_resume_parser.py -v`.

4. **Run the full unit suite** — Confirm no regressions in the 5 currently-passing tests.

5. **Run linter and formatter** — `ruff check` and `black` to match codebase style before opening the PR.

### Inputs & outputs

**`_detect_sections(text: str) -> list[str]`**
- Input: plain-text string — after the fix, any amount of leading whitespace before a section header is tolerated
- Output: list of title-cased section names (e.g., `["Experience", "Education", "Skills"]`) — previously `[]` for indented input; now correctly populated
- No signature change; behavior change only

**`_strip_markdown(content: str) -> str`**
- Input: markdown string, possibly with leading whitespace before `#` headers
- Output: plain-text string with markdown syntax stripped — after fix, `#`-prefixed headers with leading whitespace are removed
- No signature change; behavior change only

### Risks & unknowns

- **`\s*` is greedy** — `^\s*` matches any amount of whitespace. If a section keyword somehow appeared mid-line after real content (not just whitespace), it would not match — but that is correct behavior. Verify with the existing test for `test_parse_preserves_text_content` that body lines like `"experience with React"` are not misclassified as section headers.
  - Investigation path: `ingestion/parsers/resume_parser.py` lines 134–138 after change; run `test_parse_preserves_text_content`.

- **`_strip_markdown()` scope creep** — The issue description names only `_detect_sections()`, but `_strip_markdown()` has the same root cause and its failure (`test_strip_markdown_syntax`) blocks `test_parse_markdown_resume` too. Both fixes are in the same file, one line each. I will mention this in the PR description to flag the expanded scope.
  - Investigation path: `ingestion/parsers/resume_parser.py` line 102.

- **`re.MULTILINE` interaction** — `^` with `re.MULTILINE` matches at the start of each line. Adding `\s*` after `^` still behaves correctly. Verify with a `\r\n` (Windows-style) line-ending input, since `pypdf` on Windows may produce CRLF text.

### Edge cases

1. **Tabs vs spaces** — `\s*` matches both. A header like `"\t\tEducation:"` must be detected. The existing fixtures use spaces; will verify tabs work after the fix by running `test_detect_sections` and checking the `\s*` pattern matches tab-indented input.

2. **Mixed indentation** — A document where some headers are flush and some are indented should correctly detect all of them. The `^\s*` pattern matches both `"Experience:"` (zero whitespace) and `"    Experience:"` (four spaces).

3. **Section keyword mid-line** — A body line like `"    I have experience with React"` must not be detected as a section. The patterns `^\s*experience\s*$` and `^\s*experience\s*[:|-]` require either nothing after the keyword or an immediate colon/dash, so mid-sentence mentions are safe.

4. **Empty or whitespace-only input** — `_detect_sections("")` and `_detect_sections("   \n  ")` must return `[]` without error. Adding `\s*` does not change this behavior.
