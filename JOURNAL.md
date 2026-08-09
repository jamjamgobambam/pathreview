## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/69

**Issue title:** Add a "feedback tone check" that ensures all generated feedback is written constructively

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
After PathReview generates feedback for a user, there is currently no check on whether that feedback is written constructively. This issue asks for a tone classification step to run after generation, using a prompt to judge whether each feedback section is constructive (actionable, specific, encouraging) or negative (discouraging, vague, dismissive). Sections that fail the check should be rejected and regenerated rather than shown to the user. The main files affected are `safety/content_filter.py` and `rag/generator/review_generator.py`, so the fix touches both the safety layer and the review generation pipeline.

**Branch name:** feat/69-feedback-tone-check

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/SaimM2007/pathreview/commit/271b823

**Reproduction summary:**
I added a test showing that `ContentFilter.filter()` only catches explicitly harmful content and has no concept of constructive vs discouraging tone. A harsh but non-harmful feedback string passes through unchanged, confirming the tone check gap described in issue #69.

**PLAN.md link:** https://github.com/SaimM2007/pathreview/blob/feat/69-feedback-tone-check/PLAN.md

**Blockers or open questions:**
Still unsure how strict the tone classification prompt should be without over-rejecting valid critical feedback.

## Week 9 — Implementation & PR Submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the `ToneChecker` class in `safety/content_filter.py`, alongside the existing `ContentFilter`. It takes the same LLM client used for review generation and classifies a piece of feedback text as constructive or negative using a dedicated prompt — distinguishing "critical but specific and actionable" feedback (which should pass) from "vague or dismissive" feedback (which should fail), per the distinction laid out in PLAN.md. Also handled the empty/short-content edge case identified in planning: `ToneChecker.check()` returns constructive without calling the LLM when there's nothing meaningful to classify, so it can't get stuck looping on blank input.

**Next steps:**
Wire `ToneChecker` into `ReviewGenerator.generate_section()` so every generated section is checked before being returned, with a capped retry/regeneration loop and a logged fallback if it never passes. Then write unit tests for both files and run `make check` / `make test-unit`.

**Blockers:**
None so far.

---

### Check-in 2 (end of week)

**PR link:** [paste your PR link here once opened]

**Branch:** feat/69-feedback-tone-check

**What you built:**
Wired `ToneChecker` into `ReviewGenerator.generate_section()` — the original generation logic was extracted into a `_generate_section_once()` helper, and `generate_section()` now runs the tone check after each generation, regenerating up to `MAX_TONE_RETRIES` (2) times if a section fails. If a section still fails after all retries, the last attempt is returned with its confidence score lowered rather than looping indefinitely, and a `structlog` warning is logged so the fallback is visible in logs rather than silent.

**Tests added or updated:**
`tests/unit/test_content_filter.py` — added tests for `ToneChecker` covering constructive feedback, negative feedback, critical-but-specific feedback (must not be falsely flagged), and the empty-content edge case. `tests/unit/test_review_generator_tone_check.py` (new) — covers `generate_section()` passing on the first attempt, succeeding after one regeneration, and falling back correctly after exhausting all retries. Ran the full unit suite (428 tests) before and after this change: 53 pre-existing failures exist on `main` in unrelated modules (`review_service`, `resume_parser`, `security`, `skill_extractor`, etc.), and this branch introduces 0 new failures. Similarly, `make check` (lint) reports pre-existing issues across the repo that predate this branch — none in the files this PR touches.

**Self-review confirmation:** [x] tests for this issue (`test_content_filter.py`, `test_review_generator_tone_check.py`) pass — 8/8  [x] no new lint or test failures introduced vs. `main`

**Draft PR feedback received from:** None