## Week 7 — Issue selection

**Issue link:** [[paste link here]](https://github.com/ascherj/pathreview/issues/88)

**Issue title:** POST /reviews endpoint has no test for when the profile has no ingested documents #88

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The /reviews endpoint currently assumes a profile will already have some documents ingested before a review is requested, and that assumption is never checked in the test suite. If someone triggers a review for a profile that exists but hasn't had anything ingested yet, it's unclear whether the endpoint fails gracefully or throws an unhandled exception, since no test exists to pin down the expected behavior. This is a gap in edge-case coverage rather than a confirmed bug — the fix is really about writing a regression test that calls the endpoint under this specific condition and asserts a clean, well-formed error response (e.g. a 4xx with a descriptive message) instead of a server crash. A successful fix gives the team confidence that this edge case is handled predictably and prevents future changes from silently reintroducing a crash for profiles with no ingested content.

**Branch name:** test/88-review-endpoint-test

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

**Reproduction steps:**

Root cause traced to `process_review()` in [core/services/review_service.py:82](core/services/review_service.py#L82). `POST /reviews` ([api/routes/reviews.py:22](api/routes/reviews.py#L22)) never checks for ingested documents — it creates the review with `status="pending"` and hands the real work to a background task. Inside that task, `_run_ingestion_pipeline()` ([core/services/review_service.py:197](core/services/review_service.py#L197)) correctly returns `[]` when a profile has no `github_username`, `portfolio_url`, or `resume_text`. But `_run_agent_orchestration()` ([:282](core/services/review_service.py#L282)) and `_run_rag_retrieval_generation()` ([:307](core/services/review_service.py#L307)) are hardcoded placeholders that ignore the (empty) ingestion results entirely, and `_run_safety_checks()` ([:357](core/services/review_service.py#L357)) only validates shape, not provenance. Net effect: **no crash, no 4xx** — a documentless profile silently reaches `status="complete"` with fabricated feedback.

Steps to reproduce against a local server (`make run`, API at `localhost:8000`):

1. Register a fresh user:
   ```bash
   curl -s -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "empty-profile-test@example.com", "password": "testpass123"}'
   ```
   Extract `access_token` as `$TOKEN`.

2. Create a profile with no fields set (all optional per `ProfileCreate`):
   ```bash
   curl -s -X POST http://localhost:8000/profiles -H "Authorization: Bearer $TOKEN"
   ```
   Confirmed profile `349cc633-fc7a-4178-9207-7283dab27943` created with `github_username`, `portfolio_url`, `resume_text` all null and zero `ingested_sources` rows.

3. Trigger a review for that profile:
   ```bash
   curl -s -X POST http://localhost:8000/reviews \
     -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"profile_id": "349cc633-fc7a-4178-9207-7283dab27943"}'
   ```
   Returns `201` with `status: "pending"`, review id `72a8a928-ed09-43be-879e-128bc03e142f`.

4. Poll the review after the background task runs:
   ```bash
   curl -s http://localhost:8000/reviews/72a8a928-ed09-43be-879e-128bc03e142f -H "Authorization: Bearer $TOKEN"
   ```
   **Actual result:** `status: "complete"`, `overall_score: 0.81`, `error_message: null`, and three fully-populated feedback sections ("Technical Skills", "Project Experience", "Career Growth") — none of which reflect real analysis, since nothing was ever ingested.

**Expected behavior (not yet implemented):** the review should end in `status="failed"` with a descriptive `error_message` (the column already exists on `Review` but is never set on this path), rather than fabricating a successful result. No test currently exists for this path (`process_review`, `_run_ingestion_pipeline`, and this scenario are entirely uncovered in `tests/unit/test_review_service.py`).

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [962e503](https://github.com/asnts18/pathreview/commit/962e503)

**Reproduction summary:**
Created a fresh user, then a profile with no `github_username`, `portfolio_url`, or `resume_text` set, then triggered `POST /reviews` against it. The review reached `status: "complete"` with a fabricated `overall_score: 0.81` and three canned feedback sections, instead of failing — confirming that `process_review()` never checks whether ingestion actually produced anything before generating feedback.

**PLAN.md link:** [PLAN.md](https://github.com/asnts18/pathreview/blob/test/88-review-endpoint-test/PLAN.md)

**Blockers or open questions:**
Still deciding whether "no documents ingested" should be judged from the profile's own fields (`github_username`/`portfolio_url`/`resume_text`) or from the `ingested_sources` table directly — these should normally agree, but could diverge if a profile has stale `IngestedSource` rows from a prior partial run. See Risks & unknowns in `PLAN.md` for details.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from `PLAN.md` step 1: `process_review()` in `core/services/review_service.py` now checks whether `_run_ingestion_pipeline()` returned any results, and if not, sets `status="failed"` with a descriptive `error_message` instead of continuing on to the placeholder agent/RAG/safety steps. Also completed step 2 — confirmed `error_message` is already exposed on `ReviewResponse` for `GET /reviews/{id}`, and added it to the lighter `GET /reviews/{id}/status` payload too, since that's the endpoint clients poll while a review is processing. Wrote both regression tests from steps 3–4 in `tests/unit/test_review_service.py`: one asserting a documentless profile ends in `status="failed"` with a non-null `error_message`, and a companion happy-path test asserting a profile with at least one source still reaches `status="complete"`. Re-ran the original curl reproduction from Week 8 against a live local server (Postgres via `docker compose up -d`) — confirmed the same profile shape now returns `status: "failed"` with the descriptive message on both endpoints, and confirmed a profile with `github_username` set is unaffected and still completes normally.

Resolved the open question from Week 8: went with checking `_run_ingestion_pipeline()`'s return value (the profile's own fields) rather than querying `ingested_sources` directly, since that function is the sole writer of those rows and is already re-run fresh on every `process_review()` call.

Verified no regressions: `make test-unit` still shows the same 53 pre-existing failures (all pre-existing mock-configuration bugs in unrelated test files) plus 377 passing (up from 375 — the 2 new tests). `make lint` (182 errors) and `make typecheck` (103 errors) are both unchanged from the pre-existing baseline I recorded before starting.

**Next steps:**
Finish filling out the PR template, double-check branch name and commit messages against `docs/CONTRIBUTING.md` conventions, and open the PR.

**Blockers:**
None.

### Check-in 2 (end of week)

**PR link:** [#707](https://github.com/ascherj/pathreview/pull/707)

**Branch:** `test/88-review-endpoint-test`

**What you built:** `process_review()` now checks whether the ingestion pipeline actually produced any sources for a profile, and if not, sets the review to `status="failed"` with a descriptive `error_message` instead of letting the (hardcoded, placeholder) agent/RAG generation steps fabricate a fake "complete" review. The failure reason is also surfaced on the lightweight `/reviews/{id}/status` polling endpoint, not just the full review fetch.

**Tests added or updated:** `tests/unit/test_review_service.py` — added `TestProcessReviewNoIngestedDocuments` with two tests: one confirms a profile with no `github_username`/`portfolio_url`/`resume_text` ends in `status="failed"` with a non-null `error_message`; the other confirms a profile with at least one source (e.g. `github_username` set) still reaches `status="complete"`, guarding against the new check rejecting valid profiles.

**Self-review confirmation:**
- [x] `make check` passes — with caveats: 182 pre-existing lint errors and 103 pre-existing mypy errors in the repo, confirmed identical in count and content before and after this change (verified via `git stash` diff on the touched files). No new lint or type errors introduced by this fix.
- [x] `make test-unit` passes — with caveats: 53 pre-existing test failures in unrelated files (mock-configuration bugs), unchanged by this change. 377 tests pass (up from 375 baseline — the 2 new tests added here, both green).

**Draft PR feedback received from:** none.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
Reviewer feedback is not a feature in Summer 2026.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
Figuring out what the bug actually *was* took longer than fixing it. Issue #88 was filed as a missing-test-coverage gap, so I expected the endpoint to either 500 or return a clean 4xx once I poked at it — instead, tracing the async flow from `POST /reviews` into the `process_review()` background task revealed there was no error path at all. A documentless profile sailed through to `status="complete"` with confident, fabricated feedback sections, because the agent/RAG steps are still hardcoded placeholders that ignore their inputs. That's a much sneakier failure mode than a crash, and I wouldn't have caught it without actually reproducing it end-to-end with curl rather than just reading the code. The other surprise was hitting a hard wall on `git commit`: this repo's mypy pre-commit hook has no baseline mode, so it fails on any pre-existing type error in a file I touched, whether or not I caused it. I hadn't budgeted time for a tooling problem that had nothing to do with my actual fix.

**What did you learn about working in a large codebase?**
The biggest shift was learning to tell "my change broke this" apart from "this was already broken," and proving it instead of assuming it. I ran `make check` and `make test-unit` before touching anything specifically so I'd have a baseline to diff against later — without that, I couldn't have confidently said the 53 failing tests and 182 lint errors were pre-existing rather than something I introduced. I also learned to resist the urge to clean up what I saw along the way. It would have been easy to "fix" the unsorted imports or add type annotations while I was in `review_service.py`, but that inflates the diff and makes the actual change harder to review. Scoping the fix to exactly one `if not ingestion_results:` block, and pushing back on my own instinct to auto-format the whole file, felt like the real skill being tested here.

**How did AI tools help — and where did they fall short?**
AI was strongest at the mechanical tracing work — following the call chain from the route handler through the background task through each placeholder helper function, and spotting that `_run_agent_orchestration()` and `_run_rag_retrieval_generation()` silently ignore their `ingestion_results` argument. That's the kind of thing that's easy to miss skimming and tedious to verify by hand across five files. It also made the reproduction loop fast — spinning up Docker, registering a user, creating an empty profile, and curling the review into existence, all scripted rather than clicked through manually. Where it fell short was exactly the judgment calls: whether "no documents" should be judged from the profile's own fields or the `ingested_sources` table, whether to bypass the pre-commit hook with `--no-verify`, how strict to be about the checkboxes in the PR template given the pre-existing failures. Those needed an actual decision from me, not just information — the AI could lay out the tradeoffs clearly, but I had to be the one to pick.

**What would you do differently if you started over?**
I'd check the repo's pre-commit config before writing any code, not after trying to commit. Knowing upfront that mypy has no baseline mode would have changed how I planned my time — I'd have either budgeted for the `--no-verify` conversation earlier or picked a smaller, more isolated file to touch. I'd also push back sooner on my own default of committing frequently; bundling the fix and its tests into one commit up front would have meant hitting the hook wall once instead of losing time re-doing the same edit after `git checkout` accidentally reverted more than I meant it to.

**What are you most proud of from this module?**
The reproduction, not the fix. Anyone can read `process_review()` and guess it might not handle an empty profile well — proving it, live, with a real curl request against a real running server, and getting back an actual fabricated `overall_score: 0.81` for a profile with zero ingested documents, is what turned "this looks like a gap" into "this is definitely broken, and here's exactly what it does instead." That evidence is what made the fix itself almost mechanical.