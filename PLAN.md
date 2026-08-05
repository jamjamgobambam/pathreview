## Solution plan

**Issue:** Resume section detection fails on text with leading whitespace — https://github.com/ascherj/pathreview/issues/147


### Understand
`_detect_sections()` in `ingestion/parsers/resume_parser.py` matches section headers
with regexes that are linked to line start (`^header`) or after a newline (`\nheader`), with
no built in buffer for leading whitespace.
- **Expected:** an indented line like `    Education:` is detected as "Education".
- **Actual:** the leading spaces block every pattern, so `_detect_sections()` returns
  `[]` and `metadata['detected_sections']` is empty for any indented resume.

Reproduced by three failing tests in `tests/unit/test_resume_parser.py`
(`test_detect_sections`, `test_parse_single_column_resume_text`,
`test_parse_resume_no_work_experience`), which feed indented text and fail on
`assert 0 > 0 where 0 = len([])` and `python -c "from ingestion.parsers.resume_parser import ResumeParser; r = ResumeParser(); res = r.parse('\n    John Smith\n    john@example.com\n\n    Education:\n    - B.S. Computer Science\n\n    Skills: Python\n'); print(res.metadata['detected_sections'])"` which gave me the result []

### Map
- **`ingestion/parsers/resume_parser.py`** — `_detect_sections()` (~line 127) and its
  `patterns` list (~lines 134–139) This is where I expect the fix to go 
- **`tests/unit/test_resume_parser.py`** — once fixed, the three failing tests should pass 

### Plan
1. Fix `_detect_sections()` to allow leading whitespace either anchor with `^\s*`
   or strip each line before matching.
2. Run the tests and confirm they pass.
3. Add tests for indented and mixed-indentation input.
4. Check indented body text isn't misdetected as a header

### Inputs & outputs
- **Input:** a resume `text` string whose lines may have leading whitespace.
- **Output:** `_detect_sections()` returns the correct section names (still
  `list[str]`); `metadata['detected_sections']` is populated for indented input.

### Risks & unknowns
- Changing the code could make indented body lines match a header word by mistake 
- Unsure whether real PDF text uses tabs or non-breaking spaces (`\xa0`) `\s` covers
  tabs but not `\xa0`.

### Edge cases
- Space and tabindented headers (`    Education:`).
- Header with vs. without a trailing colon.
- Header on the very first line (no preceding newline).
- Indented non-header text containing a header word must NOT match.
- Empty or whitespace-only input should return `[]` without error.