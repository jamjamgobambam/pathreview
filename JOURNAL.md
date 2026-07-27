# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview uses prompt templates to generate its reviews, and even small wording changes can affect the results. Right now, those changes can happen without being noticed or requiring the template version to be updated. This issue adds tests that detect changes to the templates and require a version bump, making edits intentional and easier to review.

The work will be done in tests/unit/test_prompt_templates.py and will cover the prompt templates in the rag module.

**Selection notes — "Is this right for me?" checklist:**

*Part 1 — Understanding the issue*
- **In my own words:** Prompt templates are the core of the reviews this project produces, so a test should exist that fails if a template's text changes without bumping its version — that way a change can't slip in silently.
- **Part affected:** The issue affects the `rag` module's prompt templates (`rag/generator/prompt_templates.py`); my test guards them and lives in `tests/unit/test_prompt_templates.py`.
- **What "done" looks like (before → after):** Before the fix, a developer can edit a template and the whole test suite still passes, so the change ships unnoticed. After the fix, editing a template without a version bump makes the snapshot test fail, forcing the developer to either revert or consciously bump the version and update the stored snapshot.

*Part 2 — Tier fit*
- This is my first contribution to a large open-source codebase, so I chose a Tier 1 issue. #37 is labeled `tier-1` and `good first issue`, which is the recommended starting point.

*Part 3 — Codebase readiness*
- **Found the code:** `PROMPT_TEMPLATES` is a two-level nested dict — outer keys are the 5 template names, inner keys are version labels (`"v1"`) mapping to the template text; `get_template(name, version="v1")` reads from it.
- **Rough plan:** The existing `test_template_snapshot_content_hash` already computes an MD5 hash of all template content but never asserts it against a known value. I'll store an expected hash (ideally per template) in the test and assert the current hash matches it, so any content change fails the test and a version bump + snapshot update is the deliberate escape hatch.
- **Read the test file:** Read `test_all_5_templates_exist` end-to-end — it builds a set of the 5 expected names and asserts it equals `set(PROMPT_TEMPLATES.keys())`, catching both missing and extra templates. These tests are fixture-free and assertion-based.

*Part 4 — Scope and time*
- **Claims:** 3 students in the ledger and ~13 claim comments on the issue. Claims are non-exclusive and grading is on my own artifacts, and I've already done the readiness work for this issue, so I'm comfortable staying on #37.
- **Time:** Estimated at 3–5 hours (Tier 1 range), and I'm confident I can complete it within Weeks 8–9.
- **Blockers:** No "blocked by" references or dependencies on other unresolved issues; the code it touches already exists and is self-contained.

**Branch name:** test/37-prompt-template-snapshot-tests

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** _(replace with the commit URL after pushing — the commit adding the reproduction note to `tests/unit/test_prompt_templates.py` + this Week 8 entry + PLAN.md)_

**Reproduction summary:**
I edited the `skills_feedback` template text in `rag/generator/prompt_templates.py` and ran `.venv/bin/pytest tests/unit/test_prompt_templates.py` — all 37 tests still PASSED, including `test_template_snapshot_content_hash`. That "snapshot" test only asserts the hash is a 32-char string (always true for any MD5) and never compares it to a stored value, so template wording can change silently without any test catching it or requiring a version bump. I restored the template afterward and documented the exact gap as a `REPRODUCTION — issue #37` comment on the no-op test.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Blockers or open questions:**
- Confirm with maintainers whether the snapshot should assert *exact* text hashes (trailing-whitespace-sensitive) vs. normalized text.
- Confirm snapshot storage preference: inline `EXPECTED_TEMPLATE_HASHES` dict vs. a separate JSON file.
- Ensure stored hashes reflect the post-`black`/`ruff` template text so the `make check` formatter pass doesn't cause snapshot drift.
