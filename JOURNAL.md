## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/149

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** \[x] Tier 1  \[ ] Tier 2  \[ ] Tier 3

**Problem summary:**
The RAG ingestion pipeline chunks documents by splitting on markdown headings. StructuralChunker's section-extraction logic only starts collecting content once it has already seen a heading, so a document with zero headings never triggers collection and returns no sections at all. Since chunk() has nothing to loop over in that case, it returns an empty list instead of at least one chunk. The pipeline never flags a zero-chunk result as an error, so a real candidate's README that just doesn't use markdown headings would silently contribute nothing to their review. The fix reuses the file's existing SemanticChunker fallback (already used for oversized sections) so headingless documents get chunked too, instead of dropped.

**Branch name:** fix/149-structural-chunker-no-headings

**Setup confirmation:** \[x] App runs locally at localhost:5173

**Cohort ledger:** \[ ] Issue added to cohort ledger





\## Week 8 — Reproduction \& solution planning



**Reproduction commit link:** https://github.com/akshaypsharma-AIA/pathreview/commit/a7452b2



\*\*Reproduction summary:\*\*

Ran `pytest tests/unit/test\_structural\_chunker.py -k test\_document\_with\_no\_headings -v` locally. It failed with `assert 0 >= 1` / `where 0 = len(\[])`, confirming `StructuralChunker.chunk()` returns an empty list for a headingless plain-text document instead of at least one chunk.



*PLAN.md link:** https://github.com/akshaypsharma-AIA/pathreview/blob/fix/149-structural-chunker-no-headings/PLAN.md



\*\*Walkthrough video (recommended):\*\* \[skip, or add later — not graded]



\*\*Blockers or open questions:\*\*

Confirming semantic\_chunker.py's token-based sub-splitting handles very large headingless documents sensibly.


### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in structural_chunker.py's chunk() -- falls back to SemanticChunker when no headings are found, instead of returning an empty list. Added missing type annotations to both structural_chunker.py and semantic_chunker.py so ruff/black/mypy pass clean on both files. All tests in test_structural_chunker.py (15/15) and test_semantic_chunker.py (16/16) pass, including the previously-failing test_document_with_no_headings.

**Next steps:**
Open the pull request against ascherj/pathreview, write the PR description (noting pre-existing unrelated test failures), and request review.

**Blockers:**
make test-unit shows 52 pre-existing failures across ~15 unrelated test files (bias detector, PII scrubber, faithfulness checker, tech detector, skill extractor, etc.) -- none touch the files I changed, and my two test files pass 100%. Documenting these as pre-existing rather than fixing them, per course guidance.



### Week 9 Check-in 2

- **PR link:** https://github.com/ascherj/pathreview/pull/444
- **Branch:** fix/149-structural-chunker-no-headings
- **What was built:** StructuralChunker.chunk() now falls back to SemanticChunker when no headings are found, instead of silently returning an empty list. Also added missing type annotations to structural_chunker.py and semantic_chunker.py (required to pass pre-commit's mypy hook, no behavior change).
- **Tests added/updated:** test_document_with_no_headings (previously failing) now passes. Full suite: 15/15 in test_structural_chunker.py, 16/16 in test_semantic_chunker.py.
- **Self-review:**
  - [x] make check passes on changed files (ruff, black, mypy all clean)
  - [x] make test-unit passes for changed files (52 pre-existing failures elsewhere, documented, unrelated to this change)
- **Draft PR feedback received:** [fill in once someone responds on Slack]



### Week 9 Closing Note

- **PR status:** Marked "Ready for review" on [date]. Requested review via
  Slack (2x) and CodePath support email; no reviewer response received by
  the extended deadline.
- **Verification in lieu of peer review:** Full test suite passing for
  changed files, ruff/black/mypy clean, changes scoped to the two files
  needed for the fix. Confident in correctness pending maintainer approval.
- **Branch:** fix/149-structural-chunker-no-headings
- **PR:** https://github.com/ascherj/pathreview/pull/444



## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review (not a feature this term per course note)

**Summary of feedback:**
No feedback received. Also requested review proactively via Slack (2x)
and in a PR comment, before learning reviewer feedback isn't enabled
for Summer 2026 — good practice to keep regardless.

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Getting the local dev environment running on Windows took longer than
the actual bug fix — Docker Desktop needed WSL2, `make` wasn't
available out of the box, and pasting multi-line commands into Git
Bash silently corrupted them (bracketed paste mode), which cost real
time before I switched to editing files directly. The other surprise:
pre-commit hooks check the whole file (and, for mypy, files it
imports) — not just my diff — so a 3-line fix got blocked by
pre-existing type-annotation gaps in two files I hadn't touched the
logic of.

**What did you learn about working in a large codebase?**
That "don't make it worse" is the actual bar, not "leave everything
clean." This repo had ~183 pre-existing lint errors and 52 failing
tests scattered across other modules, and the right move was to
verify none of them were in my changed files and move on — not to
fix them. I also got a much clearer mental model of forks: issues and
PRs live on the upstream repo, not the fork, which is why I was
commenting on ascherj's thread instead of my own.

**How did AI tools help — and where did they fall short?**
Most useful for diagnosing the root cause quickly and explaining
git/tooling concepts I was rusty on, without derailing the fix
itself. Less useful for judgment calls specific to this codebase —
like which pre-existing failures were safe to ignore — where I had
to verify things myself rather than trust it outright.

**What would you do differently if you started over?**
Set up the dev environment and run a scoped lint/type-check on my
target file in week 7, before writing any fix — that would've
surfaced the pre-existing annotation gaps early instead of mid-commit
under deadline pressure.

**What are you most proud of from this module?**
Diagnosing and fixing a real silent-data-loss bug end to end — under
a genuine time crunch — while actually understanding every step
instead of just executing commands I didn't follow.