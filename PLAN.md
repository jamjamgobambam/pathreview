# Solution plan

**Issue:** Resume section detection fails on text with leading whitespace (#147)

## Understand

The `_detect_sections()` method searches for resume section headers using regular expressions anchored to the beginning of a line (`^`). When resume text extracted from PDFs contains leading spaces before section headers, those patterns do not match. As a result, the parser returns an empty or incomplete `detected_sections` list even though valid section headers are present.

## Map

Files involved:

- `ingestion/parsers/resume_parser.py`
- `tests/unit/test_resume_parser.py`

Functions involved:

- `_detect_sections()`
- `ResumeParser.parse()`

Related tests:

- `test_parse_single_column_resume_text`
- `test_parse_resume_no_work_experience`
- `test_detect_sections`

## Plan

1. Review the regular expressions used in `_detect_sections()` to understand why indented section headers are ignored.
2. Modify the section detection logic so that optional leading whitespace is accepted before section headers.
3. Run the existing resume parser tests to verify that indented section headers are detected correctly.
4. Confirm that resumes without indentation continue to pass existing tests.

## Inputs & outputs

### Input

Resume text that may contain leading spaces before section headers.

### Output

`detected_sections` should correctly contain section names such as "Education", "Experience", and "Skills" regardless of indentation.

## Risks & unknowns

- Updating the regular expressions may accidentally match text that is not a section header.
- Additional resume formats may contain tabs or inconsistent spacing that require further testing.
- Existing parser behavior should remain unchanged for resumes that already work correctly.

## Edge cases

- Multiple leading spaces.
- Tabs before section headers.
- Empty resumes.
- Resumes without any recognizable section headers.
- Mixed formatting where some headers are indented and others are not.