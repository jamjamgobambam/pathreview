## Solution plan

**Issue:** [Resume section detection fails on text with leading whitespace](https://github.com/ascherj/pathreview/issues/147)

### Understand

**Root cause:** `_detect_sections()` in `ingestion/parsers/resume_parser.py` (line 127) looks for section headers ("Experience", "Education", "Skills", etc.) using regex patterns anchored at the very start of a line:

```python
patterns = [
    rf"^{re.escape(section)}\s*$",
    rf"^{re.escape(section)}\s*[:|-]",
    rf"\n{re.escape(section)}\s*$",
    rf"\n{re.escape(section)}\s*[:|-]",
]
```

`^` and `\n` require the header text to begin at column 0 of a line, with zero tolerance for whitespace in between. Text pulled from PDFs (and any resume that isn't perfectly flush-left) commonly has leading indentation, so a line like `"    Education:"` matches none of these patterns.

**Expected behavior:** an indented resume like `"\n    Education:\n    - B.S. CS\n"` should return `detected_sections` containing `Education`.

**Actual behavior:** `detected_sections` comes back completely empty (`[]`) for any resume text where headers are indented, even though a human reader can clearly see the sections.

### Map

- `ingestion/parsers/resume_parser.py` — `_detect_sections()` (line 127), specifically the four regex patterns at lines 132-138. This is the only function whose logic needs to change.
- `tests/unit/test_resume_parser.py` — the test file for this module. Already added `test_detect_sections_with_leading_whitespace` here to reproduce the bug; several existing tests (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, `test_detect_sections`) also touch indented text and are currently failing for the same underlying reason.
- `tests/conftest.py` — `sample_resume_text` fixture (indented), used by `test_parse_single_column_resume_text`. Not touched directly, but relevant context for why that test is affected.

Files I expect to touch: `ingestion/parsers/resume_parser.py` and `tests/unit/test_resume_parser.py`. No other files should need to change — nothing calling `_detect_sections()` depends on its exact regex internals, and its signature (`text: str -> list[str]`) stays the same.

### Plan

1. Reproduce the bug with a test first (done) — added `test_detect_sections_with_leading_whitespace`, confirmed it fails against the current code.
2. Apply the regex fix in `_detect_sections()`: insert `\s*` right after each `^`/`\n` anchor so leading whitespace is allowed but not required:
   ```python
   patterns = [
       rf"^\s*{re.escape(section)}\s*$",
       rf"^\s*{re.escape(section)}\s*[:|-]",
       rf"\n\s*{re.escape(section)}\s*$",
       rf"\n\s*{re.escape(section)}\s*[:|-]",
   ]
   ```
3. Re-run `test_detect_sections_with_leading_whitespace` and confirm it now passes.
4. Re-run the full test file (`pytest tests/unit/test_resume_parser.py -v`) and confirm the other tests affected by the same bug — `test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, `test_detect_sections` — also pass.
5. Run `make check` (ruff, black, mypy) to confirm the change is clean and introduces no new type/lint issues, then update `JOURNAL.md` and open the PR referencing issue #147.

### Inputs & outputs

**Input:** raw resume text (`str`) as extracted from a PDF, Markdown file, or plain text — potentially containing leading whitespace/indentation on any line, including section header lines.

**Output:** `_detect_sections()` returns a deduplicated `list[str]` of detected section names (e.g. `["Education", "Skills", "Experience"]`), title-cased. After the fix, this list should include a section whenever its header appears on a line — regardless of how much leading whitespace precedes it — matching what it already does for flush-left text today.

### Risks & unknowns

- **Over-matching:** `\s*` after `^`/`\n` is intentionally permissive (any amount of whitespace, including none). Risk is low since section names are still matched exactly via `re.escape(section)` — only leading whitespace before the name becomes tolerated, not extra/different characters.
- **Overlap with an existing open PR:** issue #147 already has a linked PR (#178) proposing a similar fix (also widening `^`/`\n` to `^\s*`/`\n\s*`, plus a similar fix in `_strip_markdown()`). I'm writing my implementation independently and only comparing against #178 afterward as a sanity check, since grading is based on my own artifacts — but there's a chance #178 merges first and the issue closes before my PR is up. If that happens, I'll pick a different open issue rather than treat this as wasted effort, since the repro → fix → test exercise still counts.
- **Whitespace beyond plain spaces:** unsure whether tabs or other whitespace characters need distinct handling — Python's `\s` already covers tabs, so this is expected to be fine, but worth a quick manual check rather than assuming.

### Edge cases

- Section header with no leading whitespace at all (flush-left) — must keep working exactly as before.
- Section header with multiple levels of indentation (e.g. nested under a sub-heading) — should still be detected.
- Section header preceded only by blank lines (no whitespace on the header's own line) — already handled today, must not regress.
- Text where a section name appears indented but *not* as a header (e.g. mentioned mid-sentence, like "my education includes...") — should not be falsely detected; this is unaffected by the fix since the patterns still require the header to be anchored to a line start (now with optional leading whitespace) and match the section name specifically, not embedded anywhere.
- Empty string or text with no section headers at all — should still return `[]`, not error.
