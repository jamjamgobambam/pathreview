## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The resume parser currently fails to detect common resume section headers when extracted text includes leading spaces or tabs before the header. This matters because PDF text extraction often preserves indentation, so headers like `Education:` or `Skills:` may appear with whitespace before them and then `detected_sections` comes back empty or incomplete. The affected code is in `ingestion/parsers/resume_parser.py`, specifically the `_detect_sections` regex logic. A successful fix will let the parser detect indented section headers while keeping section detection strict enough to avoid matching ordinary sentences.

**"Is this right for me?" checklist reasoning:**
I chose this issue because it is a focused Tier 1 bug with a clear reproduction and a small implementation surface. I found the relevant parser code in `ingestion/parsers/resume_parser.py` and the existing unit tests in `tests/unit/test_resume_parser.py`. The fix should only require adding a regression test for leading whitespace and updating the section-header regex to allow spaces or tabs at the start of a line. The main risk is making the regex too broad, so the plan is to keep matches anchored to line starts and only allow optional leading whitespace before known section names.

**Branch name:** fix/147-resume-section-leading-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 - Reproduction & solution planning

**Reproduction commit link:** https://github.com/yaritzay27/pathreview/commit/0fd27b9

**Reproduction summary:**
I reproduced the issue by running `ResumeParser` on resume text where `Education:` had leading spaces and `Skills:` had a leading tab. The parser returned an empty `detected_sections` list, confirming that the current `_detect_sections` logic misses valid indented section headers. I also reproduced the issue locally with .venv/bin/python by parsing resume text containing indented Education and tab-indented Skills headers. The parser returned [], showing that valid section headers with leading whitespace are not detected.

**PLAN.md link:** https://github.com/yaritzay27/pathreview/blob/fix/147-resume-section-leading-whitespace/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
The main open question is how narrow to keep the regex so it detects indented headers without matching ordinary sentences that mention words like education, skills, or experience. The planned approach is to keep the regex anchored to the start of each line and only allow optional leading whitespace before known section names.



<!--
PAUSED DUE TO MISSING FILES

Old Issue #105 Week 7 notes, preserved for reference.

## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/105

**Issue title:** Add accessibility tests for the review page using jest-axe

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The review page currently does not have automated accessibility coverage, so regressions like invalid ARIA attributes, missing labels, or heading problems could be introduced without being caught by the frontend test suite. This issue asks for tests around `ReviewPage` using `jest-axe`, while following the project's existing Vitest and React Testing Library patterns. The relevant code is in the frontend, especially `frontend/src/pages/ReviewPage.tsx`, `frontend/src/test/setup.ts`, and possibly `frontend/src/components/ReviewSection.tsx` if the accessibility test exposes a real issue. A successful fix will add focused accessibility tests and only change production code if the tests reveal a genuine accessibility violation.

**"Is this right for me?" checklist reasoning:**
I chose this issue because the scope is realistic and mostly limited to the frontend test setup and a new ReviewPage test file. The repository already uses Vitest, React Testing Library, jsdom, and has `jest-axe` listed in the frontend dev dependencies, so the required testing infrastructure is mostly present. I inspected the ReviewPage and related components and found that ReviewPage depends on router params, `useReviewStatus`, and `apiClient.getReview`, which can be mocked in tests. The main risk is that axe may expose an accessibility issue in `ReviewSection`, but the plan is to keep production changes minimal and only fix that component if the test shows a real violation.

**Branch name:** test/105-review-page-accessibility-tests

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
-->
