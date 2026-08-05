
## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The application’s prompt templates directly influence the quality and consistency of generated reviews, but there are currently no snapshot tests protecting their content. This means a developer could accidentally modify a prompt template without updating its version, causing unexpected behavior that may be difficult to notice during review. The issue affects the prompt-template unit tests in `tests/unit/test_prompt_templates.py`. A successful fix will add snapshot tests that fail whenever a prompt changes without an intentional version bump, ensuring prompt updates are reviewed and versioned deliberately.

**Branch name:** `test/issue-37-prompt-template-snapshots`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/KhoaDao03/pathreview/commit/8bd84c3f522af587345310e36a61bf355cd80108

**Reproduction summary:**
Confirmed that `tests/unit/test_prompt_templates.py::TestPromptTemplates::test_template_snapshot_content_hash` computes an MD5 hash of all prompt template content but only asserts `isinstance(content_hash, str)` and `len(content_hash) == 32` — it never compares the hash to a pinned expected value. Verified by temporarily appending an unversioned behavioral change to the `skills_feedback` `v1` template in `rag/generator/prompt_templates.py` and re-running `pytest tests/unit/test_prompt_templates.py -v -m unit`: all 37 tests still passed, proving no test currently catches an accidental prompt-template change. Change was reverted after confirming; a comment marking the confirmed root-cause lines (183-188) was added as the reproduction artifact.

**PLAN.md link:** https://github.com/KhoaDao03/pathreview/blob/fix/37-add-snapshot-tests-for-prompt-templates/PLAN.md

