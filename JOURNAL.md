## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The architecture documentation explains that PathReview combines vector-search and keyword-search results during hybrid retrieval, but it does not show how the two scores are mathematically combined. It also omits the default weighting assigned to each retrieval method, making it difficult for contributors to understand or reason about the final ranking. This issue affects `docs/ARCHITECTURE.md`, although the implementation must also be reviewed to ensure the documentation matches the actual retrieval behavior. A successful fix will add the scoring formula, identify the default weights, and include a worked example showing how a final hybrid score is calculated.

**Selection notes — “Is this right for me?” checklist:**
This issue has a clearly defined documentation deliverable and is limited primarily to one file. The necessary information should be available in the hybrid retrieval implementation, so the scope can be verified before making changes. I am comfortable reading Python code and translating implementation details into clear technical documentation. The issue does not require redesigning the retrieval system or changing application behavior, and its estimated effort of two to three hours fits the module timeline.

**Branch name:** docs/36-explain-hybrid-retrieval-scoring

**Setup confirmation:** [yes] App runs locally at localhost:5173

**Cohort ledger:** [ yes] Issue added to cohort ledger

## Week 8 — Reproduction notes

I reproduced the documentation gap by comparing `docs/ARCHITECTURE.md` with the implementation in `rag/retriever/hybrid.py`. The architecture document states that vector and keyword search results are blended, but it does not document the normalization formulas, weighted scoring formula, default weights of 0.7 and 0.3, or the minimum-score filtering behavior implemented by `HybridRetriever`.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [Paste the GitHub link to your reproduction commit]

**Reproduction summary:**
I reproduced the issue by comparing the hybrid retrieval explanation in `docs/ARCHITECTURE.md` with the implementation in `rag/retriever/hybrid.py`, `vector_store.py`, and `keyword_search.py`. The code defines score conversion, normalization, default weights, weighted blending, filtering, and sorting behavior that the architecture document does not currently explain.

**PLAN.md link:** https://github.com/MalikSCole/pathreview/blob/docs/36-explain-hybrid-retrieval-scoring/PLAN.md


**Blockers or open questions:**
I need to ensure that the wording around ChromaDB distance is accurate because the collection uses cosine distance while an implementation comment refers generally to Euclidean distance. I also want to confirm whether the documentation should mention that custom weights are not currently validated to sum to one.
## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I reviewed the hybrid retrieval implementation and added a draft scoring section to `docs/ARCHITECTURE.md`. The section now explains vector-score conversion, per-retriever normalization, the weighted scoring formula, the default 0.7 vector and 0.3 keyword weights, and a worked numerical example.

**Next steps:**
I will compare the documentation against `rag/retriever/hybrid.py`, `vector_store.py`, and `keyword_search.py` one more time, run `make check` and `make test-unit`, open a draft pull request, and request peer or mentor feedback.

**Blockers:**
None currently.

### Check-in 2 (end of week)

PR link: https://github.com/ascherj/pathreview/pull/772

Branch: docs/36-explain-hybrid-retrieval-scoring

What you built:
I expanded docs/ARCHITECTURE.md with an explanation of PathReview’s hybrid retrieval scoring process. The documentation now covers vector-score conversion, score normalization, the weighted formula, default weights, missing retriever scores, score filtering, result ordering, and a worked example.

Tests added or updated:
No test files were added or updated because this was a documentation-only change and did not modify executable behavior. I ran the project’s existing checks and unit tests and recorded the current failures below.

Self-review confirmation: [ ] make check passes [ ] make test-unit passes

Validation note: `make check` and `make test-unit` were run, but both commands failed due to existing lint and unit test failures unrelated to this documentation-only change.

Draft PR feedback received from: [“none”]

## Week 9 — Documentation update and validation

Updated `docs/ARCHITECTURE.md` to explain hybrid retrieval scoring for Issue #36. The new section documents vector distance conversion, per-retriever score normalization, default vector and keyword weights, missing-score handling, minimum-score filtering, max returned chunks, and a worked example.

No tests were added because this PR changes documentation only and does not modify runtime behavior. I ran the existing validation and unit test commands:

- `make check` failed in Ruff lint with 182 existing issues across application and test files, including import ordering, unused imports/variables, line length, FastAPI `Depends`/`File` default warnings, duplicate dictionary key `"Git"` in `agent/tools/skill_extractor.py`, and an undefined `skill_names` reference in `tests/unit/test_skill_extractor.py`.
- `make test-unit` failed with 52 failed tests, 345 passed tests, 31 errors, and 1 warning. Failures/errors were spread across existing unit areas including batch processing, bias detection, faithfulness scoring, keyword search empty-index handling, output parsing, PII scrubbing, prompt defense, README/resume parsing, review service async mocks, security hash handling, skill extraction, tech detection, semantic chunking, and structural chunking.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback arrived during the Summer 2026 contribution period. I still reviewed my own pull request against the issue requirements and compared the documentation change with the implementation before finalizing it.

**How you responded:**
No response was needed because no reviewer feedback was received.

---

### Reflection

**What was harder than you expected?**

The hardest part was making sure my documentation accurately reflected the implementation instead of only repeating what Issue #36 said. I had to trace the hybrid retrieval logic through `rag/retriever/hybrid.py`, `rag/retriever/vector_store.py`, and `rag/retriever/keyword_search.py` to understand how vector scores and BM25 scores were normalized and combined. I also noticed that the vector store is configured for cosine distance while a code comment refers to Euclidean distance, so I had to be careful not to repeat potentially misleading wording in `docs/ARCHITECTURE.md`.

**What did you learn about working in a large codebase?**

I learned that even a small documentation change can depend on several different parts of a large codebase. For Issue #36, the file I actually changed was `docs/ARCHITECTURE.md`, but I had to understand retrieval logic from multiple files before I could document it correctly. This was different from working on my own projects because I had to respect the existing structure, stay within the issue scope, and treat the codebase itself as the source of truth.

**How did AI tools help — and where did they fall short?**

AI tools helped me understand unfamiliar code more quickly and helped me identify the important parts of the scoring process, including the `0.7` vector weight, `0.3` keyword weight, score normalization, filtering threshold, and missing-score behavior. They were also useful for helping me organize my `PLAN.md` and think through edge cases before making the documentation change. However, I still had to verify every technical detail directly in the repository because AI could explain the logic, but it could not replace checking the exact implementation or deciding whether something was actually within the scope of Issue #36.

**What would you do differently if you started over?**

If I started over, I would inspect the relevant implementation files immediately after choosing the issue instead of waiting until the planning stage. Reading `hybrid.py`, `vector_store.py`, and `keyword_search.py` earlier would have made my Week 7 problem summary and Week 8 plan more precise from the beginning. I would also keep short notes while exploring the code so I would not need to revisit the same implementation details when writing `PLAN.md`, the PR description, and the final documentation.

**What are you most proud of from this module?**

I am most proud of completing the entire contribution workflow from issue selection through pull request submission. I claimed Issue #36, created a dedicated branch, set up the repository locally, documented the issue in `JOURNAL.md`, created `PLAN.md`, traced the implementation, updated `docs/ARCHITECTURE.md`, ran the required checks, and opened a pull request to the upstream PathReview repository. The documentation change itself was small, but completing the full workflow gave me experience contributing to a codebase I did not originally build.
