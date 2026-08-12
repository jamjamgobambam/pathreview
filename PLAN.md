## Solution plan

**Issue:** #147 — Resume section detection fails on text with leading whitespace
(https://github.com/ascherj/pathreview/issues/147)

### Understand

`_detect_sections()` in `ingestion/parsers/resume_parser.py` (lines 127–146) detects
resume sections by testing each keyword in `SECTION_HEADERS` against four regex
patterns per section, e.g.:

```python
rf"^{re.escape(section)}\s*[:|-]"
rf"\n{re.escape(section)}\s*[:|-]"
```

searched with `re.MULTILINE`, which makes `^` match right after every `\n` in the
string (not just at index 0).

**Root cause:** the patterns anchor the keyword *directly* against `^`/`\n` with no
`\s*` in between. `re.MULTILINE` is working correctly — the bug is that the pattern
itself requires the keyword to be the very next character after the line start. Text
extracted from PDFs (and the reproduction case in the issue) commonly has leading
indentation on every line, e.g. `"    education:"`. At that line's start, `^` matches
position 0 of the line, but the characters there are spaces, not `e` — so none of the
four patterns ever match, and `detected` stays empty for every section.

**Expected vs. actual:**
- Expected: `_detect_sections()` finds section keywords regardless of leading
  whitespace on the line (e.g. `"    Education:"` → detects `"Education"`).
- Actual: any line with leading whitespace before the keyword is invisible to all
  four patterns; `detected_sections` comes back `[]`.

### Map

Files I expect to touch:
- `ingestion/parsers/resume_parser.py` — `_detect_sections()` (lines 132–139): update
  the four regex patterns to allow optional leading whitespace after the anchor.
- `tests/unit/test_resume_parser.py` — add a new test for the indented-text case
  (the exact repro from the issue), alongside the existing `test_detect_sections`.
  The three tests already named in the issue
  (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`,
  `test_detect_sections`) currently fail against indented fixture text
  (`tests/conftest.py:sample_resume_text`, and inline indented text in the other two)
  — confirmed in Week 8 reproduction — and should pass once the regex is fixed. No
  fixture changes should be needed since the existing fixtures already use indentation.

I don't expect to touch `_parse_pdf`, `_parse_markdown`, or `_strip_markdown` — they
only call `_detect_sections()` and don't need to change.

### Plan

1. Update the four patterns in `_detect_sections()` to insert `\s*` (or `[ \t]*`)
   between the anchor (`^`/`\n`) and the escaped section keyword, so a line like
   `"    education:"` matches.
2. Re-run the three previously-failing tests plus `test_detect_sections` to confirm
   they now pass:
   `python3 -m pytest tests/unit/test_resume_parser.py -k "test_parse_single_column_resume_text or test_parse_resume_no_work_experience or test_detect_sections" -v`
3. Add a new unit test using the exact issue reproduction input (leading whitespace
   on every line, including blank-line-separated sections) to lock in this specific
   regression.
4. Run the full test file (`test_resume_parser.py`) to make sure no existing test
   (e.g. `test_parse_markdown_resume`, `test_strip_markdown_syntax`) regresses —
   markdown headers/content already get whitespace-stripped elsewhere, but I want to
   confirm the widened regex doesn't cause false-positive section matches inside
   body text.
5. Run `make check` (lint, format, typecheck) and `make test-unit` for the full suite.

### Inputs & outputs

**Function I'm changing:** `_detect_sections(self, text: str) -> list[str]`

**Existing behavior:** given resume text with section keywords flush against the
line start (no leading whitespace), returns the list of matched section names
(title-cased, deduplicated).

**New behavior:** given resume text where section keywords are preceded by leading
whitespace/indentation on their line (common in PDF-extracted and fixture text),
still returns the matched section names — same output shape and same matching rules
otherwise (still requires `:`, `|`, `-`, or end-of-line immediately after the
keyword).

**Test case to add** (mirrors the issue's reproduction):
```python
def test_detect_sections_with_leading_whitespace(self, parser):
    text = (
        "\n    John Smith\n    john@example.com\n\n"
        "    Education:\n    - B.S. Computer Science\n\n"
        "    Skills: Python\n"
    )
    sections = parser._detect_sections(text)
    sections_lower = [s.lower() for s in sections]
    assert "education" in sections_lower
    assert "skills" in sections_lower
```

### Risks & unknowns

1. **Over-widening the match.** Adding `\s*` after `^`/`\n` allows arbitrary amounts
   of leading whitespace, including within body text if a section keyword happens to
   appear indented mid-paragraph (e.g. a bullet point that starts with "Skills" as a
   regular word). This risk already exists today for non-indented text and isn't
   meaningfully increased by the fix, but I'll check the multi-page PDF test
   (`test_parse_multipage_pdf`) and markdown test still behave as expected.
2. **Tabs vs. spaces.** `\s` covers both, but I should confirm the fix handles tab
   indentation the same as space indentation (PDF extraction could plausibly produce
   either, though the issue only mentions spaces).
3. **Whether `\n` in the pattern still needs to be included alongside `^`.** With
   `re.MULTILINE`, `^` already matches after `\n`, so the `\n{...}` patterns look
   redundant with the `^{...}` ones. I won't remove them as part of this fix (out of
   scope / risk of behavior change unrelated to the reported bug) but it's worth a
   note for a future cleanup.

### Edge cases

- Section keyword indented with spaces: `"    Education:"` → should detect.
- Section keyword indented with tabs: `"\tEducation:"` → should detect.
- Section keyword with no indentation (existing behavior): `"Education:"` → should
  still detect (no regression).
- Section keyword appearing mid-sentence with leading spaces but not as an actual
  header, e.g. `"    I gained my education: at State University"` — this already
  would false-positive today for non-indented equivalents (`"education:"` inside a
  sentence at line start), so this fix doesn't introduce a new class of false
  positive; not in scope to fix separately.
- Blank lines between sections (already in the issue's repro and existing fixtures)
  — should not affect matching since each pattern only concerns a single line.
