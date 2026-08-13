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

**Draft PR feedback received from:** [none yet — PR was moved from draft to ready for review from my own account after peer/mentor feedback was requested in Slack and no one reviewed it]

## Week 10 — Iteration & Reflection

**Reviewer feedback received:** [ ] Yes  [x] No

**Feedback summary / response:**
[No review arrived on PR #401 (https://github.com/ascherj/pathreview/pull/401) before the course ended. I checked the PR directly today (Aug 13): it's open, not draft, mergeable, with zero reviews and zero comments — same state it's been in since I marked it ready for review in Week 9. I'd requested peer/mentor review in Slack but no one picked it up in the window available. Nothing to respond to, so I'm noting it and moving on, per the Week 10 instructions.]

### Reflection

**1. What was harder than you expected?**
[Telling the difference between "my bug" and "a bug that happens to be sitting next to my bug" was harder than I expected. While fixing `_detect_sections()`, I found that `test_parse_markdown_resume` and `test_strip_markdown_syntax` were failing for a related reason — the same category of anchoring issue, but in `_strip_markdown()`'s header regex, not in the function my issue was actually about. It was tempting to just fix it since I was already in the file, but issue #147 was scoped to section detection, so I documented it in the PR description instead. I also didn't expect to have to reverse-engineer the Makefile: `make check`'s format step runs bare `black .` with no `--check`, which would have reformatted the entire repo instead of just the two files I touched, so I had to run `ruff`, `black --check`, and `mypy` individually, scoped to my files, instead of trusting the documented command.]

**2. What did you learn about working in a large codebase?**
[A clean-looking local fix isn't enough evidence on its own — I had to run the full `tests/unit` suite before and after my change (53 failed/375 passed → 50 failed/383 passed) to actually show the fix worked and introduced zero regressions, rather than just pointing at the 3 tests I already knew about. I also learned to respect the boundary of a single-issue PR: this repo has 130 open issues across tier-1/2/3, and it would be easy to let a fix sprawl into "also fixed while I was here." Scoping the change to exactly `_detect_sections()` in `ingestion/parsers/resume_parser.py`, and writing the adjacent `_strip_markdown()` bug down instead of touching it, felt like the actual skill being tested — not the regex itself.]

**3. How did AI tools help — and where did they fall short?**
[AI tools were most useful for stress-testing the regex change before I wrote it — walking through why `[ \t]*` (not `\s*`) was the right anchor, since `\s*` matches newlines and could let the pattern skip a blank line and falsely anchor to a header several lines down. That reasoning is what shaped the "Risks & unknowns" and "Edge cases" sections in my PLAN.md, and it's why I added the false-positive test (`test_detect_sections_ignores_indented_body_text`) before touching the implementation. Where it fell short: it couldn't tell me how `pypdf`'s `extract_text()` actually represents indentation across different real-world PDF producers — that's an empirical question about a specific library's behavior, not something reasoning alone resolves — so I left it flagged as an open unknown in PLAN.md rather than assuming my test coverage was complete.]

**4. What would you do differently if you started over?**
[I'd open the draft PR by Check-in 1 instead of waiting until right before Check-in 2. Doing it that way meant there was almost no real calendar time left for anyone to actually review it before I had to move it to ready-for-review myself — the review cycle never really got a chance to happen. I'd also check upfront whether a repo's documented `make check` command is safe to run as-is (vs. reformatting unrelated files) before relying on it, instead of discovering the `black .` issue mid-task.]

**5. What are you most proud of?**
[Holding the fix to exactly what issue #147 asked for, even after finding a second, related bug I could have folded in. Documenting it instead of fixing the second bug, and backing the PR description with real before/after numbers (53/375 → 50/383) instead of just asserting "tests pass," is the kind of evidence-over-assertion habit I want interviewers to see when they ask about this project.]

