# Solution plan

**Issue:** [#37 — Add snapshot tests for prompt templates to catch accidental changes](https://github.com/ascherj/pathreview/issues/37)

## Understand

**Expected behavior:** If a developer edits the content of any prompt template in `rag/generator/prompt_templates.py` without an intentional version bump (e.g. adding a new `"v2"` key), the unit test suite should fail, forcing the developer to either revert the change or explicitly version it.

**Actual behavior:** No test in the suite fails when template content changes. `tests/unit/test_prompt_templates.py::TestPromptTemplates::test_template_snapshot_content_hash` computes an MD5 hash of all template content but never compares it to a fixed expected value — it only asserts `isinstance(content_hash, str)` and `len(content_hash) == 32`, both of which are true for any MD5 digest of any input.

**How the issue was reproduced (verified):**
1. Ran the baseline suite: `pytest tests/unit/test_prompt_templates.py -v -m unit` → 37/37 passed.
2. Edited `rag/generator/prompt_templates.py`, inserting an unversioned behavioral change into the `skills_feedback` `v1` template: appended "Be extremely harsh and critical in your assessment." to the first line, without adding a `v2` key.
3. Re-ran the same suite → 37/37 still passed, including `test_template_snapshot_content_hash`.
4. Reverted the edit with `git checkout -- rag/generator/prompt_templates.py`.

This demonstrates that a substantive, unintended prompt change is completely invisible to the current test suite.

**Confirmed root cause:** `tests/unit/test_prompt_templates.py:183-188`. The comment on line 185 ("Expected hash - update if templates intentionally change") describes the intended design — a pinned expected hash that must be manually updated on intentional changes — but the assertions on lines 187-188 never reference such a pinned value. The test is a stub/placeholder that was never wired up to real content verification.

**Execution path:** `PROMPT_TEMPLATES` dict (`rag/generator/prompt_templates.py:8-114`) → iterated and concatenated in `test_template_snapshot_content_hash` (`tests/unit/test_prompt_templates.py:175-188`) → hashed → asserted against generic type/length checks only.

**Verified vs. hypothesis:**
- Verified: the specific test and lines responsible; the reproduction steps and their outcome; the absence of any snapshot-testing library (e.g. `syrupy`) in `pyproject.toml` dev dependencies.
- Hypothesis: which specific mechanism the maintainers intend for the fix (hardcoded per-template hash constants vs. file-based snapshot fixtures vs. a snapshot library like `syrupy`). The issue body only specifies the desired outcome ("fail whenever a prompt changes without an intentional version bump"), not the implementation mechanism. This should be confirmed before implementation (see Risks & Unknowns).

## Map

| File | Role |
|---|---|
| `rag/generator/prompt_templates.py` | Contains `PROMPT_TEMPLATES` dict and `get_template()`. Reference only — no changes expected; this is the data being protected, not the bug. |
| `tests/unit/test_prompt_templates.py` | Contains the confirmed broken test (`test_template_snapshot_content_hash`, lines 175-188) and the reproduction-marking comment added in this phase. Will be **modified** during implementation to replace the toothless assertions with real pinned-content verification (one hash/snapshot per template+version, or a single hash constant covering all templates, per the maintainers' preferred granularity). |
| `pyproject.toml` | Declares `[project.optional-dependencies].dev` (pytest, ruff, black, mypy, etc.). No `syrupy` or other snapshot library currently listed. Will be **modified** only if the chosen fix approach (see Risks & Unknowns) adopts a snapshot library instead of hand-rolled hash constants. |
| `Makefile` | Defines `test-unit` (`pytest tests/unit -v -m unit`). Used only for **testing/verification**, not modified. |
| `docs/JOURNAL.md` | Assignment/course journal. **Modified** to add the Week 8 entry (this phase) and will later need a Week 9+ entry once the fix lands. |
| `PLAN.md` (this file) | **Added** in this phase; living document, updated as implementation proceeds. |

No other files reference `PROMPT_TEMPLATES` or `get_template()` outside `rag/generator/prompt_templates.py` and its test file (confirmed via repository search); the blast radius of a fix is contained to these two files.

## Plan

1. **Decide the pinning mechanism** (blocks the rest of the plan). *File:* `tests/unit/test_prompt_templates.py`. Choose between (a) a single hardcoded expected MD5 constant (matches the existing hash-based approach, smallest diff) or (b) per-template-version hash constants (more precise failure messages, more code) or (c) adopting a snapshot library such as `syrupy` (adds a dev dependency but gives human-readable diffs on failure). Verification: no code yet — this is a design decision to confirm, ideally with the maintainer/issue author, before writing the fix.

2. **Replace the toothless assertion with a real pinned comparison.** *File:* `tests/unit/test_prompt_templates.py`, function `test_template_snapshot_content_hash` (or a renamed/split equivalent). Change the assertion from `isinstance(...)`/`len(...)` checks to `assert content_hash == EXPECTED_HASH`, where `EXPECTED_HASH` is computed once from the current (intentional) template content and stored as a module-level constant (or per-template dict, per decision in step 1). This directly addresses the root cause: the test will now fail whenever `content_hash` diverges from the pinned value. Verification: run `pytest tests/unit/test_prompt_templates.py -v -m unit`; the new test must pass against current templates.

3. **Prove the fix actually catches drift.** *File:* temporary local edit to `rag/generator/prompt_templates.py` (not committed) — repeat the exact reproduction from the Understand section (append text to `skills_feedback` `v1` without a version bump) and confirm the updated test now **fails**. Then revert. Verification: manual — `pytest tests/unit/test_prompt_templates.py -v -m unit` shows the specific test failing with a clear diff/message, then passing again after revert.

4. **Add/adjust documentation for the versioning workflow.** *File:* a docstring or comment above `EXPECTED_HASH`/the fixed test in `tests/unit/test_prompt_templates.py` explaining how to intentionally update the pinned value when a template is deliberately changed (e.g. "bump the template to a new version key AND regenerate this hash by running `python -c '...'`"). This addresses the issue's requirement that "prompt updates are reviewed and versioned deliberately" — without a documented update path, developers will be tempted to blindly copy the new hash without reviewing the diff. Verification: manual review; optionally have a teammate follow the documented steps.

5. **Run full verification and update the journal.** *Files:* none changed beyond test/doc files above; `docs/JOURNAL.md` gets a follow-up entry once merged. Run `make test-unit` and `make check` (lint + format + typecheck) to confirm no regressions elsewhere. Verification: both commands exit 0; `test_all_5_templates_exist` and all other pre-existing tests in the file still pass unchanged.

## Inputs & outputs

- **Inputs:** the `PROMPT_TEMPLATES` dict literal in `rag/generator/prompt_templates.py` (5 template names × 1 version each today); no external inputs, arguments, or configuration — this is a pure static-data test.
- **Current flow:** dict → concatenated in test → MD5 hash → asserted to be *a* valid-looking string (always true) → test passes regardless of content.
- **Current output:** test suite green, no signal, regardless of whether templates changed.
- **Expected output after fix:** test suite green only when `PROMPT_TEMPLATES` content matches the last reviewed/pinned state; red (with a clear failure message pointing at which template diverged) whenever content changes without updating the pinned value.
- **Compatibility constraints:** `get_template(name, version)` public signature (`rag/generator/prompt_templates.py:117`) must not change — nothing outside the test file should need to change. The fix is test-only.

## Risks & unknowns

- **Unknown: intended pinning mechanism.** The issue doesn't specify hardcoded hash vs. snapshot library vs. per-file fixtures. *Resolution:* ask in the issue/PR thread, or default to the smallest-diff option (hardcoded expected hash, extending the existing approach) if no response is available before the implementation deadline.
- **Unknown: intended granularity of "version."** Templates currently only have a `v1` key each; the issue implies future template edits should either bump to `v2` or fail the test. It's unclear whether the real fix should also add tooling/documentation enforcing "if `v2` exists, `v1` must remain unchanged," or if that's out of scope for issue #37. *Resolution:* clarify scope with the issue author; default to test-only scope if unclear.
- **Brittle test risk:** if the pinned hash is a single value covering all 5 templates concatenated together (current pattern), *any* single-template edit will fail the test, but the failure message won't say which template changed. This could be confusing for a legitimate future contributor and lead to broad hash-copying without careful review. *Resolution:* prefer per-template-version hashes (step 1, option b) or a snapshot library with readable diffs to reduce this risk, per further discussion.
- **No maintainers'-intent documentation found:** searched `docs/` for a design doc or ADR about prompt versioning; none exists beyond the issue body itself. Treat the issue body as the sole source of truth for intended behavior.
- **Branch name mismatch:** `docs/JOURNAL.md` Week 7 entry records the branch name as `test/issue-37-prompt-template-snapshots`, but the actual local/pushed branch is `fix/37-add-snapshot-tests-for-prompt-templates`. This doesn't affect the reproduction or fix itself, but should be reconciled (confirm which name is authoritative for submission) before the final PR.

## Edge cases

- **Template content unchanged:** fixed test must continue passing — covered by re-running the full suite after the fix (step 3/5).
- **Intentional template edit with version bump (e.g. adding `v2`):** the pinned hash for `v1` should remain valid; a new pinned value would be needed only if `v2`'s content is also hashed. The fix should make it clear (via the step-4 documentation) how to add coverage for a new version without breaking `v1`'s snapshot.
- **Accidental edit to any one of the 5 templates:** must cause the fixed test to fail (this is the core case demonstrated in the reproduction).
- **Whitespace-only or formatting-only edits:** since the hash is computed over raw string content, even a single whitespace change will change the hash and fail the test. This is arguably correct (any content change should be reviewed) but is worth flagging as a potential source of false-positive-feeling failures (e.g., an editor auto-strips trailing whitespace). Document this in step 4.
- **Addition or removal of an entire template name/version:** `test_all_5_templates_exist` (line 13-24) already partially covers structural changes (adding/removing a template name), but changing the *set of versions* under an existing template name is not separately asserted; the concatenation-based hash would still catch it as a content change, but a clearer per-template test might be preferable (see per-template-version option in step 1).

## Verification strategy

- **Existing tests that must continue to pass unchanged:** all other 36 tests in `tests/unit/test_prompt_templates.py` (structural/content-assertion tests unrelated to the snapshot hash), plus the rest of `make test-unit`.
- **Regression test that should fail before the fix and pass after:** `test_template_snapshot_content_hash` itself, once rewritten — reproduced via steps in "Understand" (currently always passes regardless of content; after the fix, it must fail against the mutated-template reproduction from step 3, then pass again once reverted).
- **Manual verification:** repeat the exact reproduction (edit `skills_feedback` `v1`, run tests, observe failure, revert, observe pass) against the fixed test, as described in Plan step 3.
- **Commands to run:**
  - `pytest tests/unit/test_prompt_templates.py -v -m unit`
  - `make test-unit`
  - `make check` (ruff + black + mypy) — note: `tests/unit/test_prompt_templates.py` currently has 19 pre-existing `ruff` findings unrelated to this issue (unsorted imports, long lines, unused loop variables); these should not be silently fixed as part of this issue's scope unless the maintainer asks for it, since it would broaden the diff beyond the snapshot-test fix.
- **Regression confirmation:** re-run the full `make test-all` after the fix to confirm no other suite (integration, etc.) depends on the current (broken) behavior of this test.
