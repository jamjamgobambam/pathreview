## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

Why? Because this is my first time, this was an issue I could be challenged yet understand by doing some deep diving. With the Scope of the project, I definitely need to focus on tier 1 issues.

**Problem summary:**
A bug is in the orchestrator.py file. Before running tools, it creates it's own session id from a user profile. So if the smae profile is reviewed again, the orchestrator starts from whatever session data was already stored for that profile instead of clearing it first. So although the new review creates a new session, the agent will still reuse the old per-profile session state unless that state is cleared.

To fix that, I would need to make sure the orchestrator will use the new session id instead to remove that stale tool. 

**Branch name:** fix/43-agent-session-state-not-cleared

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue](https://github.com/Dani-risingBW/pathreview/commit/097b846a6f9928107e49848e8693a38695bca6a9)

**Reproduction summary:**
Ran a curl command to call POST/ reviews twice with the same profile_id. The second review reuses the same old state unless that state is cleared first. It returns the same message and response.

I also started a review of the same user but with two different resumes and the results were the exact same. They aren't supposed to be but with the agent reusing stale data it turns to be the same. 

**PLAN.md link:** [See the plan](PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
None


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented everything but testing and adding edge cases. 

**Next steps:**
Testing, finding edge cases, and opening a PR. 

**Blockers:**
I didn't know about the pre-existing failures in make check before it was mentioned in the assignment. I definitely need to read everything before doing everything. But I will work on cleaning up at the end of the week.

---

### Check-in 2 (end of week)

**PR link:** [[(https://github.com/ascherj/pathreview/pull/562)](https://github.com/ascherj/pathreview/pull/562)]

**Branch:** [fix/43-agent-session-state-not-cleared]

**What you built:**
I updated the orchestrator/session-store flow so repeated reviews for the same profile do not reuse stale session state from an earlier run. I also fixed the review generation path so the uploaded document actually changes the final feedback instead of producing the same canned output every time. I added repeated-review and dynamic-review edge cases to the plan and cleaned up the session-store typing so the touched files pass the focused pre-commit checks.

**Tests added or updated:**
`tests/unit/test_orchestrator.py` was added to cover the review orchestration path and the session-state behavior around repeated reviews. `tests/unit/test_review_service_ingestion.py` covers the `IngestedSource` fix, and `tests/unit/test_review_generation_dynamic.py` verifies that different uploads now produce different review output. I also updated the session-store typing in `agent/memory/session_store.py` and the mypy hook scope in `.pre-commit-config.yaml` so the touched files can be validated cleanly.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

I ran focused pre-commit checks on the touched files and they passed. I also ran `make check`, and it failed on pre-existing repo-wide lint issues in unrelated files (for example `api/routes/profiles.py`, `api/routes/reviews.py`, `ingestion/chunking/semantic_chunker.py`, `ingestion/chunking/strategy_selector.py`, `ingestion/chunking/structural_chunker.py`, `ingestion/embeddings/provider.py`, `ingestion/parsers/resume_parser.py`, `rag/generator/output_parser.py`, `rag/retriever/hybrid.py`, `safety/monitoring.py`, `safety/pii_scrubber.py`, and multiple unit tests). The failures were B008, B904, B007, SIM116, F841, E501, N806, and related style/type errors that do not come from this branch.

The branch now includes three focused commits after the base session-state fix: one for the invalid `raw_data` ingestion argument, one for the dynamic review-output behavior, and one for the journal/plan documentation updates.

**Draft PR feedback received from:** ["none"]

**Notes for reviewers:**
Pre-existing failures observed in `make check` and `pre-commit run --all-files`: repo-wide lint and type errors in unrelated files, including B008/B904 in API routes, B007/SIM116/F841/E501/N806 in ingestion, safety, and test files, and hundreds of unrelated mypy errors across the codebase. This PR does not touch those unrelated files, and the changes here do not affect those failures.