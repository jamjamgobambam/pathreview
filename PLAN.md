## Solution plan

**Issue:** #147 — Resume section detection fails on text with leading whitespace

### Understand
When `resume_parser.py` processes text extracted from PDFs, it attempts to detect standard resume sections (like "Experience" or "Education") using regular expressions in the `_detect_sections()` method. Currently, these patterns strictly anchor to the absolute start of a line (`^`) or immediately following a newline character (`\n`). 

Because PDF text extraction often preserves leading indentation or whitespace (e.g., `\n    Education:`), the strict anchors fail to match the indented headers, returning an empty `detected_sections` list. 

The expected behavior: modify the regex patterns to tolerate optional leading horizontal whitespace (spaces or tabs) between the line anchor and the section name. 

**Root cause:** Overly strict regular expression anchors in `_detect_sections()` that do not account for leading indentation.

### Map
Files I expect to touch:
- `ingestion/parsers/resume_parser.py` — `_detect_sections()` function (line ~92): where the regex patterns are defined and executed. I will update the four patterns here.
- `tests/unit/test_resume_parser.py` — I will add a new unit test here specifically designed to pass an indented resume string to verify the fix, and ensure the existing `test_detect_sections` still passes.

### Plan
1. Open `ingestion/parsers/resume_parser.py` and locate the `patterns` list inside `_detect_sections()`.
2. Modify the four regex strings to include `[ \t]*` (optional space or tab characters) immediately after the `^` and `\n` anchors, but before `{re.escape(section)}`. 
   *(Note: I will use `[ \t]*` instead of `\s*` for the leading space, as `\s*` includes newlines and could cause unexpected multi-line capture issues).*
3. Run `make test-unit` to confirm the existing happy-path tests (like `test_detect_sections` and `test_parse_single_column_resume_text`) do not break with the broader regex.
4. Write a new test in `tests/unit/test_resume_parser.py` called `test_detect_sections_with_indentation` (see Inputs & outputs below).
5. Run `make test-unit` again to confirm my new test successfully catches the extracted sections.
6. Run `make check` to ensure `ruff` and `black` formatting rules are satisfied before finalizing the branch.

### Inputs & outputs
**Function I'm changing:** `_detect_sections(self, text: str) -> list[str]`

**Existing happy path:**
- Input: `"\nExperience:\nStandard text"`
- Output: `['Experience']`

**New behavior (indented case):**
- Input: `"\n    Experience:\n    Standard text"`
- Expected output: `['Experience']` (Currently returns `[]`)

**Test I'll write:**
```python
def test_detect_sections_with_indentation(self, parser):
    """Test section detection handles leading whitespace and indentation."""
    text = (
        "\n    John Smith\n"
        "    john@example.com\n\n"
        "    Education:\n"
        "    - B.S. Computer Science\n\n"
        "    Skills: Python\n"
    )
    sections = parser._detect_sections(text)
    
    assert isinstance(sections, list)
    sections_lower = [s.lower() for s in sections]
    assert "education" in sections_lower
    assert "skills" in sections_lower

### Risks & unknowns
1. **Using `\s*` vs `[ \t]*`:** The existing pattern uses `\s*` after the section name. If I use `\s*` *before* the section name, it might greedily swallow subsequent newlines if a document is formatted strangely. I need to verify if `[ \t]*` is safer for catching purely horizontal indentation.
2. **False positives:** By loosening the anchor restrictions, could the parser accidentally match a bullet point that happens to start with a section name? (e.g., `  - Experience with Python`). The presence of the newline anchor and the lack of a preceding hyphen in the pattern should prevent this, but I must rely on the unit tests to confirm.

### Edge cases
- Headers indented with tabs instead of spaces: should be captured successfully.
- Headers with extreme indentation (e.g., centered text): should be captured successfully.
- Inline mentions of section names (e.g., "I have 5 years of experience"): should continue to be ignored, as they do not immediately follow a newline and indentation.
