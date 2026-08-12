## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/149

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**

The structural chunker doesn't handle documents that don't contain Markdown headings. Instead of creating at least one chunk, it returns an empty list, so those documents are skipped, and they never make it into the RAG index. This affects the ingestion pipeline because plain text documents cannot be processed correctly.

A successful fix would make sure documents without headings still get chunked, such as by treating the whole document as a single chunk or using a fallback approach.

**Branch name:** fix/149-structural-chunker-no-headings

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/goodCodeForGood/pathreview/commit/<reproduction-commit>

**Reproduction summary:**

I reproduced the issue by running the structural chunker against a Markdown document containing only plain text and no Markdown headings. The chunker returned an empty list instead of generating a fallback chunk, causing the document to be skipped by the ingestion pipeline.

**PLAN.md link:** https://github.com/goodCodeForGood/pathreview/blob/fix/149-structural-chunker-no-headings/PLAN.md

**Blockers or open questions:**

I still need to verify whether the fallback chunk should include the same metadata as heading-based chunks and whether any downstream components rely on heading information.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the structural chunker fix for documents without Markdown headings. Updated the structural chunker tests to verify heading-less documents, heading paths, metadata, nested headings, and other section-handling behavior. I also addressed the necessary type annotations and linting issues in the chunking code and tests.

**Next steps:**
Run the full project checks, review the final diff, commit and push the changes, and open the PR for review. I will also complete the final self-review and document the test results.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/266

**Branch:** `fix/149-structural-chunker-no-headings`

**What you built:**
Fixed the structural chunker so documents without Markdown headings are handled correctly instead of producing no usable chunks. The implementation preserves the expected chunk metadata while continuing to support heading-based structure and nested heading paths.

**Tests added or updated:**
Updated `tests/unit/test_structural_chunker.py` with coverage for heading-less documents, whitespace-only input, nested headings, heading paths and breadcrumbs, heading levels, metadata preservation, large sections, multiple H1 headings, and empty sections. The structural chunker test suite passes with **15/15 tests passing**.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes

Pre-existing failures were observed in the broader chunk-related unit test run for BatchEmbeddingProcessor and FaithfulnessChecker. These failures are unrelated to the structural chunker changes. The structural chunker tests pass, and make check and make test-unit pass.

**Draft PR feedback received from:** None as of now

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback received yet.

**How you responded:** N/A

---

### Reflection

**What was harder than you expected?**

The hardest part was figuring out which failures were actually caused by my changes. My structural chunker tests passed, but broader test commands showed failures in the batch embedding processor and faithfulness checker that were unrelated to my issue. At first, it was easy to assume that every failure meant something in my branch was broken. I had to learn to trace failures back to the specific files and understand the difference between a regression I introduced and a pre-existing problem in the codebase.

I also found the project's type-checking and linting requirements more involved than expected. Fixing the structural chunker itself was only part of the work; I also had to add type annotations, resolve mypy errors, and clean up issues that Ruff and Black identified, which I did not expect to fix in the first place, and took longer than I estimated.

**What did you learn about working in a large codebase?**

I learned that working in an existing codebase requires much more careful scope management than working on a project I built myself. A test command can fail for several unrelated reasons, so I cannot assume that every failure belongs to the issue I am working on. I also learned to use the existing tests, type checker, linter, and project commands as part of understanding the project's expectations rather than treating them as checks to run only at the end.

The structural chunker issue also showed me the importance of understanding edge cases. The original issue involved documents without headings, which seems like a small case, but handling it correctly required understanding how sections, heading paths, heading levels, metadata, and chunks fit together.

**How did AI tools help — and where did they fall short?**

AI was most useful for helping me interpret error messages, understand what mypy and Ruff were asking for, and work through the next debugging step when I was unsure what a failure meant. It was also useful for helping me differentiate between failures in my structural chunker work and other unrelated failures in the repository.

However, AI could not replace actually running the project commands and checking the repository state. Some of the failures looked relevant at first but were pre-existing issues in other parts of the codebase. I had to verify the results myself and make decisions based on the actual test output. This taught me to use AI as a debugging and reasoning aid rather than treating its suggestions as automatically correct.

**What would you do differently if you started over?**

I would establish a clearer baseline at the beginning of the work. I would run the required project-wide checks before making changes, record the failures, and then use that baseline when evaluating whether my changes introduced anything new. That would save time and prevent confusion related to failures caused by unrelated issues. I would also spend more time understanding the project's contribution and testing conventions before making implementation changes.

Additionally, I would keep the scope of my changes tighter from the beginning. When type checking and linting showed issues in related files, it was important to distinguish the changes necessary for my work from unrelated cleanup. Starting with that mindset would make the review history easier to understand and more efficient and faster to complete.

**What are you most proud of from this module?**

I am most proud of learning how to contribute to an existing codebase without treating the repository as if it were my own project. I started with a specific structural chunker issue, added and updated tests for the behavior, worked through type-checking and linting requirements, investigated broader test failures, and ultimately got the required checks passing and opened a PR. The biggest accomplishment for me was not just making the test pass, but learning how to verify that my changes were actually the cause of the behavior I was fixing, ensuring the code passed all the test cases and lint checks, and that I was not making unrelated parts of the project worse. It was a great hands-on experience, and I learned a lot while navigating this open source project contribution. Thank you CodePath for this interesting project! :)
