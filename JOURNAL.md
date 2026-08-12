## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/109

**Issue title:** Test coverage for `core/services/review_service.py` is below 40%

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The review service orchestrates the full review workflow and is the most critical service in the application, but most of its code paths are untested. Add unit tests targeting the major execution paths including success, partial failure, and full failure cases.

Relevant files:

tests/unit/test_review_service.py



**Branch name:** test/109-test-coverage-service

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Gabbykoms/pathreview/commit/e45b300

**Reproduction summary:**
Ran `.venv/bin/pytest tests/unit/test_review_service.py --cov=core.services.review_service --cov-report=term-missing` against the current `test/109-test-coverage-service` branch. Measured coverage on `core/services/review_service.py` is **22%** (135 statements, 105 missed) — even lower than the "below 40%" the issue reports. The uncovered ranges (`98–194`, `202–279`, `288`, `323`, `369–390`) confirm that `process_review` and all four internal helpers are entirely untested. A secondary finding: **13 of the 19 pre-existing tests fail** with `AttributeError: 'coroutine' object has no attribute 'all'` because the existing scaffolding uses `AsyncMock` where SQLAlchemy 2.0's sync `result.scalars()` chain requires `MagicMock`. The full coverage report is included in the reproduction commit.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):** <!-- optional Loom link -->

**Blockers or open questions:**
- The `chromadb/chroma:0.4.22` image pinned in `docker-compose.yml` fails to boot against NumPy 2.0 (`np.float_` removed). Doesn't block this issue since `review_service.py` doesn't touch the vector store, but it will need bumping before end-to-end runs.
- Whether to fix the pre-existing broken tests as part of this PR or in a separate one — currently planned to fix them in-place because otherwise the coverage numbers stay wrong.
- `_run_agent_orchestration` and `_run_rag_retrieval_generation` are placeholder stubs; if real implementations land before this PR merges, the helper-level tests (step 4 of PLAN.md) will need to be revisited.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Steps 1 and 2 of PLAN.md are done. Replaced `AsyncMock` with `MagicMock` on the `.scalars()` chain across the 13 broken pre-existing tests — they're all green now, and coverage on `core/services/review_service.py` has risen from 22% into the mid-30s just from unblocking measurement. Added the `_exec_result` helper and the `mock_profile_full` / `mock_profile_empty` fixtures inside `TestReviewService` so the new `process_review` tests don't have to re-mock the SQLAlchemy `Result` chain each time.

**Next steps:**
Steps 3 and 4 — the ~14 new tests. Working through the eight `process_review` branches first (success, review-not-found, profile-not-found, safety-fail, partial ingestion failure, unexpected mid-pipeline exception, exception during recovery-write, single-source profile), then the six helper-direct tests. Then `make check` and open the PR.

**Blockers:**
None. Pre-commit mypy is complaining on imported source modules when I stage test-only changes (unrelated pre-existing errors surfacing via imports); planning a one-line `.pre-commit-config.yaml` fix to align its scope with the Makefile's `typecheck` target so test-only PRs aren't blocked by unrelated failures.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1005

**Branch:** `test/109-test-coverage-service`

