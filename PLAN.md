# Solution plan

**Issue:** Resume section detection fails on text with leading whitespace

**Link:** https://github.com/ascherj/pathreview/issues/147

### Understand

The resume parser should detect common section headings such as `Education:` and `Skills:` even when extracted resume text preserves indentation before those headings. The current issue appears when section detection expects the heading text to begin at the start of the line. In real PDF extraction output, headings can be preceded by spaces, so valid sections may be omitted from `metadata["detected_sections"]`.

Expected behavior: indented section headings should be detected the same way as non-indented headings.

Actual behavior before the fix: headings such as `    Education:` and `    Skills:` are missed, producing incomplete section metadata.

### Map

Files involved:

- `ingestion/parsers/resume_parser.py`: contains `ResumeParser._detect_sections()` and markdown cleanup logic.
- `tests/unit/test_resume_parser.py`: contains unit coverage for resume parsing and section detection.
- `JOURNAL.md`: records the Week 8 reproduction summary and deliverable links.

Primary function involved:

- `ResumeParser._detect_sections(text: str) -> list[str]`

Related helper:

- `ResumeParser._strip_markdown(content: str) -> str`

### Plan

1. Add a focused regression test in `tests/unit/test_resume_parser.py` using resume text where `Education:` and `Skills:` are indented.
2. Confirm the test reproduces the issue against the original detection behavior.
3. Update `_detect_sections()` in `ingestion/parsers/resume_parser.py` so section header regexes allow optional whitespace after the line-start anchor.
4. Keep the regex anchored to the beginning of each line to avoid detecting section words inside normal body sentences.
5. Run `python -m pytest tests/unit/test_resume_parser.py` to verify the regression and existing resume parser behavior.

### Inputs & outputs

Input: resume text from Markdown or PDF extraction, including lines that may start with whitespace before a known section heading.

Output: `ParseResult.metadata["detected_sections"]` should include recognized sections such as `Education` and `Skills` when those headings are indented, while preserving the existing parsed text and metadata shape.

### Risks & unknowns

- `ingestion/parsers/resume_parser.py`: loosening the regex too much could classify ordinary body text as a section heading. The fix should only allow leading whitespace while preserving line-start anchoring.
- `tests/unit/test_resume_parser.py`: section order is not stable because `_detect_sections()` removes duplicates with a set, so tests should assert membership rather than exact order.
- PDF extraction output can vary by source document. The current plan covers leading spaces before headings, but future parser work may need to handle bullets, all-caps headings, or unusual punctuation.

### Edge cases

- Headings with spaces before the section name, such as `    Education:`.
- Headings without indentation, such as `Education:`.
- Headings with trailing punctuation, such as `Skills: Python` or `Experience -`.
- Body sentences that mention section names should not be detected unless they appear in a heading-like line position.
- Markdown headings with indentation should still have markdown syntax stripped before section detection.
