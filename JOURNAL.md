## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The resume parser currently misses section headers when extracted text contains leading spaces before headings like Education or Skills. This matters because PDF text extraction often preserves indentation, so valid resumes can produce an empty `detected_sections` list even though the sections are present. The affected code is in `ingestion/parsers/resume_parser.py`, specifically the `_detect_sections()` logic. A successful fix should allow section headers to be detected whether or not they are indented, while keeping the existing resume parser behavior intact.

**Selection notes:**
This issue is a good fit because it is Tier 1, has a focused scope, and affects one parser module with existing unit tests. The expected behavior is clear from the issue reproduction: indented section headers should be detected the same way as unindented headers. The fix can be verified with a targeted regression test in `tests/unit/test_resume_parser.py`.

**Branch name:** fix/147-resume-section-leading-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/PrishaTHE-PRO/pathreview/commit/9b883cef99bd1eae6b8cb9be8eb4fefa67472df9

**Reproduction summary:**
I reproduced issue 147 with a focused resume parser regression test using indented `Education:` and `Skills:` headings. The affected behavior lives in `ResumeParser._detect_sections()`, where section headings need to be detected even when PDF or Markdown extraction preserves leading whitespace.

**PLAN.md link:** https://github.com/PrishaTHE-PRO/pathreview/blob/fix/147-resume-section-leading-whitespace/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
None right now. The main follow-up risk is ensuring the section detection regex stays anchored to heading-like lines so it does not over-detect normal body text.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the issue 147 parser fix and added a focused regression test for indented resume section headings. The planned parser and test sub-tasks from `PLAN.md` are complete.

**Next steps:**
Open the pull request, request peer or mentor feedback, and confirm the final validation status before marking the PR ready for review.

**Blockers:**
Repo-wide `make check` and `make test-unit` currently fail in unrelated modules, so the PR description should document those pre-existing failures and note that the focused resume parser tests pass.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/812

**Branch:** `fix/147-resume-section-leading-whitespace`

**What you built:**
Updated resume section detection so headings with leading whitespace, such as indented `Education:` and `Skills:` lines from PDF extraction, are detected the same way as non-indented headings. The regex remains anchored to line starts so normal body sentences are not treated as section headers.

**Tests added or updated:**
Updated `tests/unit/test_resume_parser.py` with `test_detect_sections_with_leading_whitespace`, which covers indented `Education:` and `Skills:` headings.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback has come in on PR #812 yet. I checked the PR conversation and inline review threads, and there were no comments to respond to.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The hardest part was keeping the fix small while still being confident it handled the real problem. The code change for issue 147 was only a regex adjustment, but it was easy to make the pattern too broad and accidentally detect words like "skills" inside normal resume body text. I had to think carefully about anchoring the match to heading-like lines and only adding optional leading whitespace where PDF extraction would realistically introduce it.

**What did you learn about working in a large codebase?**
I learned that even a small bug fix needs to fit the codebase's existing behavior and tests. In my own projects, I might rewrite a parser more freely, but here the better contribution was to preserve the existing `ResumeParser._detect_sections()` structure and add a focused regression test. I also learned to separate my change from unrelated repo-wide test failures so reviewers can see what my PR actually validates.

**How did AI tools help — and where did they fall short?**
AI tools helped most with navigating the repository, identifying the affected parser and test file, and turning the issue description into a concrete reproduction plan. They were also useful for checking whether the test covered the exact leading-whitespace case. Where AI fell short was judgment: I still had to verify the regex behavior myself, decide what not to change, and make sure the PR notes were honest about the broader test suite failures.

**What would you do differently if you started over?**
I would check the full test suite status earlier, before implementing the fix, so I could document pre-existing failures sooner instead of discovering them near PR submission. I would also write the reproduction test first and keep it as a separate checkpoint, because that made the issue much clearer than only reading the parser code.

**What are you most proud of from this module?**
I am most proud that the final PR is narrow and reviewable. It fixes a realistic parsing edge case, includes a regression test for the exact bug, and avoids changing unrelated parser behavior just to make the solution look larger.
