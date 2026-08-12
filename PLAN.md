# Solution plan

**Issue:** Resume section detection fails on text with leading whitespace ([#147](https://github.com/ascherj/pathreview/issues/147))

### Understand
- **Root Cause:** In `ingestion/parsers/resume_parser.py`, the `_detect_sections` method uses regular expressions anchored directly to the beginning of a line (`^` or `\n`) followed immediately by section header strings (e.g., `^Experience`, `\nExperience`). When extracted PDF text or markdown text contains leading whitespace (such as margins, tab indents, or list paddings like `"  Experience:"` or `"\tEducation"`), the regex engine fails to match the section titles. Furthermore, `_strip_markdown` uses `re.sub(r"^#+\s+", "", content, flags=re.MULTILINE)` which fails to strip markdown headers if they are indented with leading spaces or tabs.
- **Expected Behavior:** `_detect_sections()` should reliably detect section headers regardless of leading tabs or spaces on the line. `_strip_markdown()` should strip header tags (`#`) even when preceded by leading whitespace.
- **Actual Behavior:** Any leading whitespace before section headers causes `_detect_sections()` to miss section titles entirely, resulting in an empty or incomplete `detected_sections` list in `ParseResult.metadata`.

### Map
Files and modules involved:
- [ingestion/parsers/resume_parser.py](file:///Users/EVOTECH/Desktop/pathreview/ingestion/parsers/resume_parser.py):
  - `ResumeParser._detect_sections()`: Update regular expressions to match optional leading whitespace (`^\s*` or `\n\s*`).
  - `ResumeParser._strip_markdown()`: Update header regex to support optional leading whitespace (`^\s*#+\s+`).
- [tests/unit/test_resume_parser.py](file:///Users/EVOTECH/Desktop/pathreview/tests/unit/test_resume_parser.py):
  - Add test cases covering leading spaces, tabs, mixed indentation, and multi-word headers.
  - Verify all unit tests pass cleanly.

### Plan
1. **Update Section Detection Regex in `ResumeParser._detect_sections()`**:
   Modify pattern definitions in `ingestion/parsers/resume_parser.py` to allow optional horizontal/vertical whitespace `\s*` (or `[\t ]*`) after line start anchors (`^` or `\n`).
2. **Fix Markdown Header Stripping in `ResumeParser._strip_markdown()`**:
   Update `_strip_markdown()` regex pattern from `r"^#+\s+"` to `r"^\s*#+\s+"` with `re.MULTILINE` to handle indented markdown headers.
3. **Execute & Validate Unit Tests**:
   Run pytest via `.venv/bin/pytest tests/unit/test_resume_parser.py` to verify that previously failing unit tests (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, `test_parse_markdown_resume`, `test_detect_sections`, `test_strip_markdown_syntax`, and `test_reproduce_issue_147_leading_whitespace`) pass.
4. **Expand Test Coverage for Edge Cases**:
   Add comprehensive unit test scenarios in `tests/unit/test_resume_parser.py` testing tab characters (`\t`), multi-space indents, multi-word section headers (`Work Experience`, `Technical Skills`), and mixed case formats.
5. **Code Formatting & Type Checking Verification**:
   Run pre-commit checks (`ruff`, `black`, `mypy`) to ensure code compliance and type safety across all updated files.

### Inputs & outputs
- **Inputs:** Resume text strings (extracted from PDF bytes via `PdfReader` or raw Markdown strings) containing leading spaces or tab characters preceding section titles (e.g., `"  Experience:"`, `"\tEducation"`, `"   ## Technical Skills"`).
- **Outputs:** A `ParseResult` object with `metadata["detected_sections"]` populated with standardized section title strings (e.g., `["Experience", "Education", "Skills"]`), and cleaned resume text with stripped markdown.

### Risks & unknowns
- **Risk 1: False Positive Section Header Matching:**
  - *Details:* Broadening regex matching with `\s*` could accidentally match occurrences of header words used in regular sentence bodies (e.g., `"  experience with Python and JavaScript"`).
  - *Mitigation:* Ensure patterns strictly require line endings (`$`) or header punctuation delimiters (`:`, `-`, `|`) immediately after section title words.
- **Risk 2: Multi-word Header Space Normalization:**
  - *Details:* Multi-word section headers like `"Work Experience"` or `"Technical Skills"` contain internal spaces.
  - *Mitigation:* Verify `re.escape()` preserves internal spaces while pattern `\s*` handles leading and trailing line whitespace.
- **Risk 3: Performance Impact on Large Documents:**
  - *Details:* Applying multiple regex searches per section header with `re.MULTILINE` over large text files could introduce minor overhead.
  - *Mitigation:* Keep regex patterns efficient and test runtime performance with pytest.

### Edge cases
- **Tab Characters (`\t`):** PDFs parsed into text frequently represent column offset margins as tabs rather than space characters.
- **Variable Indentation Depth:** 2, 4, or 8 space indents before section headers.
- **Header Delimiters:** Section headers ending with colons (`"  Experience:"`), hyphens (`"  Education -"`), vertical bars (`"  Skills |"`), or standalone line titles (`"  Experience"`).
- **Indented Markdown Headers:** Markdown titles with leading spaces before `#` tags (e.g., `"  # Experience"`).
- **Capitalization Variants:** Uppercase (`"  EXPERIENCE"`), Title Case (`"  Education"`), or lowercase (`"  skills"`).
