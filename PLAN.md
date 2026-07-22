## Solution plan

**Issue:** [POST /reviews endpoint has no test for when the profile has no ingested documents #88](https://github.com/ascherj/pathreview/issues/88)

### Understand

**Expected behavior:** Requesting a review for a profile that has no ingested documents (no GitHub username, portfolio URL, or resume) should fail in a clean, well-formed way — e.g. `status="failed"` with a descriptive `error_message` — so the client can tell the user to add content before requesting a review.

**Actual behavior (confirmed via reproduction, see `JOURNAL.md`):** No such check exists anywhere in the pipeline. `POST /reviews` ([api/routes/reviews.py:22](api/routes/reviews.py#L22)) creates the review with `status="pending"` and hands processing to a background task, `process_review()` ([core/services/review_service.py:82](core/services/review_service.py#L82)). Inside that task, `_run_ingestion_pipeline()` correctly returns `[]` for a documentless profile, but the downstream placeholder steps — `_run_agent_orchestration()` and `_run_rag_retrieval_generation()` — ignore the (empty) ingestion results and always return hardcoded, canned sections and a fixed `overall_score`. `_run_safety_checks()` only validates structural shape, not whether the content reflects real input. Net result: the review silently reaches `status="complete"` with fabricated feedback instead of failing — no crash, no error, nothing to catch the case. Root cause is a missing guard: nothing in `process_review()` checks "did ingestion actually produce anything?" before proceeding to generate feedback.

### Map

- [core/services/review_service.py](core/services/review_service.py) — `process_review()` (orchestration/guard logic goes here, right after the ingestion step); `_run_ingestion_pipeline()` (already returns the empty-list signal we need, no change expected)
- [tests/unit/test_review_service.py](tests/unit/test_review_service.py) — currently has zero coverage of `process_review()`; needs new tests for both the no-documents-fails case and the happy path (has documents → proceeds normally)
- [core/models/review.py](core/models/review.py) — no schema change needed; `error_message: Mapped[str | None]` already exists on `Review` and is simply unused today
- [api/schemas/review.py](api/schemas/review.py) — `ReviewResponse` — verify `error_message` is already exposed in the response model (likely yes, since the reproduction curl output included `"error_message":null`)
- [JOURNAL.md](JOURNAL.md) — already updated with reproduction steps in a prior commit; may want a short "resolved" follow-up note once the fix lands

### Plan

1. **Add the guard in `process_review()`** — right after `_run_ingestion_pipeline()` returns, check if `ingestion_results` is empty. If so, set `review.status = "failed"`, `review.error_message = "No documents have been ingested for this profile. Add a GitHub username, portfolio URL, or resume before requesting a review."`, commit, log a warning, and `return` early — skipping agent orchestration, RAG generation, and safety checks entirely.
2. **Confirm `error_message` is wired through the API layer** — check `ReviewResponse` in `api/schemas/review.py` and the `GET /reviews/{id}` / `GET /reviews/{id}/status` handlers so the failure reason is actually visible to the client, not just stored in the DB.
3. **Write the regression test that pins down current (broken) behavior first** — a test calling `process_review()` with a mocked profile that has `github_username=None`, `portfolio_url=None`, `resume_text=None`, asserting `status == "failed"` and `error_message` is set. This should fail before the fix and pass after.
4. **Write a companion happy-path test** — same test shape but with e.g. `github_username` set, asserting the review still reaches `status == "complete"` with sections populated, to guard against the new check being overly aggressive and blocking valid reviews.
5. **Run the full unit suite (`make test-unit`) and manually re-run the curl reproduction from `JOURNAL.md`** against the local server to confirm the same profile (`349cc633-fc7a-4178-9207-7283dab27943`) now returns `status: "failed"` with a descriptive message instead of fabricated `status: "complete"` content.

### Inputs & outputs

**Input:** A `profile_id` passed to `process_review()`, resolving to a `Profile` row whose `github_username`, `portfolio_url`, and `resume_text` are all unset (and consequently zero `IngestedSource` rows created for it).

**Output:** The corresponding `Review` row updated to `status="failed"` with a non-null, descriptive `error_message`, and `sections`/`overall_score` left as `null` — instead of the current fabricated `status="complete"` result. No change to the synchronous `POST /reviews` response shape (still `202`/`pending` immediately); the change is entirely in what the background task produces.

### Risks & unknowns

- **Source of truth for "no documents":** the guard as planned checks the return value of `_run_ingestion_pipeline()` (the profile's own fields), not the `ingested_sources` table directly. These should currently be equivalent since that function is the only writer of `IngestedSource` rows, but if a profile could have stale/orphaned `IngestedSource` rows from a previous partial run while its current fields are empty, checking the function's return value vs. querying the table could disagree. Need to confirm which is the intended source of truth before finalizing.
- **Overly broad failure condition:** need to make sure the check doesn't also reject profiles that have *some* content that legitimately produces zero ingestable sources (e.g. a malformed but non-empty resume) — that's a different failure mode (ingestion error) than "nothing was submitted at all," and conflating them could produce a misleading error message.
- **Existing consumers of `status="complete"`:** unclear if the frontend or any other code currently assumes every triggered review eventually reaches `"complete"` and doesn't yet handle `"failed"` gracefully in the UI — worth a quick check of `frontend/` before considering this done end-to-end, though that's outside the scope of the backend fix itself.
- **No existing test scaffolding for `process_review()`:** since this function isn't tested at all today, mocking its two sequential `db.execute()` calls (for `Review` then `Profile`) correctly will take some care to avoid a brittle test that breaks on unrelated refactors.

### Edge cases

- Profile with all three fields (`github_username`, `portfolio_url`, `resume_text`) unset — the primary case from issue #88; should fail cleanly.
- Profile with fields set but pointing to unreachable/invalid sources (e.g. a GitHub username that doesn't exist) — currently `_run_ingestion_pipeline()` catches exceptions per-source and continues, meaning `ingestion_results` could still end up empty here too; confirm this should also route to the new "no documents" failure path.
- Profile that has at least one valid source — must still reach `status="complete"` as before (guarded against via the happy-path test).
- Review for a profile that gets deleted between creation and background processing — already handled by the existing `if not profile` branch; not in scope for this fix but worth confirming it isn't accidentally broken by the new guard's placement.
