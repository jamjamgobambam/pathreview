# Module 3 Journal — Addree Barua

## Week 7 — Issue Selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/108

**Issue title:** No test verifies that the mock LLM provider returns responses in the expected format

**Claim comment:** https://github.com/jamjamgobambam/pathreview/issues/108#issuecomment-4938550638

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview uses two embedding providers: `MockEmbeddingProvider` for local development and testing, and `OpenAIEmbeddingProvider` for the production application. Both providers are expected to return embeddings in the same format so that the mock can accurately replace the real provider during testing. The current test suite (`tests/unit/test_llm_provider_contract.py`) thoroughly tests the mock provider but never verifies that its output matches the structure of the real OpenAI provider — the only test involving the real provider checks that an `embed` method exists, which does not confirm that both providers return compatible responses. As a result, the mock provider could drift away from the real provider over time, allowing all tests to pass while the application fails when using the actual OpenAI service. A successful fix adds a contract test ensuring both providers follow the same interface and output structure, making the test suite more reliable.

**Selection reasoning ("Is this right for me?" checklist):**
I selected Issue #108 after carefully evaluating several Tier 1 issues. I first investigated Issues #107, #123, and #106, but found that one could not be reproduced, another was already outdated because the fix already existed in the Makefile, and the third had already been claimed with an open pull request. Rather than choosing an issue without verifying it, I confirmed that Issue #108 was still unclaimed, reviewed the referenced test file end-to-end, and verified locally that the missing contract test described in the issue is genuinely absent. I chose this issue because it has a clear and manageable scope (Tier 1, centered on one test file), addresses a real testing gap in the codebase, and aligns with my previous experience reading existing code and writing unit tests, making it realistic to complete within the four-week timeline.

**Branch name:** test/108-mock-llm-provider-contract

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## Week 8 — Reproduction & Solution Planning

**Reproduction commit link:** https://github.com/AddreeBarua/pathreview/commit/f6ac40c

**Reproduction summary:**
Ran `.venv/bin/pytest tests/unit/test_llm_provider_contract.py -v` → 27 passed, then confirmed by reading the file that no test compares the mock provider's output structure against the real OpenAI provider's — the only real-provider coverage is a `hasattr` check, so all tests stay green even if the formats diverge. The reproduction is documented in PLAN.md.

**PLAN.md link:** https://github.com/AddreeBarua/pathreview/blob/test/108-mock-llm-provider-contract/PLAN.md

**Walkthrough video (recommended):** https://www.loom.com/share/d2fe927f53f343ee946fa1b8d58a0ed5

**Blockers or open questions:** None.

---

## Week 9 — Solution Building & PR Submission

### Check-in 1 (mid-week)

**Current progress:**
PLAN.md sub-tasks 1–3 complete: added the mocked-OpenAI fixture and the `TestProviderContractParity` class (7 tests) to `tests/unit/test_llm_provider_contract.py`. All 34 tests pass locally (27 existing + 7 new).

**Next steps:**
Run the linter/formatter/type checker on changed files, resolve pre-commit hook findings, and open the PR.

**Blockers:**
The strict mypy pre-commit hook required type annotations on every function in the touched files, including the 27 pre-existing tests — resolved by annotating the whole module.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/jamjamgobambam/pathreview/pull/136

**Branch:** test/108-mock-llm-provider-contract

**What you built:**
A `TestProviderContractParity` test class that mocks the OpenAI client (patched at `openai.OpenAI`, response shaped like the real SDK) so `OpenAIEmbeddingProvider.embed()` can run offline, then asserts both providers return identically structured responses: list type, one vector per input, lists of floats, matching 1536 dimensionality, empty-input handling, batch consistency, and factory return types.

**Tests added or updated:**
`tests/unit/test_llm_provider_contract.py` — 7 new contract parity tests; type annotations added across the module. `ingestion/embeddings/provider.py` — annotation and exception-chaining fixes required by the pre-commit hooks.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(In a codebase with documented pre-existing failures: my changed files pass ruff/black/mypy via the pre-commit hooks, and `make test-unit` shows the same 53 pre-existing failures on `main` and my branch — verified by running the suite on both — with 7 new passes and no new failures from my change.)

**Draft PR feedback received from:** none

---

## Week 10 — Reflection

**1. What was harder than you expected?**
The hardest part was getting the development environment working correctly before I could even begin working on Issue #108. I had to install Docker Desktop and Node.js, and then troubleshoot a ChromaDB container crash caused by NumPy 2.0 compatibility. I also did not expect adding mypy type annotations to the existing `test_llm_provider_contract.py` file to take so much time, because the pre-commit hook required annotations across the entire test module.

**2. What did you learn about working in a large codebase?**
I learned that working in a large codebase requires understanding the existing structure and conventions before making changes. For Issue #108, I had to review the existing tests, inspect the embedding provider implementation, and understand how the mock and real providers were expected to behave before creating the `TestProviderContractParity` class. I also learned that changes in one test file can trigger project-wide quality checks, such as Ruff, Black, and strict mypy checks.

**3. How did AI tools help — and where did they fall short?**
AI tools helped me understand unfamiliar parts of the codebase, think through testing approaches, and troubleshoot some of the technical issues I encountered during the project. However, AI could not replace actually running the code and verifying the results; I still had to test the solution myself and confirm that the 34 tests passed and that the pre-commit hooks succeeded. I learned that AI is most useful as a supporting tool, while the developer still needs to understand and verify the changes.

**4. What would you do differently if you started over?**
If I started over, I would spend more time checking the repository's existing configuration and quality requirements before making changes. In particular, I would check the mypy requirements earlier so I could avoid spending additional time adding annotations to the existing functions in `test_llm_provider_contract.py`. I would also continue using a systematic process for vetting issues because checking whether an issue was already claimed, fixed, or reproducible helped me avoid working on the wrong issue.

**5. What are you most proud of from this module?**
I am most proud that I completed the full open-source contribution process from beginning to end: setting up the repository, selecting and reproducing an issue, creating a plan, implementing the tests, running quality checks, and submitting PR #136. I added seven contract parity tests covering response structure, vector dimensions, empty inputs, batches, and provider factory types, while keeping the existing tests passing. I am also proud that I documented my decisions and progress in `JOURNAL.md` and `PLAN.md`, giving me a complete record of my contribution.

**Reviewer Feedback:**
No reviewer feedback arrived during the project. Since the grading process does not depend on receiving reviewer feedback, I documented that no review was received and left the PR ready for review.
