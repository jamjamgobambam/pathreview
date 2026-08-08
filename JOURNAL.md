## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/149

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `StructuralChunker` class is responsible for splitting documents into
smaller pieces ("chunks") before they're added to the RAG index, so the app
can search and retrieve relevant sections later. Right now, it only knows how
to split documents that have markdown headings — if a document has no
headings at all, the chunker returns an empty list instead of treating the
whole document as one chunk or falling back to a different splitting
strategy. This means any heading-less document is silently dropped from the
index entirely, so its content becomes invisible to search and retrieval,
with no warning or error to indicate anything went wrong. A successful fix
would make `StructuralChunker.chunk()` return at least one chunk for these
documents, likely by adding a fallback path when no headings are detected,
and there's already a failing test (`test_document_with_no_headings`) that
should pass once the fix is correct.

**Branch name:** fix/149-structural-chunker-no-headings

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/bairejavier1/pathreview/commit/f3f1dfce7664a11401adfbea7c9f149ef569cf0f

**Reproduction summary:**
Ran the reproduction script directly against StructuralChunker.chunk() with a ~1000-character headingless document and confirmed it returns 0 chunks. Also ran test_document_with_no_headings directly and confirmed it fails with assert 0 >= 1 where 0 = len([]). Traced the root cause to _extract_sections(), where a guard condition prevents any content line from being collected unless a heading has already been seen, so headingless documents never populate current_section_lines and no section is ever recorded.

**PLAN.md link:** https://github.com/bairejavier1/pathreview/blob/fix/149-structural-chunker-no-headings/PLAN.md

**Walkthrough video (recommended):** Not yet ready

**Blockers or open questions:**
Still need to confirm whether other parts of the codebase (agent/, rag/) assume heading_level is always an integer 1-6, since headingless sections will need some sentinel value there.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed the root-cause investigation from PLAN.md: traced the bug to the guard condition in `_extract_sections()` that only collected content lines once `heading_stack` was non-empty. Implemented the fix by replacing that guard with a content-based check, allowing headingless documents to be captured as a section. Verified the fix resolves the original repro (`chunk()` now returns 1 chunk instead of 0 for a headingless document) and confirmed all pre-existing tests in `test_structural_chunker.py` still pass.

**Next steps:**
Add a new test covering a headingless document that also exceeds `SECTION_TOKEN_LIMIT`, to confirm the `SemanticChunker` sub-chunking fallback works correctly for this case too. Then run `make check` and `make test-unit` for full self-review, document any pre-existing failures, and open the PR.

**Blockers:**
None — the fix ended up being narrower in scope than expected once the root cause was clear.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/578

**Branch:** fix/149-structural-chunker-no-headings

**What you built:**
Fixed `StructuralChunker._extract_sections()` so documents with no markdown headings are no longer silently dropped from the RAG index. The fix replaces a guard condition that depended on heading state with one that checks for actual accumulated content, so headingless documents are now captured as a section (using `heading_path=""` and `heading_level=0` as sentinel values) instead of producing an empty chunk list.

**Tests added or updated:**
Added `test_large_document_with_no_headings_is_sub_chunked` in `tests/unit/test_structural_chunker.py`, covering the case where a headingless document also exceeds `SECTION_TOKEN_LIMIT` and must be routed through `SemanticChunker` rather than returned as a single oversized chunk. The pre-existing `test_document_with_no_headings` test (previously failing) now passes without modification.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*(Both commands surface pre-existing, unrelated failures documented in the PR description — 52 pre-existing test failures across unrelated modules and 182 pre-existing lint errors repo-wide, plus a pre-existing mypy/NumPy stub incompatibility. This change introduces no new failures in any of the three.)*

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback arrived. Per the Su26 course note, reviewer feedback is not a feature offered this term, so no review was expected.

**How you responded:**
N/A — no feedback was received to respond to.

---

### Reflection

**What was harder than you expected?**
I expected the actual code fix to be the hard part, but it turned out to be the smallest piece of the whole process. Getting my local environment running consumed most of my early effort - make wasn't installed on Windows by default, then Docker wasn't installed at all, and once both were sorted, the ChromaDB container crashed on startup because its own entrypoint script reinstalled chroma-hnswlib and pulled in NumPy 2.x, which broke compatibility with code written for NumPy 1.x (np.float_ had been removed). I had to override the container's entrypoint in docker-compose.yml to pin numpy<2 and a specific chroma-hnswlib version just to get a healthy vector-db container. None of that was mentioned in SETUP.md - I had to read raw container logs and reason about what "Rebuilding hnsw to ensure architecture compatibility" actually meant.

**What did you learn about working in a large codebase?**
The biggest thing was learning to distinguish my bug from the codebase's pre-existing problems. When I ran make test-unit and make check after implementing my fix, I got back 52 failing tests and 182 lint errors - none of which had anything to do with structural_chunker.py. My first instinct was that I'd broken something, but tracing through the failures (review_service.py's async mocking issues, resume_parser.py's markdown-stripping bugs, a repo-wide mypy failure caused by NumPy's type stubs needing Python 3.12 syntax) showed they were unrelated and pre-existing. Learning to scope my verification narrowly - "did I introduce new failures in files I touched" rather than "is the whole repo green" - was a real shift from how I'd think about a personal project, where I'd just expect everything to pass.

**How did AI tools help - and where did they fall short?**
Claude was most useful for exactly the kind of pattern-matching debugging I was doing constantly: reading a Docker error and immediately identifying it was a NumPy 2.0 breaking change, or reading a pytest traceback and immediately spotting that _extract_sections()'s guard condition (if heading_stack or current_section_lines:) was checking the wrong state. Where it fell short was anywhere requiring live verification I had to do myself - it couldn't see my actual terminal output, browser DevTools Network tab, or database contents without me pasting them in each time, and at one point it initially suggested a fix with broken Python indentation from a copy-paste artifact that I had to catch by running python -m py_compile before trusting it. It was also confidently wrong about whether an OpenRouter API key was required until I pasted the actual .env.example and it corrected itself against the real file instead of what SETUP.md's prose implied.

**What would you do differently if you started over?**
I'd read the actual docker-compose.yml and Makefile before touching SETUP.md's prose instructions, since the two didn't fully agree (SETUP.md mentioned an OPENROUTER_API_KEY that doesn't exist anywhere in the real .env.example). I'd also verify my local environment fully (including a real end-to-end UI test, not just unit tests) before considering the issue "done," since I only discovered - after already submitting my PR - that the "Start Review" form in the frontend never actually saves uploaded resume text to resume_text in the database, meaning my chunker fix, while correct and tested, doesn't actually get exercised by that particular UI flow yet. I'd want to know that earlier in the process, even though it turned out to be a separate, unrelated bug outside issue #149's scope.

**What are you most proud of from this module?**
Diagnosing the actual root cause in _extract_sections() rather than patching around the symptom. The obvious "quick fix" would have been to add a special case like "if not sections: return [Chunk(text=text, metadata=metadata)]" at the end of chunk() - but that would have only covered the exact "zero headings" case named in the issue. Instead, I traced the real problem to the guard condition checking heading state instead of content state, and fixed that condition directly, which turned out to also correctly handle a related edge case (leading blank lines before a document's first heading) that no existing test even covered. That felt like the difference between fixing an issue and understanding a codebase.
