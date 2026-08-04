# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview generates portfolio reviews using versioned prompt templates stored in `rag/generator/prompt_templates.py`. These templates directly shape what the LLM is asked to evaluate (skills, projects, presentation, gaps, and first impression), so even small wording changes can silently affect review quality. The project already has unit tests in `tests/unit/test_prompt_templates.py`, but they only check that templates exist and contain expected placeholders — they do not lock in the full template text. A successful fix would add snapshot-style tests that fail when a template's content changes without an intentional version bump (e.g., editing `v1` instead of adding `v2`), forcing developers to consciously version prompt changes rather than editing them in place.

**Selection notes ("Is this right for me?" checklist):**
- **Tier match:** Tier 1 — labeled "good first issue" with an estimated 3–5 hour effort, appropriate for a first contribution to a large codebase.
- **Scope is bounded:** Primary work is in one existing test file (`tests/unit/test_prompt_templates.py`) with read-only reference to `rag/generator/prompt_templates.py`; no new API routes, frontend work, or database migrations required.
- **I can explain the problem:** Prompt templates are versioned dicts; snapshot tests compare stored hashes or fixture files against live content so accidental edits are caught in CI.
- **Tests are the deliverable:** This is a test-only issue, which fits Week 7's goal of getting oriented without needing to ship production logic yet.
- **Dependencies are minimal:** No OpenRouter API key or live LLM calls needed to implement or run the new tests.
- **Existing starting point:** There is already a placeholder `test_template_snapshot_content_hash` test that computes an MD5 hash but does not assert a fixed expected value — a clear hook to extend.
- **Risk assessment:** Low risk of scope creep; the main design choice is per-template snapshots vs. one combined hash, both well within the issue description.

**Branch name:** `test/37-prompt-template-snapshot-tests`

**Setup confirmation:** [x] App runs locally at localhost:5173

Setup verified by running `make setup` and `make run`; app loads at http://localhost:5173 with backend API at http://localhost:8000.

**Cohort ledger:** [x] Issue added to cohort ledger

---

## Week 7 deliverables checklist

- [x] Issue link and title in JOURNAL.md
- [x] Problem summary in JOURNAL.md (3–5 sentences, own words)
- [x] "Is this right for me?" checklist reasoning in selection notes
- [x] Fork with branch following CONTRIBUTING.md naming convention (`test/37-prompt-template-snapshot-tests`)
- [x] At least one setup commit pushed to fork
- [x] Issue claimed on GitHub (#37)
- [x] Issue added to cohort ledger
- [ ] Branch URL submitted via course portal

**Branch URL for submission:**
https://github.com/sans-2186/pathreview/tree/test/37-prompt-template-snapshot-tests

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/sans-2186/pathreview/commit/ebcece3

**Reproduction summary:**
I confirmed the gap by showing that a one-word edit to `skills_feedback` v1 (e.g. `"Analyze"` → `"Analyse"`) changes the template hash, yet the existing `test_template_snapshot_content_hash` still passes because it only asserts the hash is a 32-character string — not a known expected value. New tests in `tests/unit/test_issue_37_snapshot_reproduction.py` demonstrate this behavior explicitly.

**PLAN.md link:** https://github.com/sans-2186/pathreview/blob/test/37-prompt-template-snapshot-tests/PLAN.md

**Walkthrough video (recommended):** *(not recorded — optional for Slack/office hours feedback)*

**Blockers or open questions:**
- Whether to store expected hashes as Python constants in the test file vs. a JSON fixture in `tests/fixtures/` (leaning toward constants for simplicity).
- Confirm whether a combined all-templates hash is needed in addition to per-template snapshots, or if per-template SHA-256 checks are sufficient.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the full solution from `PLAN.md`: added `EXPECTED_TEMPLATE_HASHES` and `EXPECTED_COMBINED_TEMPLATE_HASH` SHA-256 snapshot constants to `tests/unit/test_prompt_templates.py`, plus three new tests — `test_each_template_matches_snapshot_hash`, `test_snapshot_hashes_cover_every_template_version`, and `test_snapshot_detects_unversioned_content_edit`. Strengthened the existing `test_template_snapshot_content_hash` stub to assert against a fixed expected hash instead of only checking format. All 5 sub-tasks from `PLAN.md` are done. I also manually verified the guardrail works by temporarily editing `rag/generator/prompt_templates.py` (changing one word in `skills_feedback` v1), confirming 3 tests failed with a clear diff, then reverting the change.

**Next steps:**
Run `make check` and `make test-unit`, document any pre-existing failures, remove the now-superseded `tests/unit/test_issue_37_snapshot_reproduction.py` from Week 8, open a draft PR for feedback, then finalize.

**Blockers:**
None — the resolved Week 8 open question was whether to use Python constants vs. a JSON fixture; went with Python constants for simplicity and consistency with existing test style.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/813

**Branch:** `test/37-prompt-template-snapshot-tests`

**What you built:**
Added real snapshot tests for the versioned prompt templates in `rag/generator/prompt_templates.py`. Each `(template_name, version)` pair now has an expected SHA-256 hash; if anyone edits an existing version's text in place, the new tests fail with a message telling them to add a new version key instead of silently changing `v1`. A coverage test also ensures the snapshot dict stays in sync as templates are added or removed.

**Tests added or updated:**
- `tests/unit/test_prompt_templates.py` — added `EXPECTED_TEMPLATE_HASHES`, `EXPECTED_COMBINED_TEMPLATE_HASH`, and 3 new tests; strengthened `test_template_snapshot_content_hash` to assert a real expected value.
- Removed `tests/unit/test_issue_37_snapshot_reproduction.py` (Week 8 reproduction file), which is superseded by the fix and had one assertion that no longer holds now that real snapshots exist.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

*(Pre-existing failures noted: `make check`/ruff reports 361 lint errors and `make test-unit` reports 53 failing tests across unrelated modules — e.g. `test_resume_parser.py`, `test_review_service.py`, `test_skill_extractor.py`, `test_pii_scrubber.py` — all pre-dating this branch and untouched by this PR. Confirmed identical failure lists before and after my changes; this PR introduces zero new lint errors or test failures.)*

**Draft PR feedback received from:** none — PR opened as ready for review at https://github.com/ascherj/pathreview/pull/813; requesting peer/mentor feedback in Slack
