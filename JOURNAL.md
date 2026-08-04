## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `rag/generator/prompt_templates.py` module holds versioned prompt templates used by the review generator, but nothing currently enforces that changes to a template are accompanied by a version bump. A developer can silently edit the text of `v1` (or any existing version) and the app will keep running, quietly shipping different LLM behavior. The existing `tests/unit/test_prompt_templates.py` has a placeholder "snapshot" test that only checks the length of a hash string, so it does not actually catch content changes. A successful fix adds real per-template hash snapshots so that any modification to an existing version fails the test suite, forcing developers to add a new version (e.g., `v2`) instead of silently mutating `v1`.

**Branch name:** feat/37-prompt-template-snapshots

**"Is this right for me?" reasoning:**
Scope matches the Tier 1 estimate (3–5 hours) — I finished in ~4 hours.
Skills align well: I already work with LLM prompt templates and
evaluation in my own research, so understanding what "silent template
drift" means and why version pinning matters was intuitive. No new
libraries needed — the fix uses stdlib `hashlib` and existing `pytest`,
so I didn't need to learn a snapshot testing framework from scratch.
The blast radius is contained to one test file, which makes it low-risk
for a first contribution.

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/natanyanderson/pathreview/commit/a7d77a8aaf2f5b83fcddb48f059f404de31dc2a0

**Reproduction summary:**
Verified in the local checkout that the placeholder
`test_template_snapshot_content_hash` in
`tests/unit/test_prompt_templates.py` cannot detect template drift: it
only asserts that an MD5 hex digest is 32 characters long, which is
always true. Confirmed by editing
`PROMPT_TEMPLATES["skills_feedback"]["v1"]` and re-running the test —
it still passed, proving no protection existed.

**PLAN.md link:** https://github.com/natanyanderson/pathreview/blob/feat/37-prompt-template-snapshots/PLAN.md

**Walkthrough video (recommended):** [skipping — will do office hours if needed]

**Blockers or open questions:** None. PR #301 is already open and passing tests locally.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Fix is fully implemented. Both new tests
(`test_template_content_matches_snapshot` and
`test_every_template_version_has_a_snapshot`) are passing, and the
placeholder `test_template_snapshot_content_hash` has been removed.
All 38 tests in `tests/unit/test_prompt_templates.py` pass locally.
The PR is open at #301 and I'm treating this week as review + polish
rather than new implementation, since sub-tasks 1–5 in PLAN.md are
already complete.

**Next steps:**
Run the full `make check` and `make test-unit` suites, document any
pre-existing failures in the PR description, request peer feedback in
Slack, and address any review comments before the deadline.

**Blockers:**
None right now. Only open question is whether reviewers will want me
to also fix the pre-existing ruff/mypy violations in
`test_prompt_templates.py`. I've left those alone to keep the diff
scoped, but I'll fold them in if requested.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/301

**Branch:** feat/37-prompt-template-snapshots

**What you built:**
Replaced the placeholder `test_template_snapshot_content_hash` in `tests/unit/test_prompt_templates.py` with real per-template SHA-256 snapshots. Added two new pytest tests: `test_template_content_matches_snapshot` fails when a registered template's content changes without a version bump, and `test_every_template_version_has_a_snapshot` catches the reverse case of adding a new template without a registered snapshot. This gives the project actual regression protection against silent prompt drift.

**Tests added or updated:**
Modified `tests/unit/test_prompt_templates.py`. Removed 1 placeholder test, added 2 real snapshot tests plus an `EXPECTED_TEMPLATE_SNAPSHOTS` dict pinning all 5 current template versions. All 38 tests in the file pass locally. Manually verified the snapshot test catches drift by editing `PROMPT_TEMPLATES["skills_feedback"]["v1"]` character-by-character and confirming the test fails with the expected error message, then reverting to confirm it passes again.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

Note on `make check`: the codebase has ~176 pre-existing ruff/mypy violations across many files. `test_prompt_templates.py` specifically had 14 errors on `main` and 13 after my changes — my contribution removed 1 error and introduced 0 new ones.

Note on `make test-unit`: 53 pre-existing test failures across the project on `main` (in files like `test_structural_chunker.py`, `test_tech_detector.py`, `test_review_service.py`). Confirmed the identical 53 failures exist on `main` before my changes via `git stash`. In `tests/unit/test_prompt_templates.py` specifically — the file I modified — all 38 tests pass, including both new snapshot tests. Per the Week 9 "doesn't make things worse" guidance, my contribution introduces 0 new test failures and 0 new lint errors.

**Draft PR feedback received from:** none