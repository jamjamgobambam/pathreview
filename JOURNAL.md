## Week 7 — Issue selection

**Issue link:** [Issue](https://github.com/ascherj/pathreview/issues/37)

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
There's already a test that looks like a snapshot test for the prompt templates, but it just computes a hash and never checks it against anything fixed, so it passes no matter what changes. That means someone could quietly reword a template and every test would still go green. The fix is to make that test actually compare against a saved expected hash, so it fails unless the version gets bumped on purpose.

**Branch name:** test/37-snapshot-tests-prompt-templates

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/riyan42069/pathreview/commit/db973ec

**Reproduction summary:**
Ran the existing `test_template_snapshot_content_hash` test and confirmed it passes at baseline. Then computed the same MD5 hash logic against a version of `PROMPT_TEMPLATES` with a wording edit to `skills_feedback` v1 (no version bump) - the hash changed as expected, but the test's actual assertions (`isinstance(hash, str)`, `len(hash) == 32`) pass regardless, since they never compare against a fixed expected value.

**PLAN.md link:** https://github.com/riyan42069/pathreview/blob/test/37-snapshot-tests-prompt-templates/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min - recommended, not graded]

**Blockers or open questions:**
None blocking - the fix is clear: pin an expected hash (or per-template expected hashes) in the test and assert equality, failing when content changes without a matching version key bump.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md - steps 1 through 5 are done. Confirmed no existing snapshot-testing library/convention is used elsewhere in the repo, so I hand-rolled per-template-per-version expected hashes (`EXPECTED_TEMPLATE_HASHES`) in `tests/unit/test_prompt_templates.py` instead of a single combined hash, since it gives failures that name the exact template/version that drifted. Rewrote `test_template_snapshot_content_hash` to assert against those recorded hashes, and added `test_no_new_templates_or_versions_are_missing_a_snapshot` to catch a new template being added without a recorded hash. Verified the fix works both ways: unmodified templates pass, and a temporary deliberate wording edit (reverted after) made the test fail with a clear message. Committed as `b8a680e`.

**Next steps:**
Self-review against `docs/CONTRIBUTING.md` (branch name, commit message, docstrings), run `make check` and `make test-unit`, document any pre-existing failures, then push the branch and open the PR.

**Blockers:**
None. `make check` and `make test-unit` both surface a large number of pre-existing failures/errors unrelated to this change (163 ruff errors, 5 mypy errors, 53 failing unit tests across other modules) - confirmed these exist identically on the commit before my fix, so they're not something I introduced.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** `test/37-snapshot-tests-prompt-templates`

**What you built:**
Replaced the fake "snapshot" test in `tests/unit/test_prompt_templates.py` with a real one. `test_template_snapshot_content_hash` now compares each template/version's live MD5 hash against a recorded expected hash in `EXPECTED_TEMPLATE_HASHES`, so any wording change without a deliberate version bump + hash update now fails the test suite instead of silently passing.

**Tests added or updated:**
`tests/unit/test_prompt_templates.py` - rewrote `test_template_snapshot_content_hash` to assert real equality instead of generic type/length checks, and added `test_no_new_templates_or_versions_are_missing_a_snapshot` to guard against a new template/version being added with no recorded hash. Also cleaned up pre-existing ruff violations (unused loop variables, `dict.keys()` iteration) and added missing `-> None` return annotations across the file's test methods so it passes the repo's pre-commit hooks.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both defined as: my changes introduce no new failures. `make check` has 163 pre-existing ruff errors and 5 pre-existing mypy errors unrelated to this change - confirmed present on the commit before my fix, and `test_prompt_templates.py` contributes zero of them. `make test-unit` has 53 pre-existing failures in unrelated modules, also confirmed present before my fix; all 38 tests in `test_prompt_templates.py` pass.)

**Draft PR feedback received from:** none