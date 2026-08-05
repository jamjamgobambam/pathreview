
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
