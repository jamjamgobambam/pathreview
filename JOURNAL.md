## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/13

**Issue title:** Add a content hash to detect unchanged documents and skip re-embedding

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**

The ingestion pipeline currently reprocesses and re-embeds a README even when the submitted content has not changed. This creates unnecessary embedding work and may result in avoidable API usage. The issue affects the ingestion pipeline and the `IngestedSource` model, which need a reliable way to store and compare a content hash. A successful fix will detect identical content and skip the embedding step while continuing normal processing when the document has changed.

**Selection notes — “Is this issue right for me?” checklist:**

The issue has a defined outcome, identifies the main files involved, and is estimated at 4–6 hours. It requires Python, database-model, ingestion-pipeline, and testing work, which are within my current experience. The scope appears limited to hashing submitted content, recording the hash, comparing it during later ingestion attempts, and verifying the behavior with tests. I understand that a database migration may be needed if the model does not already contain a suitable content-hash field.

**Branch name:** feat/13-content-hash-skip-reembedding

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/AhmadM2409/pathreview/commit/b99efe6

**Reproduction summary:**

I reproduced the issue with a failing unit test that submits the same README twice through the ingestion pipeline. The test showed that both submissions were parsed, chunked, and embedded because the pipeline does not persist ingestion metadata for the duplicate check.

**PLAN.md link:** https://github.com/AhmadM2409/pathreview/blob/feat/13-content-hash-skip-reembedding/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**

I still need to confirm the project’s database transaction convention before deciding whether `_record_ingested_source()` should call `flush()` or `commit()`. I also need to determine which fields should identify a duplicate README so identical content from different repositories or profiles is not skipped incorrectly.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

I implemented full SHA-256 README deduplication in the ingestion pipeline. The pipeline now queries and saves the real `IngestedSource` model, scopes duplicate checks by profile, repository, source type, and content hash, and stores the repository name in `source_url`. The focused ingestion tests now pass with 7 tests covering duplicate skips, changed content, different profiles, different repositories, persisted metadata, byte hashing, and lookup failure handling.

**Next steps:**

Next I need to review the full diff, create logical commits, push the branch, open a draft PR, request peer or mentor feedback, address any agreed feedback, rerun validation, complete Check-in 2, and finalize the PR.

**Blockers:**

There are no blockers specific to Issue #13. `make test-unit` currently reports 53 unrelated failures outside the changed Issue #13 test file, and `make check` currently reports 178 unrelated repository-wide Ruff errors. The changed Issue #13 files pass their focused tests, Ruff, Black, and diff validation.

### Check-in 2 (end of week)

**What I completed:**

I completed the implementation for Issue #13 and opened PR #873. The ingestion pipeline now stores full SHA-256 content hashes and skips parsing, chunking, and embedding when unchanged README content has already been processed for the same profile and repository. I also added focused tests for duplicate content, changed content, different profiles, different repositories, persisted metadata, byte input, and database lookup failures.

**Validation results:**

The 7 focused ingestion pipeline tests pass. Ruff and Black pass on the changed Python files, and `git diff --check` passes. The full repository commands still report unrelated pre-existing failures outside the files changed for Issue #13.

**Feedback received:**

A classmate reviewed the pull request and confirmed that the duplicate lookup is correctly scoped, the skip occurs before unnecessary processing, and the tests cover the important cases. No blocking issues were identified, so no additional code changes were needed.

**Final PR:**

https://github.com/ascherj/pathreview/pull/873

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**

No official maintainer review or requested changes were received before the Week 10 reflection. The pull request remains open and ready for review. A classmate reviewed the implementation during the Week 9 peer-feedback process and did not identify any blocking issues, but no additional maintainer feedback required code changes.

**How you responded:**

No additional code changes were required because no official maintainer feedback was received.

---

### Reflection

**What was harder than you expected?**

The hardest part was understanding how the existing ingestion pipeline, database model, and transaction ownership fit together before making the change. At first, the issue sounded like simply creating a SHA-256 hash and comparing it. The more difficult part was determining where the hash should be persisted, which fields should define the identity of an already-ingested README, and whether the pipeline should commit, flush, or only add the database record. I also had to separate failures caused by my change from existing repository-wide test, Ruff, and mypy failures.

**What did you learn about working in a large codebase?**

I learned that making a small change in a larger codebase requires understanding the surrounding conventions before writing code. In my own projects, I can choose how transactions, models, and tests are structured. In PathReview, I needed to inspect existing service patterns and follow the design already used by the project. I also learned that passing one focused test is not enough by itself. I had to check the broader diff, formatting, linting, transaction behavior, and whether the change could affect other profiles or repositories.

**How did AI tools help — and where did they fall short?**

AI tools were most useful for exploring the repository, tracing the ingestion flow, identifying relevant files, explaining unfamiliar patterns, creating focused tests, and reviewing the final diff. They also helped me break the work into smaller steps instead of trying to implement everything at once. The limitation was that AI could not automatically know which project conventions were correct without inspecting the actual code. I still had to verify transaction ownership, model fields, existing failures, Git state, and the final GitHub PR myself. AI suggestions were useful starting points, but they still needed to be checked against the repository.

**What would you do differently if you started over?**

I would begin with a smaller reproduction test and spend more time tracing the database flow before thinking about the implementation. Early on, I focused on the hashing behavior, but the important design questions were how the ingestion record was stored and how duplicate identity should be scoped. Understanding those pieces earlier would have reduced some back-and-forth and made the implementation more direct.

**What are you most proud of from this module?**

I am most proud that I took an issue from reproduction through planning, implementation, testing, documentation, and a real pull request against an existing project. The final change stayed focused on Issue #13 and included tests for duplicate content, changed content, different profiles, and different repositories instead of only testing the easiest successful case.
