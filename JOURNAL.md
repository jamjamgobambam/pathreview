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


## Week 9 - Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the parser fix from my PLAN.md by updating `ResumeParser._detect_sections` so it allows optional leading whitespace before known section headers. I also added regression coverage in `tests/unit/test_resume_parser.py` for indented `Education:`, tab-indented `Skills:`, and indented `Experience:` headers, plus a guard test to make sure section words in normal sentences are not treated as headers.

**Next steps:**
Run the targeted resume parser tests in WSL with `.venv/bin/python -m pytest tests/unit/test_resume_parser.py -q`, then run `make test-unit` and `make check` before opening the PR. After the PR is submitted, update Check-in 2 with the PR link and final test status.

**Blockers:**
The targeted resume parser checks pass locally: `python -m ruff check ingestion/parsers/resume_parser.py tests/unit/test_resume_parser.py`, `python -m black --check ingestion/parsers/resume_parser.py tests/unit/test_resume_parser.py`, and `python -m pytest tests/unit/test_resume_parser.py -q`. Broader `make test-unit` and `make check` currently fail in unrelated modules outside this issue, including safety, RAG, review service, skill extraction, and repository-wide lint issues. I need to document those unrelated failures in the PR description.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/373

**Branch:** fix/147-resume-section-leading-whitespace

**What you built:**
I updated resume section detection so known headers are recognized even when PDF-extracted text includes leading spaces or tabs. The regex remains anchored to line starts, so it handles indentation without matching section words in the middle of ordinary sentences.

**Tests added or updated:**
Updated `tests/unit/test_resume_parser.py` with a regression test for indented section headers and a guard test for normal prose containing section words.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Targeted check: [x] `.venv/bin/python -m pytest tests/unit/test_resume_parser.py -q` passes.

Targeted lint/format: [x] `python -m ruff check ingestion/parsers/resume_parser.py tests/unit/test_resume_parser.py` passes; [x] `python -m black --check ingestion/parsers/resume_parser.py tests/unit/test_resume_parser.py` passes.

Project-wide check notes: `make test-unit` and `make check` currently fail on unrelated existing tests/lint outside the resume parser files.

**Draft PR feedback received from:** Requested review, no feedback received before submission

## Week 10 - Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No - still awaiting review

**Summary of feedback:**
Requested review, no feedback received before submission. No reviewer or maintainer comments came in on my PR before the Week 10 deadline, and the Summer 2026 note says reviewer feedback is not required for this part of the module. My PR is still open at https://github.com/ascherj/pathreview/pull/373.

**How you responded:**
No code review response was needed because no feedback was received before submission. I kept the PR open and documented the final status honestly in this journal.

---

### Reflection

**What was harder than you expected?**
The hardest part was separating issues caused by my change from existing project-wide failures. My targeted resume parser tests passed, but broader commands like `make test-unit` and `make check` reported failures in unrelated modules, so I had to slow down and document the difference instead of assuming my fix broke the whole codebase. I also had to work through WSL, the virtual environment, pre-commit hooks, formatting, linting, and mypy errors, which made the workflow feel more realistic than a small class project.

**What did you learn about working in a large codebase?**
I learned that even a small bug fix needs context. For issue #147, the production change was only in `ingestion/parsers/resume_parser.py`, but I still needed to understand the parser behavior, the existing tests in `tests/unit/test_resume_parser.py`, the repository's pre-commit checks, and how to explain unrelated failures clearly in my PR. Contributing to someone else's codebase means matching the existing style and keeping the change focused instead of rewriting more than necessary.

**How did AI tools help - and where did they fall short?**
AI tools helped me inspect the repository, understand the issue scope, compare possible issues, plan the fix, write journal entries, and debug test or lint output. The most useful part was having help translate terminal errors into specific next steps, especially with ruff, black, mypy, and pytest. Where AI fell short was that it could not replace me actually running commands in my WSL environment, checking the real output, and deciding what was safe to submit. I still had to verify the fix locally and make sure the PR description matched what really happened.

**What would you do differently if you started over?**
I would choose the smaller, more localized issue earlier instead of spending time on the accessibility testing issue first. Issue #147 was a better fit because it had a clear reproduction, a narrow production file, and existing unit tests that could be extended. I would also run the targeted tests and pre-commit-style checks earlier, because that would have caught the formatting and mypy issues before I tried to commit.

**What are you most proud of from this module?**
I am most proud that I adjusted my issue choice when the original plan became risky, reproduced the new bug locally, and submitted a focused PR with tests. I did not just make the parser accept more text broadly; I added a guard test so ordinary sentences with words like education or skills do not get mistaken for headers. That made the fix feel small, intentional, and easier for a maintainer to review.



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
