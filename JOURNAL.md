# PathReview Journal — Simon Iradukunda

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `ResumeParser` class in `ingestion/parsers/resume_parser.py` fails to detect sections when the text has leading whitespace. This is because the regular expressions in `_detect_sections()` are anchored to the start of the line or string (`^Experience`, `\nExperience`) without allowing for preceding space characters. In many parsed PDF documents, the extracted text maintains margins or lists with leading tabs/spaces, causing the section detection to miss important sections like Education or Skills. A successful fix will modify the regular expressions to allow optional whitespace after a newline or string start, ensuring sections are correctly identified.

**Branch name:** fix/147-resume-section-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes / 'Is this right for me?' reasoning:**
1. **Localizability**: The bug is isolated entirely to the regex pattern matching in `ingestion/parsers/resume_parser.py`. It doesn't require modifying database models, APIs, or the React frontend.
2. **Reproduction**: The repository includes failing unit tests (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, `test_detect_sections`) which fail consistently and provide a clear, local feedback loop.
3. **No External Dependencies**: The bug can be fixed and verified completely offline without needing active GitHub tokens or LLM APIs.
4. **Scope Fit**: As a Tier 1 issue, it represents a well-defined task (updating regular expressions and markdown cleanup logic) that matches the scope of a starter contribution.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Simon2680/pathreview/commit/24e5bab59fbd76dcd22ba67adbdf67fcc393f952

**Reproduction summary:**
I reproduced the issue locally by running pytest on `tests/unit/test_resume_parser.py` and creating a reproduction test `test_reproduce_issue_147_leading_whitespace` with space and tab indented section headers. I observed that `ResumeParser._detect_sections()` returned an empty list `[]` because its regex patterns (`^Header`, `\nHeader`) fail to match lines with leading whitespace.

**PLAN.md link:** https://github.com/Simon2680/pathreview/blob/fix/147-resume-section-whitespace/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
None. The root cause in `ingestion/parsers/resume_parser.py` is fully understood and verified through failing test assertions.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented section header detection and markdown header stripping fixes in `ResumeParser` (`ingestion/parsers/resume_parser.py`) to support optional leading horizontal whitespace (spaces and tabs). Verified reproduction test passes and added unit tests in `tests/unit/test_resume_parser.py`.

**Next steps:**
Run linter, formatter, type checker, push the updated branch to GitHub, open the pull request against `ascherj/pathreview`, and complete Check-in 2.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/892

**Branch:** `fix/147-resume-section-whitespace`

**What you built:**
Fixed resume section header detection in `ResumeParser._detect_sections()` by updating regular expressions to match headers preceded by leading spaces and tabs (`[ \t]*`). Also updated `ResumeParser._strip_markdown()` to strip markdown headers (`#`) when preceded by leading whitespace.

**Tests added or updated:**
Updated `tests/unit/test_resume_parser.py` by resolving `test_reproduce_issue_147_leading_whitespace` and added `test_detect_multi_word_sections_with_whitespace` and `test_strip_markdown_indented_headers` covering multi-word headers, tabs, and indented markdown titles.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was received this week (Summer 2026 cohort note: maintainer feedback is not active for Su26).

**How you responded:**
N/A — no feedback received.

---

### Reflection

**What was harder than you expected?**
Understanding how subtle edge cases in string parsing and regex line anchors (`^` vs. `\n`) interact across different text extraction formats (e.g., PDFs parsed into plaintext with margin indentation or tabbed lists) was trickier than expected. At first glance, modifying a regex to support whitespace seemed trivial, but avoiding false positives on inline body text or multi-word section headers while maintaining clean string splitting required careful testing of regex boundaries and markdown stripping logic in `_strip_markdown()`.

**What did you learn about working in a large codebase?**
Contributing to a shared production codebase requires a much higher standard of isolation, regression testing, and strict adherence to repository developer tools (`make check`, ruff, mypy, pytest) compared to personal projects. In a solo project, you can easily alter function signatures or assumptions; in a shared codebase, you must respect established internal abstractions (like `ResumeParser`) to ensure your fix resolves the bug cleanly without breaking upstream ingestion pipelines or downstream consumers.

**How did AI tools help — and where did they fall short?**
AI tools were exceptionally useful for rapidly brainstorming regex edge cases, refining unit test assertions for varied whitespace combinations, and formatting clear documentation. However, AI fell short when navigating local environment nuances—such as recognizing which unit tests depended on offline parser logic versus external LLM APIs—and verifying that regex boundary changes wouldn't introduce subtle false positives elsewhere in section extraction.

**What would you do differently if you started over?**
If starting over, I would build an even more comprehensive suite of failing reproduction tests representing edge-case document layouts (e.g., mixed spaces/tabs, multi-line headings, non-standard section headers) before touching any implementation code. Having that exhaustive test harness up front would have made validating the regex refinements in `_detect_sections()` and `_strip_markdown()` even smoother.

**What are you most proud of from this module?**
I am most proud of delivering a clean, surgical fix that completely resolved Issue #147 without introducing code bloat or side effects, while expanding unit test coverage to protect against regression and maintaining full compliance with the repository's automated quality checks (`make check`).


