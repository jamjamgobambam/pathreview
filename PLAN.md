# Week 8 — Issue Reproduction & Solution Planning

## Issue

**Issue:** #147 – Resume section detection fails on text with leading whitespace

**Issue Link:** https://github.com/ascherj/pathreview/issues/147

---

# 1. Issue Reproduction

## Description

The resume parser fails to detect common resume section headers when the extracted text contains leading whitespace before the section names. This commonly occurs when text is extracted from PDF resumes, where indentation is preserved.

The `_detect_sections()` function currently expects section headers such as `Education`, `Skills`, and `Experience` to begin immediately at the start of a line. When spaces precede these headers, no match is found and the parser returns an empty list of detected sections.

---

## Steps to Reproduce

```python
from ingestion.parsers.resume_parser import ResumeParser

r = ResumeParser()

res = r.parse("""
    John Smith
    john@example.com

    Education:
    - B.S. Computer Science

    Skills: Python
""")

print(res.metadata["detected_sections"])
```

### Observed Result

```python
[]
```

### Expected Result

```python
["Education", "Skills"]
```

---

# 2. Current Code Investigation

Relevant file:

```
ingestion/parsers/resume_parser.py
```

Relevant function:

```
_detect_sections()
```

The function iterates through predefined section names stored in `SECTION_HEADERS` and searches for each using regular expressions.

Current patterns:

```python
rf"^{re.escape(section)}\s*$"
rf"^{re.escape(section)}\s*[:|-]"
rf"\n{re.escape(section)}\s*$"
rf"\n{re.escape(section)}\s*[:|-]"
```

These expressions require the section header to begin immediately after the beginning of the line or immediately after a newline.

---

# 3. Root Cause Analysis

The parser assumes every section header begins at column 0.

However, PDF extraction frequently preserves indentation, producing text such as:

```
    Education:
```

instead of

```
Education:
```

Because the regular expressions do not allow optional leading whitespace, the parser fails to recognize these section headers.

As a result:

- no section headers are matched
- `detected_sections` becomes an empty list
- downstream processing loses useful resume structure

---

# 4. Planned Solution

The implementation will update the regular expression patterns used by `_detect_sections()` so they accept optional leading whitespace before each section header.

The modification should preserve the current matching behavior for resumes that already work while extending support for indented text extracted from PDF documents.

---

# 5. Files Expected to Change

Primary file:

```
ingestion/parsers/resume_parser.py
```

Possible additional files:

- parser unit tests
- resume parser test fixtures (if present)

---

# 6. Implementation Tasks

1. Reproduce the issue using the provided example.
2. Inspect `_detect_sections()` and existing regex patterns.
3. Modify the regex patterns to support optional leading whitespace.
4. Verify existing behavior for non-indented resumes.
5. Test resumes containing leading spaces before section headers.
6. Run the project's test suite.
7. Commit changes and prepare a pull request.

---

# 7. Risks

- Making the regular expressions too permissive could detect text that is not actually a section header.
- Changes must preserve detection for existing resumes.
- All current parser behavior should remain unchanged except for supporting leading whitespace.

---

# 8. Edge Cases

The updated solution should correctly handle:

- multiple spaces before section headers
- tab indentation
- blank lines before headers
- headers ending with a colon
- headers without punctuation
- mixed uppercase and lowercase headers
- multiple occurrences of the same section
- resumes that contain no recognizable sections

---

# 9. Testing Plan

Manual testing:

- Resume without indentation
- Resume with four leading spaces
- Resume using tabs
- Resume containing multiple section headers
- Resume with no section headers

Expected outcome:

- Previously supported resumes continue to work.
- Indented section headers are correctly detected.
- `detected_sections` contains the expected section names.

---

# 10. Success Criteria

The issue will be considered resolved when:

- resumes containing indented section headers are correctly parsed
- `detected_sections` includes headers such as Education and Skills
- existing functionality remains unchanged
- all relevant tests pass successfully