**Blockers or open questions:**
- ~~Branch name mismatch~~ — Resolved: `fix/37-add-snapshot-tests-for-prompt-templates` is authoritative (matches `docs/CONTRIBUTING.md`'s `<type>/<issue-number>-<short-description>` convention and is the branch actually pushed to origin).
- ~~Pinning mechanism unknown~~ — Resolved in Week 9: implemented per-template-version pinned hashes (`EXPECTED_TEMPLATE_HASHES`), chosen over a single combined hash or adopting `syrupy`, so a failure names exactly which template drifted.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from `PLAN.md`'s Plan steps 1-4: replaced the toothless `isinstance`/`len()` assertions in `test_template_snapshot_content_hash` with real per-(template, version) pinned MD5 hashes (`EXPECTED_TEMPLATE_HASHES`), plus a companion assertion that catches a template/version being added or removed without a corresponding hash entry. Verified the fix actually catches drift by repeating the Week 8 reproduction (appending text to `skills_feedback` v1) against the *fixed* test — it now fails with a message naming the exact template, then passes again after reverting. Ran full `make check` / `make test-unit` baselines before and after: identical 53 pre-existing test failures and 19 pre-existing `ruff` findings in the touched file, both unrelated to this issue — no new failures introduced. Also caught and reverted an unrelated `frontend/package-lock.json` diff that had been accidentally staged.

**Next steps:**
Self-review against `docs/CONTRIBUTING.md` is done (see Check-in 2). Commit pushed and draft PR opened (#853). Remaining: request peer/mentor feedback in the instructor Slack channel per Phase 8, address any feedback, then mark the PR ready for review.

**Blockers:**
None — the two open questions from Week 8 (branch name, pinning mechanism) are resolved above.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/853

**Branch:** `fix/37-add-snapshot-tests-for-prompt-templates`

**What you built:**
Fixed issue #37 by rewriting `test_template_snapshot_content_hash` in `tests/unit/test_prompt_templates.py` to compare each prompt template's MD5 hash against a pinned per-(name, version) expected value (`EXPECTED_TEMPLATE_HASHES`), instead of only checking that the hash is *a* valid-looking string. An accidental edit to any template now fails the test with a message identifying exactly which template and version changed; a companion key-set assertion also catches templates/versions added or removed without updating the pinned hashes.

**Tests added or updated:**
- `tests/unit/test_prompt_templates.py::TestPromptTemplates::test_template_snapshot_content_hash` — rewritten to assert real pinned-hash equality per template/version (previously a no-op check). Confirmed it fails on unversioned drift and passes on the current, reviewed template content.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*(Both commands still surface only the same pre-existing, unrelated failures documented in the PR description — 19 pre-existing `ruff` findings in this file, 53 pre-existing unit-test failures repo-wide, none touching `prompt_templates.py` — with zero new failures introduced.)*

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback


**Summary of feedback:**
As of this entry, PR #853 is still in draft with no comments beyond my own PR description, no reviewers requested, and no approvals or change requests on GitHub.

**How you responded:**
N/A — no feedback is needed for this iteration.

---

### Reflection

**What was harder than you expected?**
Understanding the bug itself took longer than I expected, mostly because the broken test didn't look obviously broken. `test_template_snapshot_content_hash` computes a real MD5 hash of the template content, so at a glance it looks like a working snapshot test. The actual problem is that it only asserts `isinstance(content_hash, str)` and `len(content_hash) == 32` — both true for any hash of any input — so it never compares against a pinned value. I only really believed this once I reproduced it myself: temporarily appending a sentence to the `skills_feedback` v1 template, rerunning `pytest tests/unit/test_prompt_templates.py -v -m unit`, and watching all 37 tests pass anyway, including the "snapshot" one. Seeing a test suite go green on a change that should have been caught was more convincing than just reading the assertion lines.

**What did you learn about working in a large codebase?**
Before touching anything, I had to confirm that `PROMPT_TEMPLATES` and `get_template()` weren't used anywhere outside `rag/generator/prompt_templates.py` and its test file — otherwise a "test-only" fix could have had a wider blast radius than it looked like. I also ran into a real inconsistency between the project's layers of tooling: CI's `typecheck` job only runs `mypy` against `api/ core/ ingestion/ rag/ agent/ safety/`, but the local pre-commit hook runs `mypy` with `disallow_untyped_defs = true` against whatever file is staged, tests included. That meant a commit could fail locally for reasons CI would never flag. I hadn't thought about "passing checks" as something that could differ between environments in the same repo. I also had to be careful about scope creep that wasn't really about my change at all — an unrelated `frontend/package-lock.json` diff had gotten staged from a stray `npm install`, and a chunk of `black` reformatting on lines I never touched crept into the diff. Reverting both to keep the diff to just the fix was as much a part of "editing a shared codebase" as writing the fix itself.

**How did AI tools help — and where did they fall short?**
The AI did most of the mechanical work this week: reproducing the bug, drafting the three possible fix designs (a single combined hash, per-template-version hashes, or adopting a snapshot library like `syrupy`), writing the actual test rewrite, and later machine-editing all 37 test methods to add `-> None` annotations once the pre-commit hook demanded it. My own role was mostly making the calls it surfaced — picking per-template hashes over the other two options, deciding to fix the pre-existing lint/type issues rather than bypass the hook with `--no-verify`, and reviewing the diffs it showed me before approving each step. I didn't personally catch a specific mistake in what it produced this week; I mostly reviewed and agreed with what it proposed. That's worth being honest about as a limitation of how I used it: I got a working, well-tested fix, but I have less hands-on memory of things like resolving the `ruff` findings or writing the `mypy` fix myself than I would if I'd done that part by hand. The AI also couldn't finish the job on its own — it had no GitHub credentials in its environment, so I had to personally push the branch and open the PR.

**What would you do differently if you started over?**
I'd spend more time exploring `test_prompt_templates.py` and `prompt_templates.py` directly during the planning weeks, before locking in a plan. Since understanding the bug was the hardest part for me, getting more comfortable with exactly how `PROMPT_TEMPLATES`, `get_template()`, and the existing test patterns fit together earlier would have made the implementation week faster and made me rely less on the AI to explain things I could have figured out myself with more upfront reading.

**What are you most proud of from this module?**
I'm most proud that I understood the root cause well enough to actually direct the fix instead of just accepting whatever came first. When the AI laid out three different ways to pin the template hashes, I could reason about the tradeoff — a single combined hash would fail without saying which template changed, while per-template hashes would name the exact one — and pick the option that mattered for someone debugging a real failure later. That's a small decision, but it's the part of this module that felt like actual engineering judgment rather than just following instructions.
