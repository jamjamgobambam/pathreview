## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The `_detect_sections()` method in `ingestion/parsers/resume_parser.py` uses regex patterns that require section headers (like "Education" or "Experience") to begin at the very start of a line (`^Experience`) or immediately after a newline (`\nExperience`). Text extracted from PDFs commonly preserves leading indentation — spaces or tabs before content — which means none of those patterns ever match, and `detected_sections` always comes back empty. As a result, the ingestion pipeline has no structural information about the resume even when well-known sections like Education or Skills are clearly present. A successful fix would update the four patterns inside `_detect_sections()` to tolerate optional leading whitespace (e.g., `^\s*Experience`) so that section detection works regardless of indentation level.

**Selection notes ("Is this right for me?" reasoning):**
I chose Tier 1 because this is my first time contributing to a large multi-module codebase. The fix is tightly scoped: it touches exactly one method (`_detect_sections`) in one file (`ingestion/parsers/resume_parser.py`), and the issue body already identifies the root cause (regex anchoring) and the three failing tests to use for verification. There are no external API calls, no schema changes, and no frontend involvement — I can reproduce the bug in a Python shell in under a minute, confirm my fix with the existing tests, and move on. That tight feedback loop made this a confident Tier 1 pick.

**Branch name:** fix/147-resume-section-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/UFmainuddin/pathreview/commit/de11633

**Reproduction summary:**
Ran `pytest tests/unit/test_resume_parser.py -v` locally and confirmed 5 tests fail. The key failure is `test_detect_sections`, which passes indented text (e.g., `"    Experience:"`) and asserts `len(sections) > 0` — the actual result is `[]` because all four regex patterns in `_detect_sections()` require the section keyword at column 0 (`^section`) or immediately after a newline (`\nsection`), with no allowance for leading whitespace. A related bug in `_strip_markdown()` — its `^#+\s+` pattern also fails to strip `#` headers with leading whitespace — was discovered during reproduction and causes two additional test failures.

**PLAN.md link:** https://github.com/UFmainuddin/pathreview/blob/fix/147-resume-section-whitespace/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
The `_strip_markdown()` bug was not mentioned in issue #147 but was discovered during reproduction (it causes `test_strip_markdown_syntax` and `test_parse_markdown_resume` to fail). The fix is one character in the same file. I plan to include it in the same PR and call it out in the PR description — but want to confirm this is acceptable scope for a Tier 1 issue before Week 9.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All sub-tasks from PLAN.md are complete. Applied both fixes to `ingestion/parsers/resume_parser.py`:
- Sub-task 1: Updated all 4 regex patterns in `_detect_sections()` — `^` → `^\s*` and `\n` → `\n\s*` — so indented PDF-extracted headers are matched.
- Sub-task 2: Updated the header-removal pattern in `_strip_markdown()` — `^#+\s+` → `^\s*#+\s+` — so markdown headers with leading whitespace are stripped.
- Sub-task 3: All 10 tests in `tests/unit/test_resume_parser.py` pass (was 5 failing before the fix).
- Sub-task 4: Full `make test-unit` run confirms no regressions introduced by our change (48 pre-existing failures across unrelated test files remain unchanged).
- Sub-task 5: `ruff check ingestion/parsers/resume_parser.py` — all checks passed.

**Next steps:**
Open PR to upstream `ascherj/pathreview`, fill out PR template completely, update JOURNAL.md Check-in 2 with PR link, submit branch URL via course portal.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/800

**Branch:** `fix/147-resume-section-whitespace`

**What you built:**
Fixed `_detect_sections()` in `ingestion/parsers/resume_parser.py` by adding `\s*` after the `^` and `\n` anchors in all four regex patterns, so section headers with leading whitespace (common in pypdf-extracted text) are correctly detected instead of always returning an empty list. Also fixed a related bug in `_strip_markdown()` where markdown `#` headers with leading whitespace were not being stripped — changed `^#+\s+` to `^\s*#+\s+`.

**Tests added or updated:**
No new test files — the 5 pre-existing failing tests in `tests/unit/test_resume_parser.py` (`test_detect_sections`, `test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, `test_parse_markdown_resume`, `test_strip_markdown_syntax`) now all pass. All 10 tests in the file pass. The full unit suite (`make test-unit`) shows the same 48 pre-existing failures in unrelated files; our change introduced zero new failures.

**Self-review confirmation:** [x] make check passes (our file: `ruff check ingestion/parsers/resume_parser.py` — all checks passed; 48 pre-existing failures in unrelated files unchanged) [x] make test-unit passes (10/10 resume parser tests pass; no new failures introduced)

**Draft PR feedback received from:** none

---

## Week 10 - Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No - still awaiting review

**Summary of feedback:**
No reviewer feedback has arrived yet. For Summer 2026, reviewer feedback is not provided, so I am marking that I am still awaiting review.

**How you responded:**
No response was needed because no reviewer feedback came in. I still checked my PR and made sure my Week 10 journal is updated.

---

### Reflection

**What was harder than you expected?**
The harder part was understanding how a small regex change could affect the resume parser. At first, the issue looked very simple, but I had to read `ingestion/parsers/resume_parser.py` carefully to understand why leading spaces from PDF text made `_detect_sections()` fail.

**What did you learn about working in a large codebase?**
I learned that even a small change needs careful testing in a large codebase. I could not only change the regex and stop; I had to run `tests/unit/test_resume_parser.py` and also check the larger unit test result to make sure my fix did not create new problems.

**How did AI tools help - and where did they fall short?**
AI tools helped me understand the failing tests and explain the regex problem in simpler words. They were also useful for planning the fix for issue `#147`. But AI did not replace checking the real code and test output, because I still had to confirm that `_detect_sections()` and `_strip_markdown()` were the correct places to change.

**What would you do differently if you started over?**
If I started over, I would inspect the related helper functions earlier instead of only focusing on the exact issue description. The issue talked about section detection, but the markdown stripping problem was also related and caused more failing tests, so I would look for nearby similar patterns sooner.

**What are you most proud of from this module?**
I am most proud that I made a small but real fix and opened PR `#800` to the upstream PathReview project. The change was not large, but it made the parser handle indented resume sections better and all 10 resume parser tests passed after the fix.
