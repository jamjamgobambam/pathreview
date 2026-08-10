## Solution plan

**Issue:** Resume section detection fails on text with leading whitespace — https://github.com/ascherj/pathreview/issues/147

### Understand

**Root cause:** `ResumeParser._detect_sections()` (in `ingestion/parsers/resume_parser.py`)
builds four regex patterns per known section header, and every one of them anchors
directly at the start of a line (`^header`) or right after a newline (`\nheader`), with
no allowance for leading whitespace:

```python
patterns = [
    rf"^{re.escape(section)}\s*$",
    rf"^{re.escape(section)}\s*[:|-]",
    rf"\n{re.escape(section)}\s*$",
    rf"\n{re.escape(section)}\s*[:|-]",
]
```

Text extracted from PDFs, and any markdown resume with indented body text (the norm
for both), commonly preserves leading whitespace. A line like `"    Education:"` never
matches `^Education` or `\nEducation`, even though a human reading the same text would
immediately recognize it as a section header.

The identical anchoring mistake also lives in `_strip_markdown()`'s header-stripping
regex (`r"^#+\s+"`, `re.MULTILINE`) — an indented `"    # Header"` line is left
untouched. I found this myself while reproducing the issue; it's why the existing test
suite fails **6** tests locally, not just the 3 the issue names (see Map below).

**Expected vs. actual behavior:**
- *Expected:* `ResumeParser()._detect_sections("    Education:\n    Skills: Python")`
  returns `["Education", "Skills"]`.
- *Actual (today):* the same call returns `[]`.

