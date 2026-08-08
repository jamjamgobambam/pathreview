# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Section detection in `ingestion/parsers/resume_parser.py` looks for headers like `Education` and `Skills` only when they sit at the very start of a line. PDF-extracted resumes often keep indentation, so those headers never match and `detected_sections` comes back empty even when the sections are clearly present. A successful fix should allow optional leading whitespace in the header regex patterns so indented resumes still report the right sections, and the related unit tests in `tests/unit/test_resume_parser.py` should pass.

**"Is this right for me?" checklist / selection notes:**
- Scope is small and localized to `_detect_sections()` regex patterns — good first contribution.
- Tier 1 / good-first-issue label matches my current level for Module 3.
- Clear reproduce steps and named failing tests make success criteria easy to verify.
- Touches the ingestion subsystem without requiring frontend, agent, or RAG changes.

**Branch name:** fix/147-resume-section-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/DanOhsaka/pathreview-week-7-ai201/commit/06591db977b1f934049e0ef1148ac6c33f91efe0

**Reproduction summary:**
I ran the exact indented resume sample from issue #147 through the old `_detect_sections` regexes (no `\s*` after `^`/`\n`) and got `detected_sections: []`, then compared that to the current parser which returns Education and Skills. That comparison is checked in as `scripts/reproduce_issue_147.py` plus a docstring on `_detect_sections` explaining the failure mode.

**PLAN.md link:** https://github.com/DanOhsaka/pathreview-week-7-ai201/blob/fix/147-resume-section-whitespace/PLAN.md

**Walkthrough video (recommended):** 

**Blockers or open questions:**
None for the core fix. Optional follow-up: whether multi-line PDF headers (header split across lines) need a separate issue; out of scope for #147.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed PLAN.md sub-tasks for reproduction and the core regex fix in `_detect_sections()` (`^\s*` / `\n\s*` before section names). Added `scripts/reproduce_issue_147.py` to show broken vs fixed behavior, and confirmed the issue #147 sample returns Education/Skills instead of `[]`.

**Next steps:**
Finish regression tests for edge cases (flush-left, multi-word headers, bare lines, empty input), run unit checks, open the PR against `ascherj/pathreview`, and request peer/mentor feedback in Slack.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/430

**Branch:** `fix/147-resume-section-whitespace`

**What you built:**
Section-header detection in `ingestion/parsers/resume_parser.py` now allows optional leading whitespace so PDF-indented resumes still populate `detected_sections`. Patterns still require end-of-line or `:`/`|`/`-` after the header to reduce false matches.

**Tests added or updated:**
`tests/unit/test_resume_section_whitespace.py` — covers the issue #147 sample, flush-left headers, indented multi-word headers (`Work Experience`), bare indented headers, and text with no sections.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Notes: Pre-commit ruff/black/mypy passed on commits for touched files. Targeted unit tests for this change pass (5/5). Two pre-existing failures in `test_resume_parser.py` (`test_parse_markdown_resume`, `test_strip_markdown_syntax`) are unrelated markdown-stripping bugs and were not introduced by this PR (documented in the PR description).

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No maintainer or reviewer comments on [PR #430](https://github.com/ascherj/pathreview/pull/430) by the end of Week 10. Summer 2026 does not provide formal reviewer feedback, so this is expected.

**How you responded:**


---

### Reflection

**What was harder than you expected?**
Getting a reliable local environment on Windows was harder than the bug itself. Installing `make`, learning that PowerShell can’t run this Makefile (it needs Git Bash), fixing a UTF-16-corrupted `.bashrc`, and waiting for Docker Desktop before `make setup` / `make run` took more time than editing four regexes. Pre-commit also blocked commits until I fixed a ruff `B904` issue and learned that touching the old `test_resume_parser.py` file triggered mypy on untyped tests that weren’t part of my change.

**What did you learn about working in a large codebase?**
In your own project you can change anything; here the win was staying scoped. Issue #147 lived in one function (`_detect_sections`), but I still had to read call sites (`_parse_pdf` / `_parse_markdown`), match existing pytest patterns, and document unrelated failing markdown tests so reviewers knew I didn’t introduce them. Contributing means proving the bug, naming exact files, and leaving the rest of the system alone.

**How did AI tools help — and where did they fall short?**
AI helped navigate setup (PATH, Git Bash vs PowerShell), draft `PLAN.md` / journal sections, and scaffold regression tests. It fell short when environment details were Windows-specific — e.g. PowerShell writing UTF-16 into `.bashrc`, or assuming `source` works outside bash. I still had to run the reproduction script myself, compare broken vs fixed regexes, and decide what belonged in the upstream PR vs course-only docs.

**What would you do differently if you started over?**
I’d finish local setup in Git Bash on day one before touching code, open a draft PR earlier in Week 9 for peer feedback in Slack, and write the focused regression file (`test_resume_section_whitespace.py`) first so I never fight mypy on the older untyped test module. I’d also keep course artifacts (`JOURNAL.md`, `PLAN.md`) clearly separated from the minimal fix commits in my head when writing the PR description.

**What are you most proud of from this module?**
Building a clear reproduction path — `scripts/reproduce_issue_147.py` showing old patterns return `[]` and the fixed parser returns Education/Skills — plus a small, targeted test suite that locks the edge cases from the plan. That made the PR feel like a real contribution, not just a one-line tweak.
