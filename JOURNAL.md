# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/38

**Issue title:** Add an integration test that runs the full RAG pipeline against a mock LLM

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview has unit tests for individual RAG components, but it does not have an integration test proving that those components work together for a complete query. The missing coverage spans retrieval, reranking, LLM-backed generation, and parsing into structured feedback. A successful test will exercise that full path with a mock LLM so it remains deterministic, avoids external API calls, and can run reliably in automated test environments. The work belongs in `tests/integration/test_rag_pipeline.py` and will verify the contracts between several modules rather than testing them only in isolation.

**Selection notes — “Is this right for me?” checklist:**
- The expected outcome and relevant test file are clearly identified, so the issue has a bounded deliverable.
- The issue is appropriately labeled Tier 2 because it requires tracing data across multiple RAG modules, not changing just one isolated function.
- The 4–6 hour estimate is manageable, and the test can use mocks instead of requiring paid credentials or live LLM calls.
- I can inspect the existing retrieval, generation, parsing, and test-fixture patterns before implementing the integration test and ask maintainers for clarification if the intended mock LLM provider is unclear.
- The change can be verified locally with a focused integration test and the repository’s standard checks, giving it a clear definition of done.

**Branch name:** `test/38-rag-pipeline-integration-test`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [202d0fe](https://github.com/vrajhm/pathreview/commit/202d0feb83f2ad681d18e8975e5087081d1e893e)

**Reproduction summary:**
I ran `pytest --collect-only -q tests/integration` and observed `no tests
collected in 0.01s` because the integration-test package contains no test
module. Tracing the RAG code confirmed that retrieval/ranking, generation, and
parsing exist as separate components but are never exercised together with a
mock LLM.

**PLAN.md link:** [PLAN.md](https://github.com/vrajhm/pathreview/blob/test/38-rag-pipeline-integration-test/PLAN.md)

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
The issue calls out reranking, but the current codebase has no standalone
reranker; the plan treats hybrid score blending and sorting in
`rag/retriever/hybrid.py` as that stage. The local shell also lacks project
dependencies, so the full suite currently stops during collection and must be
rerun in the configured development environment.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was received during Summer 2026. The course notes indicate that reviewer feedback is not part of the Summer 2026 workflow, so there were no maintainer comments to respond to.

**How you responded:**


---

### Reflection

**What was harder than you expected?**

The hardest part was understanding where the boundary of an integration test should be in a codebase that already has tests for many individual components. At first, the issue sounded straightforward: add a test for retrieval, reranking, generation, and parsing. Once I traced the implementation, I found that the repository does not have a standalone reranker. Instead, the hybrid retriever normalizes and blends vector and keyword-search scores, sorts the candidates, and truncates the result set. I therefore had to think about what the issue meant by "reranking" in the context of the actual code rather than assuming there was a class with that name.

I also found that the generation path was more complicated to mock than I initially expected. `ReviewGenerator` constructs an OpenAI client directly and makes multiple completion calls. That meant an integration test could not simply provide one fake LLM response; the fake needed to match the boundary and behavior that the production code actually uses. The environment was another practical difficulty because the local shell was missing dependencies, so a test-collection failure could not automatically be interpreted as a problem with the proposed test itself.

**What did you learn about working in a large codebase?**

I learned that contributing to an existing codebase requires understanding contracts between modules before writing code. In my own projects, I can design the interfaces around the test I want to write. In PathReview, the interfaces already exist, so the test has to reflect how retrieval, generation, and parsing actually communicate.

I also learned that names in an issue do not necessarily map one-to-one to classes or files in the implementation. The issue describes a retrieval → reranking → generation → parsing pipeline, but the repository implements the ranking behavior inside the hybrid retriever rather than through a separate reranker. That made code tracing more important than relying only on the issue description.

Another difference was being careful about scope. My plan deliberately kept the expected production-code footprint at zero and focused on creating deterministic test fixtures around the existing interfaces. That helped me distinguish between fixing the application and testing the application's existing behavior.

**How did AI tools help — and where did they fall short?**

AI tools were most useful for helping me navigate the codebase and reason about how the RAG components fit together. They helped identify the relevant retrieval, keyword-search, vector-store, generation, and output-parsing files and made it easier to form a mental model of the pipeline. They were also useful for turning the issue into a concrete test plan and identifying potential edge cases, such as duplicate retrieval results, score normalization, missing metadata, and multiple LLM calls.

Where AI fell short was in replacing actual verification. It could suggest what the integration test should do, but it could not make an environment with missing dependencies behave correctly or prove that a proposed mock matched the repository's real runtime contracts. I still had to inspect the implementation and distinguish assumptions from behavior that was actually present in the code. This reinforced that AI is most useful as a navigation and reasoning aid, not as a substitute for running and interpreting tests.

**What would you do differently if you started over?**

I would spend more time on the repository's test and dependency setup before committing to the implementation plan. I identified the missing integration-test coverage correctly, but the environment limitations meant that verification was harder than expected. I would establish a working test environment earlier and confirm that the focused integration test can actually execute before spending as much time designing the complete fixture structure.

I would also inspect the generation boundary earlier. The fact that `ReviewGenerator` directly constructs its OpenAI client is important to the testing strategy, and discovering that sooner would have made the implementation plan more concrete from the beginning.

Finally, I would break the work into smaller checkpoints: first prove retrieval and score ordering with deterministic data, then prove the LLM boundary can be replaced, and finally connect the generated response to the output parser. That would make failures easier to localize than attempting to reason about the entire pipeline at once.

**What are you most proud of from this module?**

I am most proud of learning to investigate an unfamiliar codebase systematically instead of treating an issue description as a complete specification. For this issue, I traced the requested pipeline through the actual repository, identified that the "reranking" stage was implemented as hybrid score blending, found the existing mock embedding provider, and identified the OpenAI client boundary as the key challenge for deterministic generation testing. Even though the environment and tooling created limitations, I finished the module with a much better understanding of how to turn an issue into a concrete, testable plan in someone else's codebase.

