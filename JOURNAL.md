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

**PR link:** https://github.com/ascherj/pathreview/pull/716

**Branch:** `test/37-snapshot-tests-prompt-templates`

**What you built:**
Replaced the fake "snapshot" test in `tests/unit/test_prompt_templates.py` with a real one. `test_template_snapshot_content_hash` now compares each template/version's live MD5 hash against a recorded expected hash in `EXPECTED_TEMPLATE_HASHES`, so any wording change without a deliberate version bump + hash update now fails the test suite instead of silently passing.

**Tests added or updated:**
`tests/unit/test_prompt_templates.py` - rewrote `test_template_snapshot_content_hash` to assert real equality instead of generic type/length checks, and added `test_no_new_templates_or_versions_are_missing_a_snapshot` to guard against a new template/version being added with no recorded hash. Also cleaned up pre-existing ruff violations (unused loop variables, `dict.keys()` iteration) and added missing `-> None` return annotations across the file's test methods so it passes the repo's pre-commit hooks.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both defined as: my changes introduce no new failures. `make check` has 163 pre-existing ruff errors and 5 pre-existing mypy errors unrelated to this change - confirmed present on the commit before my fix, and `test_prompt_templates.py` contributes zero of them. `make test-unit` has 53 pre-existing failures in unrelated modules, also confirmed present before my fix; all 38 tests in `test_prompt_templates.py` pass.)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review has come in on PR #716 yet.

**How you responded:**
N/A - nothing to respond to yet. If feedback comes in after submission, I'll follow up in a comment on the PR itself rather than editing this journal further, since Week 10 is meant to be the final entry.

---

### Reflection

**What was harder than you expected?**
Figuring out that the existing test was fake took more than a glance. `test_template_snapshot_content_hash` looked complete on first read, it had a docstring calling it a snapshot test, it computed a real hash, it had reasonable-looking assertions. I only caught that it wasn't actually checking anything by reading the two assertions line by line and realizing `isinstance(hash, str)` and `len(hash) == 32` are true for literally any MD5 hash, not just the "right" one. That's a different kind of bug than I expected going in - I was ready to debug broken logic, not to notice logic that was quietly checking nothing at all.

The other surprise was the pre-commit hooks. My actual fix was small, maybe 15 lines of real change, but committing it failed on ruff and mypy errors for unused loop variables and missing return type annotations that had nothing to do with my change and had clearly been sitting in that file for a long time. I had to fix all of them just to get my own commit through, which meant touching almost every method in the file even though my actual logic change was tiny.

**What did you learn about working in a large codebase?**
The biggest thing was that "does the test suite pass" isn't a yes/no question in a codebase this size. Before I could even claim my change didn't break anything, I had to establish what was already broken - I checked out the commit before my fix and ran `make check` and `make test-unit` against it to get a real baseline (163 ruff errors, 5 mypy errors, 53 failing tests, none of it related to prompt templates). Without that baseline, I couldn't have told the difference between "my change is fine" and "my change happens to run in a codebase with unrelated problems." In a personal project there's no such thing as a pre-existing failure, everything failing is yours. Here, most of what's red has nothing to do with you, and part of the job is proving that.

**How did AI tools help - and where did they fall short?**
AI was most useful for the mechanical, repeatable parts: writing the throwaway reproduction script that mirrored the real test's logic without touching tracked files, generating the actual baseline MD5 hashes instead of guessing at them, and running the same before/after comparison (checking out the prior commit in a worktree, rerunning checks) reliably each time. It was also useful for drafting and iterating on the PR description and journal entries once I told it what actually happened.

Where it fell short: it couldn't open the PR for me since the `gh` CLI wasn't installed in this environment, so I had to do that step manually through the GitHub web UI. It also couldn't tell me on its own whether the pre-existing ruff/mypy/test failures mattered for this PR - that judgment call (are these actually pre-existing, is it safe to claim "no new failures") required me to actually direct it to check out the prior commit and compare, rather than trusting a single run of `make check` at face value.

**What would you do differently if you started over?**
I'd run `make check` and `make test-unit` in week 8, right after reproducing the bug, instead of waiting until the self-review step in week 9. I found out about the pre-existing lint and mypy issues late, which meant a chunk of week 9 went into cleaning up code I didn't write instead of just my actual fix. Establishing the "here's what's already broken" baseline earlier would have saved time and made the eventual self-review section easier to write with confidence instead of scrambling to verify it right before opening the PR.

**What are you most proud of from this module?**
Actually proving the fix works instead of just trusting the logic on paper. I temporarily edited a template's wording, reran the test, watched it fail with a message naming the exact template and version, then reverted the edit and confirmed everything went back to green. It would have been easy to write the hash-comparison logic, see it look reasonable, and call it done - the extra step of deliberately breaking something to watch my own test catch it is what actually gave me confidence the fix does what the issue asked for, instead of just resembling a fix.