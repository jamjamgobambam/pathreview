# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/28

**Issue title:** Generator produces duplicate feedback sections when a user has multiple projects in the same tech stack

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
When a user has several projects built with the same tech stack (e.g. three Python projects), the review generator writes a nearly identical "Python skills" paragraph for each one instead of noticing the overlap. The feedback ends up repetitive rather than useful, because the generator treats every project independently instead of looking across projects for shared observations. A fix needs to deduplicate and consolidate these cross-project observations, most likely in `rag/generator/review_generator.py` and `rag/generator/output_parser.py`, so a user with multiple same-stack projects gets one consolidated skills section instead of several near-copies.

**Branch name:** fix/28-duplicate-feedback-sections

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes ("Is this issue right for me?" reasoning):**

- *Part 1 — Understanding the issue:* In my own words: when someone's portfolio has multiple projects in the same language/stack, the review generator writes an almost identical "skills" paragraph once per project instead of noticing they overlap and saying it once. The referenced files (`rag/generator/review_generator.py`, `rag/generator/output_parser.py`) exist and are where I traced the actual cause: `ReviewGenerator._consolidate_feedback` only dedupes by `section_name`, which is already unique across the 5 fixed sections, so it never catches this. The real problem is that `_format_context` concatenates retrieved chunks without grouping by project/tech stack before they're handed to the LLM. Done = a user with 3 same-stack projects gets one consolidated observation instead of 3 near-copies, without losing genuinely distinct feedback between projects.
- *Part 2 — Tier fit:* Labeled `tier-3` on the tracker, and that matches the actual scope — the fix touches chunk retrieval/grouping, prompt templates, and generator output, not a single isolated function. I've completed Tier 1/2 issues before, so this is a reasonable stretch rather than a first-time leap into unfamiliar scope.
- *Part 3 — Codebase readiness:* Read `review_generator.py`, `output_parser.py`, `prompt_templates.py`, and the ingestion metadata code (`ingestion/pipeline.py`) that already tags repo chunks with `language`/`tech_stack` — that metadata exists but isn't used at generation time yet. Checked the test file: `tests/unit/test_output_parser.py` covers `output_parser.py` in isolation, but there is **no existing test file for `review_generator.py`** — `tests/unit/test_review_service.py` tests a different module (`core/services/review_service.py`). I'll need to create `tests/unit/test_review_generator.py` from scratch as part of this fix.
- *Part 4 — Scope and time:* Two other students (`arunkasala-open`, `aishadeveloper`) have also commented claiming this issue, in addition to my own claim comment — per course policy claims are non-exclusive and grading is based on my own artifacts, so I'm comfortable proceeding. The issue's own estimate is 7–10 hours, which is on the lower end of typical Tier 3 scope and feels achievable in the Week 8–9 window. No "blocked by" labels or dependency references on the issue.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [test: reproduce issue #28 duplicate feedback sections](https://github.com/SuperCapper/pathreview/commit/e89d6d8)

**Reproduction summary:**
Added `tests/unit/test_review_generator.py` with a strict-`xfail` test that builds three same-tech-stack (`Python`) chunks, shaped like real ingestion output (`metadata.tech_stack`, `metadata.primary_language`), and passes them to `ReviewGenerator._format_context`. The test fails as expected today, proving `_format_context` still emits one independent numbered block per chunk with no shared-stack framing — the same mechanism that causes the LLM to write a near-duplicate skills paragraph per project. A second, passing test confirms `_consolidate_feedback` is not a safety net for this: it only dedupes by `section_name`, which is already unique across the 5 fixed sections `generate_full_review` always produces.

**PLAN.md link:** [PLAN.md](https://github.com/SuperCapper/pathreview/blob/fix/28-duplicate-feedback-sections/PLAN.md)

**Walkthrough video (recommended):** _not recorded this week_

**Blockers or open questions:**
- Need to confirm whether `tech_stack`/`primary_language` metadata is reliably present on every repo chunk that reaches the generator, or whether some retrieval paths strip it before it gets here — affects how defensive the grouping fallback needs to be.
- Open design question for Week 9: should stack-grouping happen in a new dedicated helper (e.g. `context_grouper.py`) or inline in `_format_context`? Leaning toward a small dedicated helper for testability, but will decide once I start implementation.