**What you built:**
Raised unit-test coverage on `core/services/review_service.py` from **22% → 93%** with a tests-only diff. Repaired 13 pre-existing broken tests (async/sync mock mismatch on SQLAlchemy 2.0's `Result.scalars()` chain) and added 14 new tests covering the eight `process_review` branches and the four module-level pipeline helpers.

**Tests added or updated:**
- `tests/unit/test_review_service.py` — 518 insertions, 198 deletions; 35 tests passing, 0 failing. Repaired the existing `create_review` / `get_review` / `list_reviews` tests and added the `process_review` branch tests plus direct-helper tests for `_run_ingestion_pipeline`, `_run_agent_orchestration`, `_run_rag_retrieval_generation`, and `_run_safety_checks`. Uncovered 7% is trivial log-only `except` branches, flagged in the PR body.
- `.pre-commit-config.yaml` — one-line change to exclude non-source dirs from the pre-commit mypy hook, matching the Makefile's `typecheck` scope. Unblocks test-only PRs from failing on unrelated pre-existing errors in strictly-typed source modules.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none — Su26 does not include peer/reviewer feedback per course notes.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback arrived. Per the Summer 2026 course note, reviewer feedback is not a feature this term, so this is expected rather than a gap in the PR itself.

**How you responded:**
N/A — no feedback to respond to. The PR remains open on the working branch (`test/109-test-coverage-service`) at the state described in Week 9's Check-in 2, with `make check` and `make test-unit` both passing and coverage on `core/services/review_service.py` at 93%.

---

### Reflection

**What was harder than you expected?**
The async-vs-sync mock split in SQLAlchemy 2.0 was more subtle than I expected going in. I assumed "async ORM = everything is `AsyncMock`" and hit the exact `'coroutine' object has no attribute 'all'` error the pre-existing tests were already throwing. The fix — `db.execute` stays `AsyncMock` but the `.scalars().first()` chain is sync `MagicMock` — is one line to describe but took real reading of the SQLAlchemy `Result` internals to justify. The other surprise was sequenced mocks: `process_review` calls `db.execute → scalars → first` up to three times per test, and ordering the `side_effect` list by which line executes first (review lookup vs. profile lookup vs. exception-handler re-fetch) is fragile in a way that produces silent wrong-value errors rather than clean failures.

**What did you learn about working in a large codebase?**
The scope discipline is the whole game. I found a real bug in `list_reviews` (total count computed via `len(count_result.scalars().all())` on the *unpaginated* query — will silently return wrong totals as soon as pagination matters) while writing coverage tests, and my instinct was to fix it in the same PR. PLAN.md forced me to leave it flagged with a TODO and open a separate issue instead. In my own projects I'd have bundled the fix; here, doing so would have muddied a test-only PR with an unrelated source change, made the diff harder to review, and coupled my "coverage above 80%" deliverable to a design discussion that wasn't mine to have. Similarly, the ChromaDB/NumPy 2.0 boot failure I noted in Week 8 stayed noted, not fixed. Contributing to production code is as much about what you *don't* touch as what you do.

**How did AI tools help — and where did they fall short?**
Most useful: scaffolding the ~14 new test cases from the PLAN.md branch list, generating the `_exec_result` helper, and translating "this uncovered line range does X" into a matching test structure. That work was pattern-heavy and mechanical, which is where AI is strongest. Where it fell short: diagnosing the `AttributeError: 'coroutine' object has no attribute 'all'` failures in the pre-existing tests. AI kept suggesting "make it more async" (wrap in `await`, add another `AsyncMock` layer) which is the *opposite* of the actual fix. Understanding *why* `scalars()` is sync required reading SQLAlchemy source, and no amount of prompting produced that insight — I had to go find it. AI also couldn't help me judge scope calls (fix the `list_reviews` bug now vs. later); those needed the PLAN.md discipline and a read of the project's contribution norms.

**What would you do differently if you started over?**
I'd reproduce coverage numbers *before* writing PLAN.md, not after. In Week 7 I picked the issue based on the "<40%" claim in the issue body; the actual measured coverage turned out to be 22%, and 13 of the 19 existing tests were broken. That reframed the work — I was fixing broken infrastructure and adding coverage, not just adding coverage — and I'd rather have known that going into planning. I'd also have opened the draft PR earlier in Week 9 rather than late; even without peer review in Su26, the act of writing the PR description would have forced me to justify the `list_reviews` scope-out earlier and cleaner.

**What are you most proud of from this module?**
Not touching production code. Coverage went from 22% to 93% and I found a real bug on the way, but the diff is tests-only. Given how tempting it was to "just fix" the `list_reviews` count issue while I was in the file, I'm proud that I filed it as a follow-up and shipped a PR that does exactly one thing.
