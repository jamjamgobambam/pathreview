# Module 3 Journal — Shiven Saxena

## Week 7 — Issue Selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `_detect_sections()` method in `ingestion/parsers/resume_parser.py` builds regex patterns that look for section headers anchored immediately after a newline or at the start of a line — for example, `\nEducation:` or `^Skills`. Text extracted from PDFs frequently preserves the original indentation, so a line like `    Education:` (four leading spaces) never matches any of those patterns, and `detected_sections` comes back empty even when the section is clearly present. This means downstream components that rely on section metadata — such as chunking and relevance scoring — receive no structural signal from PDF-sourced resumes. A successful fix would update the patterns (or strip leading whitespace per line before matching) so that `Education`, `Skills`, and other headers are detected regardless of how much indentation precedes them.

**Selection notes (scope fit):**
Worked through the "Is this right for me?" checklist: the change is isolated to one private method (~20 lines) in a single file, the expected behavior is clearly defined by three failing unit tests in `tests/unit/test_resume_parser.py`, no external services or database are involved, and the fix requires only regex knowledge. Tier 1 / good first issue aligns with my comfort level entering this codebase.

**Branch name:** fix/147-resume-section-detection-leading-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/shivensaxena28/pathreview/commit/24b8e21

**Reproduction summary:**
Ran `pytest tests/unit/test_resume_parser.py` locally with indented resume text (spaces before section headers); `test_detect_sections` and `test_parse_resume_no_work_experience` both failed with `assert 0 > 0` — `_detect_sections()` returned an empty list because none of the four regex patterns allow whitespace between the line-start anchor and the header word.

**PLAN.md link:** https://github.com/shivensaxena28/pathreview/blob/fix/147-resume-section-detection-leading-whitespace/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
Need to verify that adding `\s*` before the header word in each pattern does not cause false positives on lines that happen to contain a section keyword mid-sentence (e.g. "She has experience with…").

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed all four sub-tasks from PLAN.md. Identified the exact failure: the four pattern strings in `_detect_sections()` (lines 134–139 of `ingestion/parsers/resume_parser.py`) anchor section headers at `^` or `\n` with no allowance for leading whitespace, so indented PDF-extracted text like `    Education:` is never matched. Applied the fix — adding `\s*` before each header word — and verified the three originally failing tests (`test_detect_sections`, `test_parse_resume_no_work_experience`, `test_parse_single_column_resume_text`) now pass. Also confirmed the two unrelated pre-existing failures (`test_strip_markdown_syntax`, `test_parse_markdown_resume`) were already failing on the unmodified codebase and are not affected by this change.

**Next steps:**
Open the PR against `ascherj/pathreview`, fill in the PR template, and finalize JOURNAL.md Check-in 2 with the PR link.

**Blockers:**
None — the `make check` equivalents (ruff, black) flagged two pre-existing issues in unrelated lines (import sort at line 1, `raise...from` at line 78); my change introduces no new linting findings.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/332

**Branch:** `fix/147-resume-section-detection-leading-whitespace`

**What you built:**
Added `\s*` before each header keyword in the four regex patterns inside `_detect_sections()` in `ingestion/parsers/resume_parser.py`, so section headers preceded by any amount of leading whitespace (spaces or tabs, as commonly preserved by PDF text extraction) are now detected correctly. The method signature, return type, and all callers are unchanged.

**Tests added or updated:**
No new test files were needed — `tests/unit/test_resume_parser.py` already contained the three failing tests that define the correct behavior (`test_detect_sections`, `test_parse_resume_no_work_experience`, `test_parse_single_column_resume_text`). All three now pass; the two pre-existing unrelated failures (`test_strip_markdown_syntax`, `test_parse_markdown_resume`) are documented in the PR description and unchanged.

**Self-review confirmation:** [x] make check passes (no new findings)  [x] make test-unit passes (3 target tests green, 2 pre-existing unrelated failures documented)

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer comments came in by the end of the week. Per the Su26 course note, reviewer feedback is not a feature in Summer 2026.

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Establishing a clean baseline before touching any code. When I first ran the full unit suite, 16 test files failed to collect due to missing dependencies, and two tests in `test_resume_parser.py` were already failing for a completely unrelated bug in `_strip_markdown()`. Untangling which failures were pre-existing versus caused by my change took more effort than I anticipated — I had to `git stash` my fix and re-run the suite just to get a trustworthy before/after comparison. I expected the hard part to be writing the fix; it turned out to be proving the fix didn't break anything else.

**What did you learn about working in a large codebase?**
The fix itself was four characters added in four lines. Everything around it — reading the call chain from `_parse_pdf` down to `_detect_sections`, understanding why `re.MULTILINE` meant `^` should work, checking whether `\s*` could cause false positives on mid-sentence keywords, verifying that two existing test failures predated my change — took significantly longer. In my own projects I jump straight to writing; here I learned that reading and verifying are the real work. Contributing to someone else's production codebase means your change has to make sense in context, not just pass the tests you ran.

**How did AI tools help — and where did they fall short?**
AI was most useful for navigating the codebase quickly — tracing the call chain, understanding what `re.MULTILINE` does with `^`, and drafting the PR description with the right level of detail. Where it fell short was in judgment calls that required running the actual environment: figuring out which of the 16 collection errors were real blockers versus missing dev dependencies, and deciding whether the two `_strip_markdown` failures were mine or pre-existing. Those required actually running commands and reading real output. AI gave me the map; I still had to walk the terrain.

**What would you do differently if you started over?**
Run `make test-unit` on the unmodified codebase before writing a single line — before even reading the issue description in depth. A clean baseline snapshot of exactly which tests fail and which pass takes two minutes and saves a lot of confusion later. I also would have scoped my PLAN.md edge cases more tightly to the regex change itself; a couple of them (like "section keyword inside an email address") were theoretically interesting but not worth investigating for a four-line patch.

**What are you most proud of from this module?**
The PR description. It's easy to submit a fix and let the diff speak for itself, but taking the time to explain the pre-existing failures, document the manual reproduction steps, and note exactly which lines changed — and why `\s*` belongs before the keyword rather than after the anchor — is the kind of context that makes a maintainer's review fast and confident. That felt like the difference between dropping code over a wall and actually contributing.
