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

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
Ran the existing `test_template_snapshot_content_hash` test and confirmed it passes at baseline. Then computed the same MD5 hash logic against a version of `PROMPT_TEMPLATES` with a wording edit to `skills_feedback` v1 (no version bump) - the hash changed as expected, but the test's actual assertions (`isinstance(hash, str)`, `len(hash) == 32`) pass regardless, since they never compare against a fixed expected value.

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min - recommended, not graded]

**Blockers or open questions:**
None blocking - the fix is clear: pin an expected hash (or per-template expected hashes) in the test and assert equality, failing when content changes without a matching version key bump.