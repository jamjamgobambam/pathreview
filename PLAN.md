# Solution plan

**Issue:** Resume parser raises `IndexError` on resumes with no work experience section (https://github.com/ascherj/pathreview/issues/1)

### Understand
The `ResumeParser` class processes resumes in PDF and Markdown formats. When extracting section details, downstream consumer logic or parser helper methods assume an `experience` section entry always exists. Attempting to access `sections['experience'][0]` on a resume belonging to a new graduate or student without work history causes an unhandled `IndexError` or `KeyError` exception. The expected behavior is for the parser to safely return empty defaults or check bounds before indexing so the ingestion pipeline can process experience-free resumes without crashing.

### Map
The primary files involved are:
- `ingestion/parsers/resume_parser.py`: Contains `ResumeParser`, `_parse_pdf`, `_parse_markdown`, and `_detect_sections`.
- `tests/unit/test_resume_parser.py`: Unit test suite where reproduction tests and edge cases will be validated.

### Plan
1. **Reproduce via Unit Test**: Write a dedicated unit test in `tests/unit/test_resume_parser.py` passing a resume string/bytes lacking any work experience section and asserting that `parse()` returns a valid `ParseResult` without raising `IndexError`.
2. **Implement Defensive Bounds Checks**: Update `ingestion/parsers/resume_parser.py` to check for key existence and verify non-empty list length before accessing index 0 on detected sections.
3. **Provide Default Fallback**: Ensure `detected_sections` or extracted experience entries default to an empty list `[]` when absent.
4. **Verification**: Run Pytest across unit tests to confirm all existing parser tests pass and no regression occurs.

### Inputs & outputs
- **Inputs**: Resume content (PDF bytes or Markdown string) without any work experience section.
- **Outputs**: A `ParseResult` object containing extracted text, metadata with `detected_sections` (excluding experience or mapping it safely), and `page_count` without raising exceptions.

### Risks & unknowns
- **Risk**: Overly restrictive section matching in `_detect_sections` might misidentify other section headers (e.g. "Projects" or "Education") as experience, masking missing sections.
- **Investigation Path**: Inspect `SECTION_HEADERS` and regex patterns in `_detect_sections` in `ingestion/parsers/resume_parser.py` to ensure section keys match strictly.

### Edge cases
- Resume containing zero detected sections (completely blank document or plain name only).
- Resume with "Experience" header present but 0 bullet points under it.
- Markdown resume using unconventional heading formatting (e.g. `# Work History` instead of `## Experience`).
