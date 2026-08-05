## Solution plan

**Issue:** [Resume section detection fails on text with leading whitespace — https://github.com/ascherj/pathreview/issues/147]

### Understand
`_detect_sections()` in `ingestion/parsers/resume_parser.py` builds four regex patterns per section keyword:

```python
rf"^{re.escape(section)}\s*$",
rf"^{re.escape(section)}\s*[:|-]",
rf"\n{re.escape(section)}\s*$",
rf"\n{re.escape(section)}\s*[:|-]",
```

With `re.MULTILINE`, `^` matches the position immediately at the start of a line (position 0 of that line — no characters before it), and `\n{section}` requires the keyword to immediately follow a newline character. Neither allows for any spaces/tabs between the start of the line and the keyword.

**Expected:** a line like `"    Education:"` (4 leading spaces) is recognized as an `Education` header.
**Actual:** it's not — since the pattern requires the keyword literally at position 0 of the line, any leading whitespace makes the match fail. `detected_sections` comes back `[]` for any indented input, which is the common case for PDF-extracted text and for the test fixtures (which use indented triple-quoted strings).

### Map
- **`ingestion/parsers/resume_parser.py`** — `_detect_sections()` (lines ~127-146) is the only function that needs a code change. This is the single file to touch for the fix itself.
- **`tests/unit/test_resume_parser.py`** — no changes needed to make the 3 named tests pass, but I'll run the full file (not just the 3 named tests) to check for regressions in the other ~7 passing tests in this file.
- **`tests/conftest.py`** — `sample_resume_text` fixture (indented) is what feeds `test_parse_single_column_resume_text`; confirmed this is why that test currently fails too, no change needed here.
- Out of scope: `ingestion/pipeline.py`, `agent/`, `rag/` — none of these call `_detect_sections()` directly; this is a self-contained parsing bug.

### Plan
1. Update the four regex patterns in `_detect_sections()` to tolerate leading horizontal whitespace (spaces/tabs) before the section keyword — e.g. inserting `[ \t]*` right after the `^`/`\n` anchor in each pattern.
2. Simplify if possible: since `re.MULTILINE` already makes `^` match every line start (including right after a `\n`), the `\n{section}...` pattern variants are redundant with the `^{section}...` variants once whitespace tolerance is added — consider dropping the two `\n`-prefixed patterns to reduce duplication, but only if it doesn't change behavior (verify with tests before removing).
3. Run `pytest tests/unit/test_resume_parser.py -v` and confirm all tests pass, not just the 3 named in the issue.
4. Re-run the exact repro snippet from the issue manually and confirm `detected_sections` now returns `['Education', 'Skills']`.
5. Run the full unit test suite (`make test-unit` or `pytest tests/unit`) to check nothing outside this file broke (e.g. anything else that imports `ResumeParser`).

### Inputs & outputs
- **Input:** raw resume text (`str`) passed into `_detect_sections(text)`, which may have leading whitespace on any/all lines (from PDF extraction, or plain indented strings).
- **Output:** unchanged shape — `list[str]` of detected, title-cased section names (e.g. `['Education', 'Skills']`). The fix changes *which* inputs produce a non-empty list, not the output format.

### Risks & unknowns
- Need to make sure the whitespace allowance doesn't cause **false positives** — e.g. a section keyword appearing mid-sentence with only whitespace before it. Since the pattern still requires the *rest* of the line to be just the keyword (`\s*$`) or the keyword immediately followed by `:`/`|`/`-` (`\s*[:|-]`), this should stay safe — a sentence like `"...work Skills include..."` won't match because there's other text on the line, not just whitespace.
- `\t` (tabs) vs spaces — should confirm the fix handles both, since PDF extraction could plausibly emit either. `[ \t]*` handles both; `\s*` would also match newlines which could over-match across lines, so I'll deliberately use `[ \t]*`, not `\s*`, for the leading-whitespace piece.
- Unsure whether removing the redundant `\n`-prefixed patterns (step 2) is worth the risk of a subtle behavior change vs. just leaving 4 (now-partially-redundant) patterns — will decide based on whether tests still pass after removal; if unsure, leave them in for a smaller, safer diff.

### Edge cases
- Section keyword with leading spaces only (` Education:`) — should be detected.
- Section keyword with leading tabs (`\tSkills:`) — should be detected.
- Section keyword with no leading whitespace at all (existing passing behavior) — must still be detected (no regression).
- Section keyword as the very first line of the text (no preceding `\n`) — must still be detected (covered by the `^` anchor with `re.MULTILINE`, which matches position 0 too).
- Section keyword appearing mid-sentence, not as a real header (e.g. `"...discuss my Skills in..."`) — must NOT be falsely detected as a header.
- Empty input string — should return `[]` without erroring (existing behavior, don't break it).