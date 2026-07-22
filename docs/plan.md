## Solution plan

**Issue:** Resume section detection fails on text with leading whitespace #147
https://github.com/ascherj/pathreview/issues/147

### Understand
Section detection fails because `_detect_sections` matches headers only at column 0 on each line. Indented lines (common in PDF text and test fixtures) do not match, so detected_sections is wrong or empty even when Education: and Skills: appear in the text. The fix is to allow optional leading whitespace on the line before each section name in the existing header patterns.

### Map
**File:** `resume_parser.py`
**Functions:** `_detect_sections`

### Plan
1. **Confirm reproduction** — Run `pytest tests/unit/test_resume_parser.py -k test_detect_sections` and verify it fails today: `metadata` / `_detect_sections` returns an empty or incomplete list for the indented fixture (lines with leading spaces before `Experience:`, `Education:`, `Skills:`).
2. **Update line-start patterns in `_detect_sections`** — In `ingestion/parsers/resume_parser.py`, change the four regexes so optional leading whitespace is allowed on the line before each section name (e.g. insert `\s*` immediately after `^` and after `\n`), without changing `SECTION_HEADERS` or the existing `:|-` suffix rules.
3. **Re-run unit tests** — Run the full `test_resume_parser.py` suite and confirm `test_detect_sections` passes and flush-left headers (no leading spaces) still match as before.
4. **Verify end-to-end metadata** — Call `ResumeParser.parse()` with the same indented sample from issue #147 and confirm `metadata["detected_sections"]` lists Experience, Education, and Skills (not only the helper in isolation).
5. **Capture edge cases in tests or notes** — Ensure behavior is clear for tabs vs spaces and multiple leading spaces (both should match); headers that appear mid-line without a preceding newline should still not match incorrectly.

### Inputs & outputs
**Input:** Raw resume text as a `str` passed to `_detect_sections` (directly in unit tests, or via `ResumeParser.parse()` after normalization). Relevant shapes include flush-left section headers (`Experience:` at column 0) and indented lines (leading spaces or tabs before `Experience:`, `Education:`, `Skills:`, etc.), as in PDF extraction and the `test_detect_sections` fixture.

**Output / change:** A `list[str]` of detected section names (title-cased entries from `SECTION_HEADERS`, deduplicated). After the fix, indented line-start headers match the same four patterns as flush-left ones, so `metadata["detected_sections"]` from `parse()` includes Experience, Education, Skills, and other recognized sections instead of staying empty or incomplete. **Code change only:** the four regex patterns inside `_detect_sections` in `ingestion/parsers/resume_parser.py` (optional `\s*` after `^` and after `\n`). **Unchanged:** `SECTION_HEADERS`, suffix rules (`:`, `|`, `-`), returned resume body text, and the rule that headers mid-line (no line start) must not match.

### Risks & unknowns
**What could go wrong**
- **False positives on indented prose** — Optional `\s*` before a header name still requires a line start (`^` or `\n`), but a line like `    See Experience: below` would now count as a section header. That may be rare in resumes but is a behavior change worth watching in the full test suite.
- **Over-permissive `\s*`** — In Python regex, `\s` includes newlines, so `^\s*experience` could theoretically skip blank lines between a line break and the header. That is usually desirable for PDF layout but could match headers farther from the preceding content than today’s flush-left rules.
- **Regressions on flush-left text** — A typo in only one of the four patterns (missing `\s*` after `\n` on pattern 3 vs 4) would fix the indented fixture partially and leave subtle bugs; all four patterns must stay in sync.
- **Pre-existing metadata quirks** — `list(set(detected))` drops section order and duplicate titles (e.g. both “Experience” and “Work Experience” matching the same block) are unchanged by this fix; callers that assumed sorted or stable ordering may still be surprised.

**What is still unsure**
- **Path through `parse()`** — Markdown runs `_strip_markdown` then `_detect_sections`; PDF joins page text with no per-line normalization. Reproduction used indented plain text; real PDF extracts may mix spaces, tabs, or odd breaks—whether `\s*` alone is enough for production PDFs is validated mainly by the unit fixture until more samples are tried.
- **Downstream use of `detected_sections`** — Empty metadata was the reported bug; it is unclear whether any review or profile flow depends on section order, completeness, or specific casing beyond what tests assert.
- **Scope of “mid-line”** — The plan assumes headers embedded in the same line as other words (no preceding newline) must not match; no dedicated test may exist for that invariant after the change.
- **Week 8 artifacts** — Reproduction commit link and JOURNAL blockers are still placeholders; CI or cohort checklist items tied to those links are not confirmed yet.

### Edge cases
- **Flush-left headers (regression)** — Section names at column 0 with `:`, `|`, or `-` suffixes must still match all four patterns; empty or wrong `detected_sections` on legacy/plain text is a failure.
- **Leading spaces and tabs** — One or many spaces, or tabs, before `Experience:`, `Education:`, `Skills:`, etc. at line start (PDF/fixture shape) must match the same as flush-left.
- **Blank lines before a header** — Optional `\s*` after `^` / `\n` may span blank lines; headers after PDF line breaks should still be detected without requiring column 0.
- **Mid-line headers (must not match)** — Text like `See Experience: below` or prose containing `Education:` without a line start must not be treated as section headers.
- **Indented “header-like” lines (behavior change)** — A line that is only indentation + `Experience:` at line start will now match; rare resume prose at line start with a known section name + suffix should be accepted as a known tradeoff.
- **All four patterns in sync** — Each regex must allow the same leading whitespace after `^` and after `\n`; partial fixes leave indented text working for some suffix styles only.
- **Unchanged semantics** — Duplicate section names still dedupe via `set`; order is not guaranteed; `SECTION_HEADERS` aliases (e.g. Work Experience vs Experience) behave as before.
- **Parse path** — Indented plain text after `_strip_markdown` (markdown resumes) and joined PDF page text without extra normalization should both populate `metadata["detected_sections"]` when line-start headers are present.