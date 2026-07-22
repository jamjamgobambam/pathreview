# PathReview Contribution Journal

A running record of my Module 3 work on PathReview.

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/149

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The issue is in PathReview's StructuralChunker, which only creates sections from content that appears under Markdown headings. If a document contains no headings, _extract_sections never records any text, causing chunk() to return an empty list. As a result, heading-less documents are silently excluded from the RAG indexing pipeline and cannot be retrieved during searches. A successful fix would ensure that any non-empty document without headings is still chunked—either as a single chunk or by using the semantic chunker fallback—so every valid document contributes at least one chunk to the index and the existing test_document_with_no_headings passes.

**Branch name:** fix/149-structural-chunker-no-headings

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

Issue Selection & Readiness
"Is this right for me?" — Scope reasoning (selection notes)
Single, well-defined location. The bug lives in one file, ingestion/chunking/structural_chunker.py (specifically the content-collection guard in _extract_sections). No cross-subsystem changes are required.
Clear, reproducible failure. Running StructuralChunker().chunk("plain text ...", {}) returns []. This is easy to reproduce and verify once fixed.
Existing test defines "done". There is already a failing unit test, test_document_with_no_headings in tests/unit/test_structural_chunker.py. The goal is to make that test pass without breaking the existing heading-based tests.
Right size for a first contribution. The issue is tagged Tier 1 and good first issue, making it a small, localized fix rather than a large refactor.
I understand the surrounding code. I traced the issue to the if heading_stack or current_section_lines guard in _extract_sections, which prevents content from being collected when a document has no headings.
Conclusion. This issue is within my current skill level and is an appropriate first open-source contribution.
Setup Notes
Forked the repository and cloned it locally.
Configured remotes:
origin → samanth1111-1111/pathreview
upstream → ascherj/pathreview
Created a .env file from .env.example using LLM_PROVIDER=mock.
Installed frontend dependencies with npm install.
Verified the Vite development server runs at http://localhost:5173.
Outstanding: Install Docker Desktop and make, then run make setup and make run to start PostgreSQL, Redis, and the backend services.
Part 1 — Understanding the Issue
Can I explain what this issue is asking for in my own words?

The issue occurs because the structural chunker only collects text after encountering a Markdown heading. If a document has no headings, it produces no chunks. The fix should ensure that plain-text documents are still chunked instead of being silently dropped.

✅ I can explain the problem and the expected behavior in 2–3 sentences without rereading the issue.
Do I understand which part of the app is affected?

The issue affects the ingestion pipeline, specifically the structural chunking logic in ingestion/chunking/structural_chunker.py.

✅ I've located the relevant files and confirmed they exist in the codebase.
Do I understand what "done" looks like?

Before the fix, documents without Markdown headings produce no chunks. After the fix, they should still produce at least one chunk while preserving the existing behavior for documents that do contain headings.

✅ I can describe a concrete before-and-after.
Part 2 — Tier Fit
Is the tier a realistic match for where I am right now?

 Picking a Tier 1 issue is appropriate. The change is localized, has clear acceptance criteria, and does not require understanding the entire system.

Part 3 — Codebase Readiness
Can I find the relevant code?
✅ I've found and read the specific code the issue references.
Do I understand the surrounding code well enough to change it safely?

I understand how _extract_sections processes documents and where the bug occurs, so I can outline the change before editing the code.

✅ I've read enough surrounding context that I can write a rough plan for the fix.
Have I read the relevant test file?
✅ I've found the test file (tests/unit/test_structural_chunker.py) and reviewed the existing tests.
Part 4 — Scope and Time
How many others are already working on this issue?
19
Is the scope realistic for Weeks 8–9?

This Tier 1 issue is expected to take approximately 3–6 hours. Based on its scope, I am confident I can complete it before the Week 9 deadline.

✅ I've estimated the time required and believe it is realistic.
Are there any blockers or dependencies?

I still need to install Docker Desktop and make to run the full backend. However, this does not block this issue because the fix is in ingestion/chunking/structural_chunker.py and can be tested using the existing unit test with pytest.

✅ I have identified the remaining setup steps, and they do not block this fix.