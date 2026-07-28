## Solution plan

**Issue:** Issue: #147 — Resume section detection fails on text with leading whitespace (https://github.com/ascherj/pathreview/issues/147)

### Understand

When pypdf extracts text from PDFs, it frequently preserves physical layout formatting as literal spaces or tabs. In ingestion/parsers/resume_parser.py, the _detect_sections() function uses regex patterns strictly anchored to the start of a line (^) or immediately following a newline (\n) with no allowance for leading whitespace. Consequently, indented headers (e.g., \n    Experience:) fail to match, resulting in an empty list of detected sections.

The expected behavior: the regex patterns must allow for optional whitespace (\s*) immediately following the line start or newline anchors, so that headers are successfully detected regardless of their indentation level.

**Root cause:** Missing whitespace tolerance (\s*) after the anchors in the regex patterns within the _detect_sections() function.

### Map

Files I expect to touch:

- **ingestion/parsers/resume_parser.py** — _detect_sections() function (line ~99): This is where the patterns list is defined. I will modify the four regex strings here.

- **tests/unit/test_resume_parser.py** — The testing file containing test_parse_single_column_resume_text, test_parse_resume_no_work_experience, and test_detect_sections. I will rely on these existing tests, which already simulate the leading whitespace, to verify my fix.

### Plan

1. Read ingestion/parsers/resume_parser.py and locate the patterns list inside the _detect_sections() function.

2. Modify the four regex patterns to inject \s* directly after the ^ and \n anchors. For example, changing rf"^{re.escape(section)}\s*[:|-]" to rf"^\s*{re.escape(section)}\s*[:|-]".

3. Run pytest tests/unit/test_resume_parser.py to confirm that the three previously failing section detection tests now pass with the relaxed regex.

4. Run make test-unit to confirm this regex change doesn't inadvertently break any other parsing logic across the system.

5. Run make check (or the equivalent linting/formatting command) to verify the code is clean and adheres to project standards.

### Inputs & outputs

Function I'm changing: _detect_sections(self, text: str) -> list[str]

**Existing happy path:**

Input: String with flush-left headers (e.g., "\nExperience:\n")
Output: ['Experience']

**New behavior (indented case):**

Input: String with spaces/tabs before the header (e.g., "\n    Experience:\n")
Expected output: ['Experience']

**Test I'll verify:**
The issue notes that test_detect_sections is currently failing. I will use the existing test structure around line 140 in tests/unit/test_resume_parser.py, which already passes in a string with indented headers:

def test_detect_sections(self, parser):
    text = """
        Experience:
        Senior Developer at TechCorp
    """
    sections = parser._detect_sections(text)
    assert isinstance(sections, list)
    assert len(sections) > 0  # This will pass once \s* is added

### Risks & unknowns

1. Will \s match unintended newline characters? In regex, \s matches spaces, tabs, and newlines. Because we are anchoring with ^ and \n, the \s* will just consume extra empty space at the start of a line. However, I need to ensure that the re.MULTILINE flag doesn't cause unexpected cross-line matching behavior when \s* is introduced.

2. Non-breaking spaces: Does pypdf output standard spaces ( ), or does it sometimes output non-breaking spaces (\xa0) during extraction? The \s character class should catch both, but it is a potential unknown if specific PDFs continue to fail after the fix.

### Edge cases

1. **Inline keyword usage:** A sentence like "I have 5 years of experience" mid-paragraph should not be falsely flagged as a header. The regex prevents this because the trailing $ or [:|-] tokens demand that the word is formatted like a title, not just inline text.

2. **Extreme indentation:** A resume where headers are center-aligned (e.g., 20 spaces before the word "Education"). The \s* token handles this gracefully since it quantifies to zero or an infinite amount of leading whitespace.