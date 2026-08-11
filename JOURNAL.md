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

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer comments on [PR #813](https://github.com/ascherj/pathreview/pull/813) as of Week 10. This matches the Summer 2026 note that reviewer feedback is not a featured part of the course this term. The PR remains open and ready for review on `ascherj/pathreview`.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
Getting a reliable local environment was harder than the actual issue fix. Docker failed with overlay mount errors and permission denied on `docker.sock`, which blocked `make setup` before I could even look at prompt templates. I also briefly ended up with two copies of the repo (a nested `pathreview/` clone) that diverged from the remote, so `git pull` aborted on uncommitted `JOURNAL.md` changes — more process friction than coding friction. Once the environment was stable, the Week 9 implementation itself was straightforward; the surprise was how much of Module 3 time went into tooling, git hygiene, and documenting pre-existing test/lint failures rather than writing new assertions.

**What did you learn about working in a large codebase?**
In your own project you often know why every file exists. Here I had to treat `docs/CONTRIBUTING.md`, `PLAN.md`, and existing tests as the map — especially matching patterns in `tests/unit/test_prompt_templates.py` instead of inventing a new testing style. Contributing also means respecting scope: issue #37 was test-only, so I left `rag/generator/prompt_templates.py` untouched even though editing production code would have been tempting. Another lesson was that “green CI” is not always realistic on day one — the suite already had dozens of unrelated failures, so the bar became “don’t make things worse,” which I verified by diffing pass/fail lists before and after my change.

**How did AI tools help — and where did they fall short?**
AI helped most for orientation and scaffolding: summarizing the issue, drafting `PLAN.md` / journal sections, proposing snapshot-hash constants, and walking through CONTRIBUTING conventions. It also helped diagnose environment errors (Docker overlay vs. missing Postgres). It fell short when details had to be exact — for example, an early draft of expected hashes was truncated by one character and only a programmatic verify script caught it. AI also couldn’t open the cross-fork PR against `ascherj/pathreview` correctly from this environment (it created a fork-internal PR first), so I still had to create the real upstream PR in the GitHub UI. The useful pattern was: AI drafts → I run tests and verify hashes/diffs myself before committing.

**What would you do differently if you started over?**
I’d lock environment setup on Day 1 (one clone path, Docker Desktop or native Postgres decided early, no nested repos) before writing any journal content. I’d also open the draft PR earlier in Week 9 instead of near the end, so peer feedback could land before Check-in 2. On the technical side, I’d decide “constants vs. JSON fixture” in Week 8 and stick with it immediately — we already leaned toward constants, and delaying that choice didn’t buy much. Finally, I’d keep Week 8 reproduction tests in a form that can coexist with the fix (or mark them clearly temporary) so I wouldn’t have to delete a file whose assertions intentionally broke once snapshots existed.

**What are you most proud of from this module?**
I’m most proud of proving the gap before fixing it: the Week 8 reproduction showed that a one-word template edit changed the hash but still passed the stub snapshot test, and Week 9 closed that loop with real expected SHA-256 values plus a regression test that simulates the same edit. Watching the new tests fail on a temporary `"Analyze"` → `"Analyse"` mutation, then pass again after revert, made the contribution feel concrete — not just “added some asserts,” but a guardrail that behaves the way the issue described.
