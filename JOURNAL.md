# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37  
**Issue title:** Add snapshot tests for prompt templates to catch accidental changes  
**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3  

**Problem summary:** PathReview's prompt templates directly shape the feedback produced by the review pipeline, but the existing test only checks that a generated MD5 value has the right type and length. That assertion still passes when template wording changes, so accidental edits can silently alter review behavior without requiring a new template version. The work is localized to `tests/unit/test_prompt_templates.py` and the versioned templates in `rag/generator/prompt_templates.py`. A successful change will store deterministic expectations for each named template version and fail when an existing version's content changes, making intentional prompt changes require an explicit version bump and reviewed snapshot update.

**Branch name:** `test/37-prompt-template-snapshots`  
**Setup confirmation:** [x] App runs locally at localhost:5173  
**Cohort ledger:** [x] Issue added to cohort ledger (Section 1B, row 33)

### "Is this right for me?" selection notes

#### Part 1 — Understanding the issue

- [x] I can explain the problem and expected behavior: the current hash test does not compare against a saved value, so it cannot detect prompt changes; version-keyed snapshots should make same-version edits fail.
- [x] I located the affected files: `tests/unit/test_prompt_templates.py` contains the ineffective snapshot assertion, and `rag/generator/prompt_templates.py` contains the versioned prompt strings.
- [x] I understand what done looks like: tests pass for the current templates, fail if any existing version is edited, and make an intentional prompt change visible as a new version and snapshot.

#### Part 2 — Tier fit

- [x] Issue #37 is labeled Tier 1 and is a realistic fit because the change is self-contained in the prompt-template unit tests, with at most a small supporting snapshot fixture.
- [x] The task does not require a cross-module feature, database change, API change, or redesign of the RAG pipeline.

#### Part 3 — Codebase readiness

- [x] I read the relevant implementation, including the nested `PROMPT_TEMPLATES` name/version mapping and `get_template()` lookup behavior.
- [x] I read `tests/unit/test_prompt_templates.py` end-to-end and confirmed the current `test_template_snapshot_content_hash` assertion cannot catch content changes.
- [x] My implementation plan is to create deterministic, version-keyed snapshots, compare the current template/version inventory and content against those snapshots, and add a regression test that demonstrates a same-version mutation is rejected.

#### Part 4 — Scope and time

- [x] I reviewed the issue comments and understand that claims are non-exclusive; multiple students may work on the same issue.
- [x] The issue estimate is 3–5 hours, which is realistic within the Week 8–9 implementation window.
- [x] The issue lists no blockers or dependencies on unresolved work.

**Verdict:** Issue #37 is well understood, appropriately scoped, and ready for implementation on this branch.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/neonforestmist/pathreview/commit/f3f028851e87f0095f512160bd9d976d433a6943

**Reproduction summary:** I ran the existing snapshot test, changed `skills_feedback/v1` in an isolated Python process by appending `ACCIDENTAL SAME-VERSION EDIT`, and ran the assertion again. The test still passed while the template remained at version `v1`, confirming that the current MD5 type-and-length checks do not detect accidental prompt changes.

**PLAN.md link:** https://github.com/neonforestmist/pathreview/blob/test/37-prompt-template-snapshots/PLAN.md

**Walkthrough video (recommended):** Not recorded (optional and not graded)

**Blockers or open questions:** No blockers. The plan uses inline, version-keyed SHA-256 hashes so prompt additions and intentional version changes remain explicit in code review.

### Reproduction steps

1. Confirm the current test passes:

   ```bash
   .venv/bin/pytest tests/unit/test_prompt_templates.py::TestPromptTemplates::test_template_snapshot_content_hash -q
   ```

2. In an isolated Python process, append text to an existing version and invoke the same test:

   ```python
   from tests.unit.test_prompt_templates import TestPromptTemplates
   from rag.generator.prompt_templates import PROMPT_TEMPLATES

   original = PROMPT_TEMPLATES["skills_feedback"]["v1"]
   PROMPT_TEMPLATES["skills_feedback"]["v1"] = (
       original + "\nACCIDENTAL SAME-VERSION EDIT"
   )
   TestPromptTemplates().test_template_snapshot_content_hash()
   ```

**Observed result:** Both runs pass. `test_template_snapshot_content_hash` computes an MD5 digest but only checks that the result is a 32-character string, which is true for every MD5 digest regardless of the prompt content.

