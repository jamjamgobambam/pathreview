## Solution plan

**Issue:** Resume section detection fails on text with leading whitespace ([#147](https://github.com/ascherj/pathreview/issues/147))

### Understand
`ResumeParser._detect_sections()` lowercases extracted resume text and checks each known section header with regexes anchored at the start of a line, such as `^education` or `\neducation`. PDF text extraction often preserves indentation before visible section headers, so inputs like `    Education:` do not match any pattern.

Expected behavior: indented resume headers such as `Education:` and `Skills:` should be included in `metadata["detected_sections"]`.

Actual behavior: the owner reproduction returns `[]`, so downstream review generation loses section awareness.

### Map
Files I expect to touch:

- `ingestion/parsers/resume_parser.py` for the section-header regex logic.
- `tests/unit/test_resume_parser.py` for a regression test covering indented headers.
- `journal.md` for the Week 8 reproduction notes.
- `PLAN.md` for this planning document.

### Plan
1. Update `_detect_sections()` so section-header patterns allow horizontal whitespace after the start of a line or after a newline.
2. Preserve current support for headers with no punctuation, `:`, `-`, and multi-word headers like `Technical Skills`.
3. Add or convert the reproduction test so it passes once indented `Education:` and `Skills:` are detected.
4. Run the focused resume parser test file and then the unit suite if time permits.
5. Review the output order/deduping behavior so the fix does not introduce duplicate section names.

### Inputs & outputs
Input: resume text from Markdown strings or extracted PDF text, including section headers that may have leading spaces or tabs.

Output: `ParseResult.metadata["detected_sections"]` should include the matched resume sections even when the headers are indented.

### Risks & unknowns
Allowing whitespace in the regex could make detection too permissive if normal content lines look like headers. The fix should still require a known header name and a line-header shape instead of matching arbitrary words inside bullet content.

The current implementation returns `list(set(detected))`, so ordering is nondeterministic. I do not plan to solve ordering unless it blocks the whitespace fix.

### Edge cases
- Headers with spaces before the header name, including tabs.
- Headers followed by `:`, `-`, or only whitespace.
- Multi-word section headers such as `Work Experience:` and `Technical Skills:`.
- Uppercase or mixed-case headers.
- Existing non-indented headers should continue to work.
