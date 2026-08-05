## Solution plan

**Issue:** [Architecture doc doesn't explain the hybrid retrieval scoring formula](https://github.com/ascherj/pathreview/issues/36)

### Understand

> What is the root cause of this issue? What behavior is expected vs. actual?

The hybrid scoring logic was implemented in `HybridRetriever` (`rag/retriever/hybrid.py`) but never documented. The architecture doc's RAG subsection was written at a higher level and stops after naming the two search methods, so the formula, the default weights, and the blending behavior exist only in source code.

**Expected behavior:**

The "RAG System" section of `docs/ARCHITECTURE.md` should contain a new subsection explaining how hybrid retrieval combines its two search methods: the scoring formula, the default weights, and an example.

**Actual behavior:**

The "RAG System" section of `docs/ARCHITECTURE.md` describes hybrid retrieval and mentions vector similarity and BM25 keyword search but says nothing about how their scores are blended.

### Map

> Which files, functions, or modules are involved? List the specific files you expect to touch.

**Involved files, functions, or modules:**

* `rag/retriever/hybrid.py`, specifically `HybridRetriever.__init__` (default weights) and `retrieve()` (scoring steps)

**Files to touch:**

* `docs/ARCHITECTURE.md`

### Plan

> What are the steps to fix this issue? Break it into 3–5 concrete sub-tasks.

1. Draft a new subsection under "RAG System" in `docs/ARCHITECTURE.md` covering the hybrid retrieval scoring formula.
2. Verify all details in the new subsection sentence by sentence against `HybridRetriever.retrieve()`.
3. Add an example and verify the correctness of the example.
4. Check spelling, grammar, and format consistency.

### Inputs & outputs

> What does your fix take as input? What should it produce or change?

**Input:**

The current `docs/ARCHITECTURE.md` and `rag/retriever/hybrid.py`.

**Produce:**

Updated `docs/ARCHITECTURE.md` with a new subsection containing the hybrid retrieval scoring formula and an example.

### Risks & unknowns

> What could go wrong? What are you still unsure about?

**What could go wrong:**

1. The new subsection becomes incorrect if the defaults in `HybridRetriever.__init__` ever change.
    Mitigation: present 0.7/0.3 explicitly as constructor defaults and name where they live, rather than stating them as fixed properties of the system.

2. Inaccurately describing the scoring formula would make the doc worse than the current state.
    Mitigation: Verify all details in the new subsection sentence by sentence against `HybridRetriever.retrieve()`.

**Still unsure about:**

Nothing.

### Edge cases

> What inputs or states should your fix handle gracefully?

Inputs or states in the code sense are not applicable to this docs-only issue.

Edge cases the updated `docs/ARCHITECTURE.md` must document correctly:

* A chunk found by only one method in hybrid scoring
* Empty results from either method
* All blended scores below the minimum score threshold
