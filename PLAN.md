## Solution plan

**Issue:** Resume section detection fails on text with leading whitespace — [#147](https://github.com/ascherj/pathreview/issues/147)

### Understand

**Root cause.** `ResumeParser._detect_sections()` in
`ingestion/parsers/resume_parser.py` matches each known section header with four
regex patterns that anchor the header to the *exact* start of a line:

```python
rf"^{section}\s*$"        rf"^{section}\s*[:|-]"
rf"\n{section}\s*$"       rf"\n{section}\s*[:|-]"
```

Both anchors (`^` under `re.MULTILINE`, and the literal `\n`) require the header
word to be the first character of the line. But text extracted from PDFs — the
primary ingestion path (`_parse_pdf`) — routinely preserves leading spaces and
tabs. An indented header such as `"    Experience:"` therefore matches none of
the patterns.

**Expected vs. actual.**
- *Expected:* `_detect_sections("    Experience:\n    Education:")` returns
  `["Experience", "Education"]` — indentation is irrelevant to which sections a
  résumé contains.
- *Actual:* it returns `[]`. Verified directly: identical content is detected
  flush-left but not when indented (reproduction commit
  [`fa08842`](https://github.com/newairforces/pathreview/commit/fa08842a68b223aa42e4f08e1ab51dc626037d25)).

The failure is silent: `detected_sections` is stored in `ParseResult.metadata`
and only logged (`ingestion/pipeline.py:89`), so an empty result degrades
downstream review generation without raising an error.

### Map

Files involved:

- **`ingestion/parsers/resume_parser.py`** — `_detect_sections()` (the four
  patterns at lines ~140–145). This is the only production code that needs to
  change.
- **`tests/unit/test_resume_parser.py`** — home of the three failing tests
  (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`,
  `test_detect_sections`) plus the new regression test
  `test_detect_sections_with_leading_whitespace`. New coverage lands here.
- **`tests/conftest.py`** — `sample_resume_text` fixture (indented) drives one of
  the failing tests. Read-only reference; no change expected.

Not touched but confirmed as consumers (no change needed): `ingestion/pipeline.py`
(logs `detected_sections`), `_parse_pdf` / `_parse_markdown` (both call
`_detect_sections` and pass the result straight into `metadata`).

### Plan

1. **Make the anchors whitespace-tolerant.** Insert an optional run of
   horizontal whitespace after each line anchor — `^[ \t]*{section}...` and
   `\n[ \t]*{section}...`. Use `[ \t]*` (not `\s*`) so the match cannot leak
   across newlines and cause false positives on a following line.
2. **Keep the trailing boundary intact.** Preserve the `\s*$` and `\s*[:|-]`
   suffixes so a header still has to end the "field" — this prevents substring
   false positives like `"Work Experience Highlights"`.
3. **Turn the reds green.** Run the three named tests plus the new regression
   test; all four must pass.
4. **Add coverage.** Extend `test_detect_sections_with_leading_whitespace` (or
   add sibling cases) for tabs, mixed space/tab indentation, and a
   negative case asserting a mid-sentence occurrence is *not* falsely detected.
5. **Guard against regressions.** Run the full parser test file
   (`make test-unit` / `pytest tests/unit/test_resume_parser.py`) to confirm no
   previously-passing test breaks.

### Inputs & outputs

- **Input:** a résumé text string (from `_parse_pdf` or `_parse_markdown`), which
  may contain arbitrary leading horizontal whitespace on each line.
- **Output:** `_detect_sections()` returns a deduplicated `list[str]` of
  `.title()`-cased section names, now independent of indentation. Only the
  regex matching changes — the return type, dedup behavior, and `metadata`
  shape are unchanged, so no downstream contract shifts.

### Risks & unknowns

- **False positives from over-broad anchoring.** Relaxing the anchor could make a
  header match where it shouldn't. Mitigated by using `[ \t]*` (horizontal only)
  and keeping the `$` / `[:|-]` trailing boundary; step 4's negative test guards
  this explicitly.
- **`\s` already swallows `\r`.** Some PDFs emit CRLF. The trailing `\s*` handles
  `\r`, but I need to confirm the *leading* side handles `\r\n` correctly — a bare
  `\n` literal anchor won't see a line starting after `\r`. Worth verifying and,
  if needed, extending the anchor.
- **Multi-word headers overlap** ("experience" vs. "professional experience" vs.
  "work experience"). The existing `set(...)` dedup + `.title()` already collapse
  these; I'll confirm the relaxed patterns don't change which of the overlapping
  variants win.
- **Unknown:** whether any consumer treats an empty `detected_sections` as a
  meaningful signal (vs. a bug). Grep shows only logging today, so low risk, but
  I'll re-check before finalizing.

### Edge cases

- Headers indented with **spaces**, with **tabs**, and with **mixed** space/tab.
- Header on the **first line** of the text (no preceding `\n`).
- Header followed by `:`, `-`, `|`, or nothing (bare header line).
- **CRLF** (`\r\n`) line endings from PDF extraction.
- **Negative:** the header word appearing mid-sentence (e.g.
  `"...gained experience building..."`) must **not** be detected.
- Empty string / whitespace-only input → returns `[]` without error.
