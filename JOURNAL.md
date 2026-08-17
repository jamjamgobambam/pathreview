## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/149]

**Issue title:** [Structural chunker silently drops documents that contain no headings]

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[The StructuralChunker used by the ingestion pipeline currently fails to create chunks when a document does not contain markdown headings. In ingestion/chunking/structural_chunker.py, the _extract_sections() helper only captures content after detecting a heading, causing heading-free documents to return no chunks even when they contain valid text. This affects README ingestion because StructuralChunker is selected for README documents through the ingestion pipeline. A successful fix would ensure that any non-empty document can still produce at least one chunk while preserving the current behavior for empty documents.]

**Branch name:** [fix/149-structural-chunker-fallback]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Issue selection notes ("Is this right for me?" checklist):**
[I chose this issue because it is my first open source contribution and I wanted to start with a manageable Tier 1 bug. I was able to understand the problem, locate the affected ingestion and chunking files, and identify what the expected behavior should be after the fix. The issue has clear reproduction steps and a related test, which makes it a good fit for learning how to contribute to a larger codebase while keeping the scope realistic for the project timeline.]

---

## Week 8 — Reproduction & solution planning

**Reproduction steps:**
Option A:
```bash
python -m pytest tests/unit/test_structural_chunker.py::TestStructuralChunker::test_document_with_no_headings -v
```

Option B:
```python
from ingestion.chunking.structural_chunker import StructuralChunker
c = StructuralChunker()
text = "This is plain text without any markdown headings. " * 20
print(c.chunk(text, {"source": "test"}))
```

- The test fails because StructuralChunker.chunk() returns an empty list for a document without markdown headings
- The issue originates in ingestion/chunking/structural_chunker.py, where _extract_sections() only collects content after encountering a markdown heading

**Reproduction commit link:** 
[(https://github.com/JairVilleda/pathreview/commit/8b851147b6b2d73ee5a711a93f915ca95782afea)] 

**Reproduction summary:**
I reproduced the issue by running the existing unit test for StructuralChunker and by testing it with a document containing no markdown headings. In both cases, StructuralChunker.chunk() returned an empty list instead of producing at least one chunk.

**PLAN.md link:** 
[(https://github.com/JairVilleda/pathreview/blob/fix/149-structural-chunker-fallback/PLAN.md)]

**Blockers or open questions:**
[None at this time.]

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for issue #149. Updated the structural chunker so documents without markdown headings are no longer silently dropped and can produce a chunk. The reproduction test for heading-less documents now passes.

**Next steps:**
Finish the final testing/checks, review the changes, update the PR, and complete the PR submission.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** [(https://github.com/ascherj/pathreview/pull/1032)]

**Branch:** `fix/149-structural-chunker-fallback`

**What you built:**
Fixed issue #149 by updating the structural chunker so heading-less documents are captured instead of causing `StructuralChunker.chunk()` to return an empty list. This prevents documents without markdown headings from being silently dropped during ingestion.

**Tests added or updated:**
Updated the structural chunker test for documents without headings in `tests/unit/test_structural_chunker.py`. The test verifies that a document without markdown headings produces at least one chunk instead of an empty result.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The hardest part was figuring out where the bug was actually coming from. The issue sounded pretty simple at first because the StructuralChunker was just returning an empty list when a document had no headings. Howevever, I had to spend time understanding how the ingestion pipeline worked and tracing how the document got to the chunker. What surprised me was that nothing crashed. The code ran normally, but the document was basically lost because no chunks were created. That made the problem harder to notice and understand.

**What did you learn about working in a large codebase?**
I learned that working in someone else's codebase takes more time to understand before you can safely make a change. When I work on my own projects, I already know how everything is organized and why I wrote the code a certain way. With PathReview, I had to figure out how different parts of the project worked together before deciding what to change. I also learned that the issue description doesn't always tell you exactly where the problem is. I had to use the tests and follow the code to figure that out.

**How did AI tools help — and where did they fall short?**
AI was really helpful for understanding parts of the codebase that I wasn't familiar with. It helped me break down the ingestion pipeline, understand the StructuralChunker, think about the root cause, and come up with possible tests. It also helped me with some of the GitHub and PR process, which I was still getting used to.

At the same time, I learned that I can't just trust what AI tells me. I still had to run the tests, reproduce the bug myself, and look at the actual code. AI could suggest a solution, but I needed to verify that it actually worked in the project.

**What would you do differently if you started over?**
If I started over, I would spend more time understanding the codebase before thinking about the fix. I would trace how the data moves through the ingestion pipeline, read the related code and tests, and form my own idea of the root cause first. I would still use AI, but more as a second opinion instead of relying on it to explain everything to me. I would also focus on making the smallest change that fixes the actual problem rather than immediately thinking about what code needs to be added. I think this would make me more confident and independent when working in an unfamiliar codebase. At the end of the day, I know more practice will build good habits and make navigating and fixing code easier.

**What are you most proud of from this module?**
I am most proud that I was able to take an issue I didn't fully understand at first and work through it until I had a working solution and PR. This was my first open source contribution. I reproduced the bug, figured out why the StructuralChunker was dropping documents without headings, made the fix, tested it, and documented the process. More than just fixing the bug, I feel like I got more comfortable working in a codebase that I didn't create myself.