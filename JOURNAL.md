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