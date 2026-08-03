## Solution plan

**Issue:** [Issue #147: Resume section detection fails on text with leading whitespace](https://github.com/ascherj/pathreview/issues/147)

### Understand

The `resume parser` is expected to parse section headers in resume. However, because of indentations (leading whitespaces), the section headers are not being detected by the parser.
```py
from ingestion.parsers.resume_parser import ResumeParser
r = ResumeParser()
res = r.parse('\n    John Smith\n    john@example.com\n\n    Education:\n    - B.S. Computer Science\n\n    Skills: Python\n')
print(res.metadata['detected_sections'])
# observed: []  (expected: Education, Skills)
```

### Map

Files/functions/tests involved:
- `_detect_sections()` in `ingestion/parsers/resume_parser.py`
- `test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, `test_detect_sections` in `tests/unit/test_resume_parser.py`

### Plan

- Extend the regex patterns in `resume_parser.py` to escape leading whitespaces
- Add more tests in `test_resume_parser.py` to validate fix

### Inputs & outputs

The fix extends the regex patterns to escape leading whitespaces
Pseudocode: `rf"\n{re.escape(section)}\s*[{leading whitespace}]"`

### Risks & unknowns

Still unsure about how the `re` library handles `spaces vs tabs` and if it will have an effect on the parser.

### Edge cases

If the user uploads a `blank` document, it should produce an `error/warning` instead of trying to parse `empty` sections.