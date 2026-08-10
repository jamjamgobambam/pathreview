# Reproduction: Issue #147 — Resume section detection fails on text with leading whitespace

## Commands run

### 1. Run the three failing unit tests

```bash
.venv/bin/pytest tests/unit/test_resume_parser.py -v -k "test_parse_single_column_resume_text or test_parse_resume_no_work_experience or test_detect_sections"
```

**Observed output (abridged):**

```
tests/unit/test_resume_parser.py:32: AssertionError
____________ TestResumeParser.test_parse_resume_no_work_experience _____________
>       assert any("education" in s for s in detected_lower)
E       assert False

____________________ TestResumeParser.test_detect_sections _____________________
>       assert len(sections) > 0
E       assert 0 > 0
E        +  where 0 = len([])

=========================== short test summary info ============================
FAILED tests/unit/test_resume_parser.py::TestResumeParser::test_parse_single_column_resume_text
FAILED tests/unit/test_resume_parser.py::TestResumeParser::test_parse_resume_no_work_experience
FAILED tests/unit/test_resume_parser.py::TestResumeParser::test_detect_sections
======================= 3 failed, 7 deselected in 0.22s ========================
```

All three tests named in the issue fail, each because `detected_sections` (or
`ResumeParser._detect_sections()` directly) returns an empty list even though
the input text clearly contains section headers like "Education" and "Skills".

### 2. Isolate the root cause directly

```bash
.venv/bin/python -c "
from ingestion.parsers.resume_parser import ResumeParser

text = '\n    Education:\n    - B.S. Computer Science\n    Skills: Python\n'
parser = ResumeParser()
print('Indented:', parser._detect_sections(text))

text2 = '\nEducation:\n- B.S. Computer Science\nSkills: Python\n'
print('Unindented:', parser._detect_sections(text2))
"
```

**Observed output:**

```
Indented: []
Unindented: ['Education', 'Skills']
```

## Conclusion

The same section text is detected correctly when each line starts at column 0,
but detection fails when lines carry leading whitespace (spaces/tabs from PDF
text extraction, or triple-quoted string indentation in tests). This confirms
the root cause described in the issue: `_detect_sections()` in
`ingestion/parsers/resume_parser.py` uses regex patterns anchored with `^` and
`\n` that require the section keyword to immediately follow the line start,
with no allowance for leading whitespace before it.
