## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/147]

**Issue title:** [Resume section detection fails on text with leading whitespace
 #147]

**Tier:** [ x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[This issue affects the section-detection logic in `ingestion/parsers/resume_parser.py`, specifically the `_detect_sections()` method. The current regular expressions assume that headings such as “Education,” “Experience,” and “Skills” begin at the first character of a line. However, text extracted from PDFs often contains leading spaces or tabs, causing valid headings to be ignored and `detected_sections` to remain empty. A successful fix would update the matching logic to accept optional leading horizontal whitespace while preserving accurate section detection and avoiding new false positives.]

**Branch name:** [fix/147-Resume-section-detection-leading-whitespace]

**Setup confirmation:** [x ] App runs locally at localhost:5173

**Cohort ledger:** [x ] Issue added to cohort ledger

**issue reproduction:**
## Issue #147: Resume section detection with leading whitespace

### Issue summary

This issue affects the `_detect_sections()` logic in
`ingestion/parsers/resume_parser.py`. The parser expects resume section
headings such as `Education` and `Skills` to begin at the first character of
a line. Text extracted from PDFs commonly preserves indentation, so headings
with leading spaces are not detected and `detected_sections` may be returned
as an empty list.

### Reproduction steps

I reproduced the issue using the following resume text:

```python
from ingestion.parsers.resume_parser import ResumeParser

resume_text = """
    John Smith
    john@example.com

    Education:
    - B.S. Computer Science

    Skills: Python
"""

parser = ResumeParser()
result = parser.parse(resume_text)

print(result.metadata["detected_sections"])

Observed result : []

The parser returned no detected sections even though the input contained
Education: and Skills: headings.

Expected result

The parser should recognize the Education and Skills sections despite the
spaces before each heading.

Related tests

I also ran:

pytest tests/unit/test_resume_parser.py \
  -k "test_parse_single_column_resume_text or test_parse_resume_no_work_experience or test_detect_sections" \
  -vv

**Test result:**
_ TestResumeParser.test_detect_sections ___________________________________________

self = <tests.unit.test_resume_parser.TestResumeParser object at 0x1044c6030>
parser = <ingestion.parsers.resume_parser.ResumeParser object at 0x1044cf390>

    def test_detect_sections(self, parser):
        """Test section detection in resume text."""
        text = """
        Experience:
        Senior Developer at TechCorp
    
        Education:
        BS Computer Science
    
        Skills: Python, JavaScript
        """
        sections = parser._detect_sections(text)
    
        assert isinstance(sections, list)
>       assert len(sections) > 0
E       assert 0 > 0
E        +  where 0 = len([])

tests/unit/test_resume_parser.py:140: AssertionError
================================================== short test summary info ==================================================
FAILED tests/unit/test_resume_parser.py::TestResumeParser::test_parse_single_column_resume_text - assert (False or False)
 +  where False = any(<generator object TestResumeParser.test_parse_single_column_resume_text.<locals>.<genexpr> at 0x103eccc70>)
 +  and   False = any(<generator object TestResumeParser.test_parse_single_column_resume_text.<locals>.<genexpr> at 0x103ecd560>)
FAILED tests/unit/test_resume_parser.py::TestResumeParser::test_parse_resume_no_work_experience - assert False
 +  where False = any(<generator object TestResumeParser.test_parse_resume_no_work_experience.<locals>.<genexpr> at 0x103ece400>)
FAILED tests/unit/test_resume_parser.py::TestResumeParser::test_detect_sections - assert 0 > 0
 +  where 0 = len([])
============================================== 3 failed, 7 deselected in 0.52s ==============================================

**Conclusion**

The issue is reproducible. Leading whitespace before resume section headings
prevents the current regular-expression matching logic from identifying valid
sections.
