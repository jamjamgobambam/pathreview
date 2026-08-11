# Solution plan

**Issue:** Resume section detection fails on text with leading whitespace — [ascherj/pathreview#147](https://github.com/ascherj/pathreview/issues/147)

## Understand

**Root cause.** `ResumeParser._detect_sections()` in `ingestion/parsers/resume_parser.py` builds four
regexes per known section name, and every one of them requires the section name to sit *immediately*
after a line boundary:

```python
patterns = [
    rf"^{re.escape(section)}\s*$",
    rf"^{re.escape(section)}\s*[:|-]",
    rf"\n{re.escape(section)}\s*$",
    rf"\n{re.escape(section)}\s*[:|-]",
]
```

`^` (with `re.MULTILINE`) and `\n` both anchor to the start of a line, and nothing in the pattern
allows indentation between that boundary and the section name. So a single leading space or tab in
front of `Experience:` makes the header invisible to the parser. Because the check is
all-or-nothing per section, an entire resume can come back with `detected_sections == []`.

There is a **second, coupled defect** on the markdown path. `_strip_markdown()` removes headers with
`re.sub(r"^#+\s+", "", content, flags=re.MULTILINE)` — also line-anchored. For an indented markdown
resume, `  ## Experience` keeps its `##`, so even after section detection is made
whitespace-tolerant, the line reads `## Experience` and still will not match. I verified this
locally: relaxing only `_detect_sections` leaves the indented-markdown case broken. Both patterns
have to be fixed for the issue to actually be closed.

**Expected vs. actual.** For a resume whose headings are indented (very common — PDF text extraction
frequently emits leading spaces, and hand-written markdown/plain-text resumes are often indented),
`parse()` should report `detected_sections` containing `Experience`, `Education`, `Skills`, etc.
Today it reports `[]`.

Measured with `scripts/repro_issue_147.py` on the current code:

| Resume variant | `detected_sections` |
|---|---|
| flush-left | `['Education', 'Experience', 'Skills']` |
| space-indented (2 spaces) | `[]` |
| tab-indented | `[]` |
| indented markdown (`  ## Experience`) | `[]` |

## Map

Files I expect to touch:

| File | Change |
|---|---|
| `ingestion/parsers/resume_parser.py` | The fix. `_detect_sections()` (lines ~128–146) and the header-stripping `re.sub` in `_strip_markdown()` (line ~102). |
| `tests/unit/test_resume_parser.py` | The regression tests. New `TestSectionDetectionLeadingWhitespace` class (already added as the reproduction); may fold cases into the existing `TestResumeParser` class before opening the PR. |
| `scripts/repro_issue_147.py` | Reproduction demo script. Written this week; I will likely delete it before opening the upstream PR so the diff stays minimal, keeping the coverage in the test file. |

Functions involved, in call order:

- `ResumeParser.parse()` → dispatches on `bytes` vs `str`
- `ResumeParser._parse_pdf()` / `ResumeParser._parse_markdown()` → both call `_detect_sections()`
- `ResumeParser._strip_markdown()` → markdown path only, runs before detection
- `ResumeParser._detect_sections()` → **the defect**
- module-level `SECTION_HEADERS` set (lines 9–23) → the vocabulary being matched

Read but *not* changing:

- `ingestion/pipeline.py` — `IngestionPipeline.ingest_resume()` (line 88) is the only production
  caller. It logs `detected_sections` and copies `parse_result.metadata` into the chunk metadata
  passed to `StrategySelector.chunk()`, so the blast radius of my change is metadata only.
- `api/routes/profiles.py` — worth knowing: the resume-upload endpoint does **not** use
  `ResumeParser`; it calls `PyPDF2` directly (line 61) and never computes `detected_sections`. So
  this bug is not reachable through the HTTP API today, which is why my reproduction is at the
  module/unit level rather than through the browser.

## Plan

1. **Lock in the reproduction.** Add `TestSectionDetectionLeadingWhitespace` to
   `tests/unit/test_resume_parser.py` with space-indented, tab-indented, and indented-markdown
   cases, plus a flush-left control and a false-positive guard. Confirm the three bug cases fail and
   the two guards pass. *(Done — this is the Week 8 reproduction commit.)*
2. **Make section detection whitespace-tolerant.** In `_detect_sections()`, replace the four
   line-anchored patterns with a single `re.MULTILINE` pattern that permits leading horizontal
   whitespace, roughly `rf"^[ \t]*{re.escape(section)}[ \t]*(?:$|[:|-])"`. Use `[ \t]` rather than
   `\s` deliberately: `\s` matches `\n`, so the existing `\s*$` can already run past blank lines,
   and I do not want to widen that. Collapsing four patterns to one also removes the now-redundant
   `\n`-anchored duplicates.
3. **Fix the markdown header strip.** Change `^#+\s+` to `^[ \t]*#+\s+` in `_strip_markdown()` so
   indented markdown headings are reduced to bare text before detection runs. This is what makes the
   `test_indented_markdown_resume_reports_sections` case pass, and it also fixes the *already
   failing* `test_strip_markdown_syntax` test.
4. **Verify no false positives and no regressions.** Run `make test-unit` and confirm the four
   previously failing whitespace-related tests in `tests/unit/test_resume_parser.py`
   (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`,
   `test_parse_markdown_resume`, `test_detect_sections`) now pass, that prose like
   "5 years of professional experience" is still not treated as a header, and that
   `tests/unit/test_readme_parser.py` is untouched.
5. **Run the quality gates and open the PR.** `make lint` and `make typecheck` (mypy runs with
   `disallow_untyped_defs` over `ingestion/`, so keep the annotations on any helper I extract), then
   write the PR against `ascherj/pathreview` from `setup/147-resume-whitespace-fail` referencing
   issue #147.

## Inputs & outputs

**Input.** Resume text reaching `ResumeParser.parse()` — either `bytes` (PDF, text extracted by
`pypdf`) or `str` (markdown/plain text). The characteristic that matters is per-line leading
whitespace: spaces, tabs, or a mix.

**Output.** `ParseResult.metadata["detected_sections"]`: a list of title-cased section names. After
the fix, indented resumes produce the same list their flush-left equivalent produces. The extracted
`text` itself, `page_count`, and `source_type` are unchanged — I am not touching text extraction, so
downstream chunking and embeddings see identical content. The only behavioral delta is that
`detected_sections` becomes non-empty in cases where it was wrongly empty, which improves the
`sections=` log line in `ingestion/pipeline.py` and the metadata carried onto chunks.

**Not changing.** The `SECTION_HEADERS` vocabulary, the PDF extraction path, the public method
signatures, or anything in `api/`.

## Risks & unknowns

- **Over-broadening into false positives.** The real danger of relaxing an anchor is matching
  mid-line text. If I reached for `\b` or `.*` instead of `^[ \t]*`, a line like
  "5 years of professional experience" would register as an Experience header. Mitigated by the
  explicit guard test `test_indented_header_does_not_create_false_positives`.
- **Overlapping vocabulary entries.** `SECTION_HEADERS` contains `experience`,
  `work experience`, `professional experience`, and `skills`/`technical skills`. A resume with
  `Professional Experience:` should report one section, not two. With `^[ \t]*` the bare
  `experience` pattern still cannot match that line (the text before it isn't whitespace), so I
  expect current behavior to hold — but this is exactly the kind of thing to assert rather than
  assume, so it gets a test.
- **Non-breaking spaces from PDF extraction.** `pypdf` sometimes emits `\xa0` or other Unicode
  whitespace where a PDF had indentation, and `[ \t]` does not match `\xa0`. I confirmed the gap is
  real for any line other than the first (the first line is incidentally saved by the trailing
  `.strip()` in `_strip_markdown`). The precise fix if I decide to cover it is `[^\S\n]*` — "any
  whitespace except a newline" — which I verified matches `\xa0` indentation while still refusing to
  span lines. Unknown: whether this is common enough in real PDFs to justify the less readable
  pattern. Falling back to plain `\s` is not an option; that reintroduces newline-spanning matches.
- **Pre-existing red test suite.** `tests/unit/test_resume_parser.py` has 5 failures on the current
  branch before I change anything, and `make lint` already reports 3 errors in that file's imports
  (unused `MagicMock`/`BytesIO`, unsorted imports). I need to keep my "before/after" comparison
  honest against that baseline and resist fixing unrelated lint in the same PR.
- **Non-deterministic output order.** `_detect_sections` ends with `list(set(detected))`, so the
  order varies between runs. My tests compare sets rather than lists to avoid flakiness. Whether to
  also sort the return value for stable logs is a judgment call I would rather raise in the PR than
  bundle in unasked.
- **Unknown: maintainer scope preference.** The markdown-strip change (sub-task 3) is technically a
  second file location within the same function family. I believe it is required to close the issue,
  and I will justify it explicitly in the PR description in case the maintainer wants it split.

## Edge cases

The fix should handle all of these gracefully:

- Headers indented with spaces (1, 2, 4, 8), with a tab, or with mixed tabs and spaces.
- Headers with trailing whitespace before the newline (`  Experience   `).
- Headers with the punctuation variants the current code already supports: `Experience:`,
  `Experience |`, `Experience -`, and bare `Experience` on its own line.
- Indented markdown headings at any level: `  # Experience` through `  ###### Experience`.
- Inline-style sections such as `  Skills: Python, JavaScript` where content follows the colon on
  the same line.
- Prose containing a section word mid-sentence — must **not** be detected.
- A resume genuinely missing a section: `detected_sections` should simply omit it and never raise.
  `test_parse_resume_no_work_experience` covers this.
- Empty string and whitespace-only input: returns an empty list, no exception.
- Case variations, since detection lowercases the text first: `EXPERIENCE`, `Experience`,
  `experience`.
- Flush-left resumes: must keep working exactly as before. This is the regression risk that matters
  most, and `test_flush_left_headers_are_detected` pins it.