**Expected result:** A content change to an existing `(template name, version)` pair should fail the snapshot test and direct the contributor to add a new prompt version and its reviewed snapshot.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:** I completed all five subtasks from `PLAN.md`: added the five reviewed `v1` SHA-256 snapshots, implemented version-keyed hashing and inventory validation, replaced the ineffective MD5 shape check, and added regression tests for same-version edits and unreviewed versions. The changed test module passes Ruff, Black, the repository's pre-commit mypy check, and all 39 focused tests.

**Next steps:** Complete the final self-review, open the upstream pull request with full verification instructions, add its link to this journal and the cohort ledger, and submit the working branch through the course portal.

**Blockers:** No blocker affects issue #37. Untouched `upstream/main` already has repository-wide lint findings and 53 failing unit tests; the branch has the same 53 failures while adding two passing prompt-snapshot regression tests.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/698

**Branch:** `test/37-prompt-template-snapshots`

**What you built:** I replaced the aggregate MD5 type-and-length assertion with reviewed SHA-256 snapshots keyed by prompt name and version. The new assertions identify inventory changes and same-version content edits, while leaving production prompt text and runtime behavior unchanged.

**Tests added or updated:** Updated `tests/unit/test_prompt_templates.py`. `test_template_snapshot_content_hash` now validates the complete prompt-version inventory and every reviewed digest; `test_template_snapshot_rejects_same_version_content_change` proves an edit to `skills_feedback/v1` fails; and `test_template_snapshot_rejects_unreviewed_version` proves a new `v2` cannot pass without an explicit snapshot.

**Self-review confirmation:**

- [x] `make check` introduces no new failures. The changed file passes Ruff, Black, and pre-commit mypy; the repository-wide command remains blocked by unrelated lint findings already present on `upstream/main`.
- [x] `make test-unit` introduces no new failures. Untouched `upstream/main` reports 53 failed and 375 passed; this branch reports the same 53 failed and 377 passed, including both new regression tests.

**Draft PR feedback received from:** None. The implementation was completed after the scheduled deadline, so no peer review was received before submission.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:** No reviewer or maintainer feedback has arrived on [PR #698](https://github.com/ascherj/pathreview/pull/698). The pull request remains open and ready for review, so there were no requested changes to evaluate or implement during Week 10.

**How you responded:** No response or follow-up commit was needed because no feedback was received. I will respond to any later review by confirming the requested behavior, making focused changes on this branch, and documenting the verification results in the pull request.

---

### Reflection

**What was harder than you expected?**

The hardest part was recognizing that `test_template_snapshot_content_hash` looked meaningful without actually protecting the prompts: it calculated an MD5 digest but only checked that the digest was a 32-character string. Reproducing that weakness safely required mutating `skills_feedback/v1` in an isolated process, proving the test still passed, and then separating failures caused by my branch from the 53 unit-test failures and lint findings already present on `upstream/main`.

**What did you learn about working in a large codebase?**

I learned that a focused change still has to be understood in the context of the repository's conventions, existing test health, and review expectations. Instead of changing production prompt text in `rag/generator/prompt_templates.py`, I kept the implementation in `tests/unit/test_prompt_templates.py`, followed the `test/37-prompt-template-snapshots` branch convention, and compared my results with an untouched upstream checkout so I could show that the branch introduced no new failures.

**How did AI tools help — and where did they fall short?**

AI tools helped me trace the prompt-template structure, turn issue #37 into a concrete reproduction, design the version-keyed SHA-256 assertions, and check the journal and pull request against the course rubrics. They could not decide whether a future prompt edit is intentional, automatically make the repository's pre-existing failures relevant to my change, or replace my review of the generated hashes and failure messages; I still had to verify the original prompt content, run the focused tests, and interpret the branch-versus-upstream results.

**What would you do differently if you started over?**

I would run both the focused prompt tests and the repository-wide checks immediately after setup, before implementation, so the upstream baseline was documented from the beginning. I would also prepare the reproduction and request feedback earlier, which would leave more time to discuss whether the snapshots should remain inline in the test module or move to dedicated fixture files as the prompt inventory grows.

**What are you most proud of from this module?**

I am most proud that the final tests replace a false sense of safety with a precise, reviewable contract for every `(template name, version)` pair. All 39 focused prompt-template tests pass, and the two new regression cases demonstrate that both an accidental same-version edit and an unreviewed `v2` addition now fail with messages that identify exactly what a contributor needs to address.
