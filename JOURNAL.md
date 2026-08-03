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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the core fix from PLAN.md: a new `ReviewGenerator._group_chunks_by_stack` static method (`rag/generator/review_generator.py`) that buckets context chunks by `metadata.primary_language` (falling back to `tech_stack`, then to an ungrouped per-chunk bucket if neither is present) before `_format_context` builds the prompt string. Same-stack chunks now render as a single `"Shared stack: <language> -- N related projects"` block instead of N independent numbered blocks. Also updated the `skills_feedback` and `projects_feedback` prompt templates (`prompt_templates.py`) to explicitly instruct the model to consolidate observations for "Shared stack" blocks instead of repeating them per project.

One deviation from PLAN.md worth flagging: the plan said to bucket primarily by `tech_stack`, falling back to `primary_language`. I flipped that precedence and grouped by `primary_language` first. The reproduction test's own fixtures explain why: three "Python" projects with *different* `tech_stack` lists (`["Python","Flask"]`, `["Python"]`, `["Python","Pandas"]`) only group correctly under a shared primary language, not a shared exact stack list. Grouping strictly by `tech_stack` would have left all three in separate buckets and failed the test I wrote to specify the bug.

Removed the `strict=True` `xfail` marker from `test_same_stack_chunks_are_grouped_not_repeated` now that it passes for real, and added four more cases to `tests/unit/test_review_generator.py`: single-project (output byte-for-byte unchanged from before this fix), mixed-stack (no incorrect merging across genuinely different stacks), missing stack metadata (README/resume-shaped chunks degrade to their own ungrouped block instead of crashing), and the existing top-10-chunk retrieval limit (an 11th same-stack chunk still never appears in the formatted context).

Decided against the optional backstop dedup step in `output_parser.py` from PLAN.md's risk section. The grouping fix is deterministic and runs before the LLM call, and it's fully covered by unit tests at the `_format_context` level. A second heuristic dedup pass over LLM output would add complexity with no good way to test it in this suite.

**Next steps:**
Run the full `make check` / `make test-unit` pass, confirm no regressions against the pre-existing failures noted below, then open the PR.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** [#682 — fix(rag): group same-stack chunks so generator stops repeating feedback](https://github.com/ascherj/pathreview/pull/682)

**Branch:** `fix/28-duplicate-feedback-sections`

**What you built:**
Fixed issue #28: the review generator's `_format_context` now groups retrieved chunks by shared tech stack (primarily `metadata.primary_language`) before building the LLM prompt, so a portfolio with multiple same-stack projects is presented as one "Shared stack" block instead of N independent blocks. Paired prompt-template instructions tell the model to write one consolidated observation for grouped projects instead of a near-duplicate paragraph per project. Single-project profiles, chunks from different stacks, and chunks with no stack metadata are all unaffected: this adds grouping on top of the existing per-chunk format rather than rewriting it.

**Tests added or updated:**
`tests/unit/test_review_generator.py` — removed the `strict` `xfail` from the Week 8 reproduction test (`test_same_stack_chunks_are_grouped_not_repeated`) now that it passes, and added: `test_single_project_output_is_unchanged`, `test_mixed_stack_chunks_are_not_merged`, `test_chunks_missing_stack_metadata_degrade_gracefully`, `test_grouping_respects_existing_top_10_chunk_limit`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Pre-existing failures observed (unrelated to this change):** Before starting, `make test-unit` had 53 pre-existing failures spread across unrelated modules (`test_bias_detector.py`, `test_resume_parser.py`, `test_review_service.py`, `test_pii_scrubber.py`, `test_skill_extractor.py`, `test_tech_detector.py`, and others), plus one pre-existing failure in a file this fix touches only incidentally: `test_output_parser.py::test_json_array_fallback`, unrelated to `_format_context` since `output_parser.py` itself was not modified. After this change, `make test-unit` still shows the same 53 pre-existing failures and no new ones. The file under test gained 5 net new passing tests (2 → 6, with the former `xfail` now a real pass). Separately, running `mypy` directly through the repo's local `.venv` hits an unrelated, pre-existing failure: a numpy stub uses `type X = ...` syntax that this environment's mypy rejects before it can check any project files. The `pre-commit` `mypy` hook runs in its own isolated environment, is what actually gates commits and CI, and passes cleanly against the changed files.

**Draft PR feedback received from:** none. Solo AI 201 submission, self-reviewed against `docs/CONTRIBUTING.md` (branch naming, conventional commit format, docstrings) before opening.