**Blast radius (why this is worth fixing but isn't an emergency):** I traced
`detected_sections` downstream via `grep -rn "detected_sections"` across the non-test
codebase. It currently only reaches a `structlog` info line in
`ingestion/pipeline.py::ingest_resume` — it is not read by `StrategySelector.chunk()`
(branches only on `source_type`) and is not persisted by `_record_ingested_source`
(stores only `chunk_count`). So today's visible damage is silently-wrong
ingestion metadata/logs, not a broken review — but it's exactly the signal a future
feature (section-aware chunking, resume completeness scoring) would reasonably build
on, so it's worth fixing correctly now.

### Map

Files/functions involved:
- `ingestion/parsers/resume_parser.py`
  - `ResumeParser._detect_sections()` — the four pattern templates need their anchors
    relaxed.
  - `ResumeParser._strip_markdown()` — the header-stripping regex has the same bug.
- `tests/unit/test_resume_parser.py`
  - Already contains 5 tests that fail today because of this bug:
    `test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`,
    `test_detect_sections`, `test_parse_markdown_resume`, `test_strip_markdown_syntax`.
  - I added a 6th, `test_detect_sections_with_leading_whitespace`, as a minimal,
    isolated reproduction of the exact issue scenario (committed separately from this
    plan — see JOURNAL.md Week 8 entry for the commit link).
- No other files are involved. `grep -rn "_detect_sections\|_strip_markdown"` across
  the repo (excluding tests) shows both methods are only called from within
  `ResumeParser` itself (`_parse_pdf` and `_parse_markdown`) — no other class touches
  them directly.

### Plan

1. In `_detect_sections()`, change the anchor `^` to `^\s*` and `\n` to `\n\s*` in all
   four pattern templates, so a header can be preceded by leading whitespace on its
   line.
2. In `_strip_markdown()`, change `r"^#+\s+"` to `r"^\s*#+\s+"` so indented markdown
   headers are stripped the same as unindented ones.
3. Run `pytest tests/unit/test_resume_parser.py -v` and confirm all 6 currently-failing
   tests (the 5 pre-existing ones plus my new reproduction test) now pass, with zero
   regressions in the 5 tests that already pass today.
4. Run `make test-unit` (full unit suite) to confirm no other suite depends on the old,
   narrower matching behavior.
5. Update `PLAN.md`/`JOURNAL.md` to reflect the fix once implemented, and open the PR
   referencing issue #147.

### Inputs & outputs

- **Input:** raw resume text (`str`) passed into `_detect_sections(text)`, or markdown
  content (`str`) passed into `_strip_markdown(content)`. In practice this text
  originates either from `PdfReader.extract_text()` (PDF path) or directly from a
  markdown string (`_parse_markdown`), both of which may contain arbitrary leading
  whitespace per line.
- **Output:** `_detect_sections()` returns `list[str]` of detected section names
  (title-cased); `_strip_markdown()` returns the input `str` with markdown syntax
  removed. After the fix, both functions produce correct output regardless of leading
  whitespace on the relevant lines, and produce *identical* output to today for input
  that has no leading whitespace (the fix only adds matches, it doesn't remove any).

### Risks & unknowns

- **Risk — over-broad matching:** widening `^` to `^\s*` could in theory make a pattern
  match something it shouldn't (e.g. a section keyword appearing mid-sentence with
  incidental leading whitespace from something other than a header). Mitigated by the
  fact that the pattern still requires the header word to be immediately preceded only
  by whitespace back to the line start — it cannot match a header that appears after
  other non-whitespace text on the same line.
- **Risk — regression in already-passing tests:** need to re-verify the currently
  5-passing tests in `tests/unit/test_resume_parser.py` (e.g.
  `test_parse_multipage_pdf`, `test_pdf_parsing_error_handling`,
  `test_parse_preserves_text_content`) still pass unchanged after the fix, since they
  exercise the same two methods indirectly.
- **Unknown — real-world PDF extraction quirks:** `pypdf`'s `extract_text()` can
  produce unusual whitespace/line-break patterns beyond simple leading spaces (e.g.
  tabs, non-breaking spaces, or multi-column layouts that interleave text). `\s*`
  covers spaces/tabs/newlines but I haven't tested against a real multi-column PDF
  resume — flagging this as something to sanity-check manually with a sample PDF
  before considering the fix complete, not just the unit tests.
- **Unknown — PR #178:** another student opened PR #178 against the same issue with a
  similar regex-anchor fix. It's still open/unmerged as of my Week 7 check. Not a
  blocker for my own submission, but worth a quick recheck before I open my PR in case
  it merged first and the file has since changed upstream.

### Edge cases

- Leading whitespace of varying width (2 spaces, 4 spaces, a tab) before a header —
  `\s*` handles all of these since it matches any whitespace character, not a fixed
  count.
- A section header with **no** leading whitespace (today's working case) — must
  continue to match exactly as before; `\s*` matches zero-or-more, so this is
  unaffected.
- Blank lines or lines containing only whitespace between sections — should not be
  mistaken for a header themselves; the fix only touches the anchor, not the header-word
  match itself, so this shouldn't change.
- A section keyword appearing as part of a longer word or sentence (e.g. "professional
  experience working with clients") — should still only match when the keyword is at
  the start of a line (mod leading whitespace) followed by `\s*$` or `\s*[:|-]`, not
  mid-sentence; this behavior is unchanged by the fix and should be covered by
  re-running the existing non-header-only tests.
- Indented markdown headers of different levels (`#`, `##`, `###`) — `_strip_markdown`'s
  `^\s*#+\s+` should strip all of them regardless of indentation or header depth.
- Empty input string / resume text with no section headers at all — should continue to
  return `[]` / unmodified text, not error.

### Status: Implemented

Steps 1–4 are complete as of commit `ee9ffeb`:
- `_detect_sections()`'s four patterns and `_strip_markdown()`'s header regex now use
  `^\s*`/`\n\s*` anchors instead of bare `^`/`\n`.
- `tests/unit/test_resume_parser.py`: all 11 tests pass (was 6 failed / 5 passed).
- `make test-unit` (full suite): 48 failed / 381 passed, down from a 54-failed/375-passed
  baseline — a clean 6-test improvement with zero new failures. The 48 remaining
  failures are pre-existing and unrelated (bias detector, PII scrubber, review service,
  etc. — confirmed identical on the pre-fix commit via `git stash`).
- `make check` (ruff/black/mypy): passes on the touched file. Also fixed a pre-existing
  `B904` lint error in `_parse_pdf`'s except clause (missing `raise ... from e`) since
  pre-commit lints the whole file and was blocking the commit otherwise.
- **Real multi-column PDF sanity check (closes the "Unknown" above):** generated a
  genuine two-column PDF with `reportlab` (left column headers indented 4 spaces,
  right column headers indented 8 spaces, simulating column offset) and ran it through
  the real `pypdf` extraction path — not mocked. `pypdf.extract_text()` extracts by
  drawing order (whole left column, then whole right column; not interleaved
  line-by-line), and both columns' headers keep their leading whitespace. Pre-fix,
  `detected_sections` on this real PDF returned `[]`; post-fix, it correctly returns
  `['Experience', 'Skills', 'Education', 'Projects']` — all four headers across both
  columns. Confirms the fix generalizes beyond the plain-text/markdown fixtures.

### Mentor review: `\s*` vs `[ \t]*`

A review pass on the draft PR caught that `\s` matches newlines, not just
same-line spaces/tabs — broader than the issue actually calls for ("leading
whitespace" on the header's own line). Verified the real impact:

- **`_strip_markdown()`:** confirmed to be a genuine regression. `re.sub` consumes
  and deletes whatever `\s*` matched, so a blank line separating a paragraph from
  the next header was silently swallowed — `"Some intro text.\n\n# Header"` stripped
  to `"Some intro text.\nHeader"` instead of preserving the blank line. This isn't
  cosmetic: `_strip_markdown()`'s output *is* the parsed resume text (unlike
  `detected_sections`, which only feeds a log line), so this would have altered
  real ingested content for any markdown resume with normal header spacing.
- **`_detect_sections()`:** re-examined and confirmed this one is *not* actually
  affected the same way, despite first appearances. It uses `re.search` (no
  consumption/deletion), and `^` in `re.MULTILINE` anchors at every line start —
  so an unindented header on its own line always has a valid zero-width anchor
  right there, regardless of how many blank lines precede it. `\s*` vs `[ \t]*`
  is behaviorally identical here; changed it anyway for consistency with
  `_strip_markdown()` and to not rely on that anchor subtlety going forward.

**Fix:** swapped `\s*` for `[ \t]*` in both methods, so the anchor only reaches
across same-line horizontal whitespace, never newlines. Added two tests:
`test_detect_sections_with_blank_lines_before_header` (documents the anchor
behavior is unaffected) and `test_strip_markdown_preserves_blank_line_before_header`
(regression guard — fails against the `\s*` version, confirmed by testing both
against `git show`'d versions of the file). All 13 tests in
`test_resume_parser.py` pass; full suite is 48 failed / 383 passed (2 more passing
than before, matching the 2 new tests; same 48 pre-existing unrelated failures).
