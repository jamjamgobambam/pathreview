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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/pgazar/pathreview/commit/9ec209ca9828d9725b9acdaaa4cd4788ad8b7dfa]

**Reproduction summary:**
[Run ResumeParser.parse() on resume text where section headings such as Education: and Skills: have leading spaces or tabs. Confirm that result.metadata["detected_sections"] returns an empty list even though those valid section headings are present.]

**PLAN.md link:** [https://github.com/pgazar/pathreview/blob/fix/147-Resume-section-detection-leading-whitespace/PLAN.md]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[All 5 sub-tasks from PLAN.md are done. Updated the four regex patterns in `_detect_sections()` (`ingestion/parsers/resume_parser.py`) to allow optional leading horizontal whitespace via `[ \t]*` instead of anchoring directly on `^`/`\n`, and dropped the now-redundant `\n`-prefixed pattern variants since `re.MULTILINE` already makes `^` match after every newline. Re-ran the 3 originally-failing tests and confirmed they now pass. Added 5 new regression tests covering tab indentation, mixed space/tab indentation, leading+trailing whitespace, a false-positive guard (indented body text mentioning a section keyword), and the empty-input edge case. Ran the full `tests/unit` suite before and after: 53 failed/375 passed before, 50 failed/383 passed after -- confirms the fix, the 5 new tests, and zero regressions elsewhere. Also fixed one unrelated pre-existing ruff `B904` finding in the same function since pre-commit blocked committing the file otherwise. Opened a draft PR against upstream: https://github.com/ascherj/pathreview/pull/401]

**Next steps:**
[Get peer/mentor feedback on the draft PR in Slack. Address any feedback, then mark the PR ready for review and complete Check-in 2 by Sunday.]

**Blockers:**
[None currently. Two pre-existing, unrelated test failures in test_resume_parser.py (test_parse_markdown_resume, test_strip_markdown_syntax) are caused by the same category of bug in `_strip_markdown()`'s markdown-header regex, but that's out of scope for issue #147 (which is specifically about resume section detection) -- documented in the PR description rather than fixed here.]

---

### Check-in 2 (end of week)

**PR link:** [https://github.com/ascherj/pathreview/pull/401]

**Branch:** `fix/147-Resume-section-detection-leading-whitespace`

**What you built:**
[Fixed `_detect_sections()` in `ingestion/parsers/resume_parser.py` so resume section headings (e.g. `Education:`, `Skills:`) are recognized even when preceded by leading whitespace (spaces or tabs), which previously caused `detected_sections` to come back empty. The regex patterns now allow optional leading horizontal whitespace via `[ \t]*` (not `\s*`, so a match can't cross a blank line onto a header further down), and the redundant `\n`-prefixed pattern variants were removed since `re.MULTILINE` already covers that case.]

**Tests added or updated:**
[Added 5 new tests to `tests/unit/test_resume_parser.py`: `test_detect_sections_with_tab_indentation` and `test_detect_sections_with_mixed_whitespace_indentation` cover tab-only and mixed space/tab indentation before a header; `test_detect_sections_with_leading_and_trailing_whitespace` covers whitespace on both sides of the header (before the keyword and before the colon); `test_detect_sections_ignores_indented_body_text` guards against a false positive where an indented bullet line merely mentions a section keyword (e.g. "skills") without being an actual header; `test_detect_sections_with_no_headers_returns_empty_list` covers the no-headers edge case. Also confirmed the 3 previously-failing tests (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, `test_detect_sections`) now pass.]

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*(Scoped to files touched by this PR: `ruff check`, `black --check`, and `mypy` all pass clean on `ingestion/parsers/resume_parser.py` and `tests/unit/test_resume_parser.py`. The repo has pre-existing, unrelated failures in both `make test-unit` — 50 failing tests across ~15 other modules — and `make typecheck` — 5 errors from missing/incompatible type stubs — that predate this PR and are unaffected by it; documented in the PR description. Ran individual check-mode commands rather than literal `make check`, since its `format` step runs bare `black .` — no `--check` — which would have reformatted unrelated files repo-wide.)*

**Draft PR feedback received from:** [none yet — PR was moved from draft to ready for review from my own account before peer/mentor feedback was requested in Slack]
