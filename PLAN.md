## Solution plan

**Issue:** Resume section detection fails on text with leading whitespace — https://github.com/ascherj/pathreview/issues/147

### Understand

**Root cause:** `_detect_sections()` in `ingestion/parsers/resume_parser.py` anchors section-header regexes at the start of a line with `^Section` or `\nSection` and does not allow characters between that anchor and the header word. Text from PDFs (and indented fixture strings) often includes leading spaces before headers like `Education:` / `Skills:`, so no pattern matches.

**Expected:** For indented resume text, `ParseResult.metadata["detected_sections"]` should include the headers that are present (e.g. `Education`, `Skills`).

**Actual (pre-fix):** `detected_sections` is `[]` even when those headers appear in the text. Confirmed with the issue sample via `scripts/reproduce_issue_147.py` (broken patterns → `[]`; fixed patterns → Education/Skills).

### Map

| Area | Path | Role |
|------|------|------|
| Bug site | `ingestion/parsers/resume_parser.py` → `_detect_sections()` | Regex patterns that miss indented headers |
| Constants | `SECTION_HEADERS` in same file | Names searched for |
| Call sites | `_parse_pdf()`, `_parse_markdown()` | Pass extracted text into detection |
| Tests | `tests/unit/test_resume_parser.py` | `test_detect_sections`, `test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, plus new whitespace repro test |
| Repro helper | `scripts/reproduce_issue_147.py` | Documents broken vs fixed behavior |

**Files expected to touch:**
1. `ingestion/parsers/resume_parser.py` (primary fix)
2. `tests/unit/test_resume_parser.py` (lock in regression coverage)
3. `scripts/reproduce_issue_147.py` (optional local reproduction helper)
4. `PLAN.md` / `JOURNAL.md` (course planning docs only)

### Plan

1. **Reproduce** — Run the issue sample locally; confirm old patterns return `[]` and note which tests fail without a fix.
2. **Adjust regexes** — In `_detect_sections()`, insert optional `\s*` after `^` and after `\n` in each header pattern so indentation is allowed.
3. **Keep match semantics** — Still require end-of-line or `:` / `|` / `-` after the header so body text like “education experience” is less likely to false-match.
4. **Regression test** — Add a unit test using the exact indented sample from issue #147 asserting `education` and `skills` appear in `detected_sections`.
5. **Verify** — Run `pytest tests/unit/test_resume_parser.py` (and the reproduction script) to confirm related tests pass.

### Inputs & outputs

**Inputs:** Resume text as `str` (markdown path) or text extracted from PDF bytes; may include leading whitespace on header lines.

**Outputs / changes:**
- `detected_sections` lists title-cased section names that appear as headers, even when indented.
- No change to `ParseResult.text` content or overall parse API.
- Unit tests pass for indented and flush-left headers.

### Risks & unknowns

- **False positives:** `\s*` before the header could match mid-line phrases if patterns are too loose — mitigated by keeping `[:|-]` / end-of-line constraints; watch multi-word headers in `SECTION_HEADERS` (e.g. `work experience`).
- **PDF layout quirks:** Some extractors insert odd whitespace or split headers across lines — `\s*` helps indentation but not split headers; out of scope unless tests reveal it.
- **Duplicate titles:** Detection still uses `list(set(detected))`, so order is unstable; fine for metadata, but don’t assert order in tests.
- **Pre-commit / lint:** Changing `raise ... from e` or formatting may be required when touching `resume_parser.py` (already seen with ruff B904).

### Edge cases

- Headers with spaces before the name (`    Education:`)
- Headers with trailing colon vs bare line (`Skills:` vs `Skills`)
- Multi-word headers (`Technical Skills`, `Work Experience`) with indentation
- Flush-left headers (must keep working — no regression)
- Resumes with no recognizable sections (still return `[]`, no crash)
- Mixed case headers (matching is on `text.lower()`)
