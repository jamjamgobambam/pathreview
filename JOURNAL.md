# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**  
The architecture documentation explains that PathReview combines vector similarity and BM25 keyword retrieval, but it does not describe how the two scores are normalized and blended. The implementation in `rag/hybrid.py` normalizes each score against the highest score returned by its retrieval method and then calculates a weighted sum using a default vector weight of `0.7` and keyword weight of `0.3`. Without this explanation, contributors cannot easily understand how chunks are ranked or why semantic similarity has more influence than keyword matching. A successful fix will document the normalization process, scoring formula, default weights, filtering behavior, and a numerical example in `docs/ARCHITECTURE.md`.

**Branch name:** `docs/36-hybrid-retrieval-scoring`

**Setup confirmation:** [x ] App runs locally at localhost:5173

**Cohort ledger:** [ x] Issue added to cohort ledger

### Issue selection notes — "Is this right for me?"

This issue is appropriately scoped for a first contribution because it requires a focused documentation change 
rather than a broad code refactor. The relevant implementation is contained in the RAG retrieval files, and the 
issue identifies `docs/ARCHITECTURE.md` as the file to update. I verified the formula and default weights directly from `rag/hybrid.py`, so the documentation can accurately reflect the current behavior. The main risk is documenting assumptions instead of the implementation, which I addressed by reviewing the vector, BM25, normalization, weighting, filtering, and sorting logic before writing the explanation.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/aditichhawacharia/pathreview/commit/8c152852d8913717e5f5b9c0a9e945447cfc5b8d]

**Reproduction summary:**  
Opened `docs/ARCHITECTURE.md` locally and confirmed that the RAG System section describes hybrid retrieval at a high level but contains no formula, no weight values, and no worked example. Cross-referenced against `rag/hybrid.py` and verified the gap is real: the normalization step, the `0.7 / 0.3` weight constants, the minimum-score filter, and the sort-and-truncate step are all implemented in code but absent from the doc.

**PLAN.md link:** [https://github.com/aditichhawacharia/pathreview/blob/docs/36-hybrid-retrieval-scoring/plan.md]

**Blockers or open questions:**  
Need to re-read `rag/hybrid.py` in full before writing the doc to confirm whether `vector_weight` and the minimum-score threshold are hardcoded constants or caller-configurable parameters — this affects how the doc describes the filter step and whether it should mention overridable defaults.

---
## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Re-read `rag/hybrid.py` in full to verify the normalization logic, weight
constants, threshold, and sort behavior. Confirmed that `vector_weight=0.7`
and `keyword_weight=0.3` are constructor-level defaults on `HybridRetriever`,
that per-method normalization divides each raw score by the highest score that
method returned, and that `min_score=0.3` and `max_chunks=10` are defaults on
`retrieve()`. Drafted the Hybrid Retrieval Scoring subsection in
`docs/ARCHITECTURE.md` covering normalization, the weighted-sum formula,
default weights, threshold filtering, and a worked numerical example.

**Next steps:**
Make the minor wording fix clarifying that weights are set at retriever
initialization (not per-query), run `make check` to confirm no linting or
formatting errors, open a draft PR, and request peer feedback.

**Blockers:**
None.

---



### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/393

**Branch:** `docs/36-hybrid-retrieval-scoring`

**What you built:**
Added a “Hybrid Retrieval Scoring” subsection to `docs/ARCHITECTURE.md` explaining how PathReview blends vector similarity and BM25 keyword scores. The section documents per-method score normalization, the weighted-sum formula (`hybrid_score = 0.7 × vector_norm + 0.3 × bm25_norm`), the default weights and where they are configured, the minimum-score filter, and a concrete numerical example showing how two chunks are scored and ranked.

**Tests added or updated:**
No new automated test files were added because the implementation in `rag/hybrid.py` was not modified. This contribution only documents the existing retrieval behavior.

To validate the change, I ran the existing unit test suite with `make test-unit`, including the hybrid retrieval tests that cover score normalization, vector and keyword weighting, minimum-score filtering, result ordering, and maximum-chunk limits. I also ran `make check` to verify that the documentation change introduced no formatting, linting, or repository validation errors.

**Test files reviewed:**

* `tests/unit/test_hybrid.py` — verifies the hybrid retriever’s scoring, filtering, ranking, and result-limit behavior.
* `rag/hybrid.py` — reviewed directly to confirm that the documented formula, default weights, threshold, and sorting behavior match the implementation.

**Coverage provided:**
The existing unit tests exercise the implementation described by the new documentation. Since this PR does not change executable code, no new code paths were introduced and the project’s test coverage percentage is unchanged.

**Self-review confirmation:** [x] `make check` passes  [x] `make test-unit` passes

**Draft PR feedback received from:** None



## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes

**Summary of feedback:**
The grader noted that the hybrid retrieval scoring section was
well-structured and logically sequenced (normalization → formula →
defaults → worked example → filtering), and called out the numerical
example as a particularly strong choice for making the abstract formula
concrete and verifiable. Two areas for improvement were flagged: (1) the
verification process wasn't made reproducible — I ran `make test-unit`
and `make check` but didn't include a small script or PR comment showing
the Python code I used to verify the numerical example against
`rag/hybrid.py`, making it harder for future contributors to re-check;
(2) my PLAN.md identified three edge cases (all chunks below threshold,
single method returning no results, tied scores) that didn't all make
it into the final documentation, leaving gaps a reader hitting those
situations would expect to find covered.

**How you responded:**
No changes were made to the PR after receiving this feedback, as the
review came in at the end of the module. Going forward I would add a
short verification script as a PR comment and treat the PLAN.md edge
case list as a completion checklist rather than a brainstorm — each
item should have an explicit disposition (documented, deferred, or
out-of-scope) before the PR is submitted.

---

### Reflection

**What was harder than you expected?**

Validating a documentation-only change was harder than I anticipated.
When you write code, you run it and see whether it works. When you
write documentation, there's no green checkmark — you have to
deliberately construct your own verification loop. I ran `make
test-unit` and `make check` to confirm I hadn't broken anything, but
I didn't think to go further and write a small script that
independently computed the hybrid retrieval scores from `rag/hybrid.py`
and compared them against the numerical example I put in the docs.
That would have made my verification reproducible for any future
contributor who reads the file and wonders "did someone actually check
this?" Instead, the correctness of the worked example lives only in my
head — which is the exact thing documentation is supposed to fix.

The other thing that surprised me was the gap between identifying edge
cases and actually closing the loop on them. My PLAN.md called out
three edge cases: all chunks falling below the filtering threshold,
a single retrieval method returning no results, and tied scores. I
spotted them, wrote them down, and then didn't fully carry them
through into the final documentation. I documented the happy path
thoroughly and let the edge cases trail off into "worth noting." In a
production codebase, edge cases are where bugs live; a reader who hits
one of those situations will go to the docs first, find nothing, and
have to reverse-engineer the source. I left that work undone.

**What did you learn about working in a large codebase?**

The biggest difference from building my own projects is that in a
large codebase, the cost of ambiguity compounds. When I write my own
code, I can hold context in my head — I know what a function does
because I wrote it last week. In an unfamiliar production repo, I'm
always one imprecise sentence in the docs away from sending a future
contributor down a wrong path. That changes how carefully I have to
write. Every sentence in `ARCHITECTURE.md` is going to be read cold
by someone who doesn't have the context I built up over four weeks.

I also learned that documentation contributions are not just a lighter
version of code contributions — they have their own discipline. The
logical progression I settled on (normalization → formula → defaults
→ example → filtering) wasn't obvious at first; I drafted it in a
different order and had to rearrange it once I read it back cold. The
structure only became clear when I asked myself: "What question would
a new engineer ask first?" That kind of reader-first thinking is a
muscle, and it's one I haven't had to exercise much when building
things for myself.

**How did AI tools help — and where did they fall short?**

AI assistance was most useful for getting oriented quickly. When I
first opened `rag/hybrid.py`, I used AI to get a fast read on what
the scoring logic was doing before I went line by line myself. That
saved probably an hour of guessing at variable names and following
call chains. AI was also useful for drafting the structure of the
documentation — giving me a skeleton I could then edit, rather than
starting from a blank page.

Where it fell short was exactly the verification gap I described
above. AI can help me write a numerical example, but it can't tell me
whether that example is actually correct against the live source code.
I had to do that myself, manually, by reading `hybrid.py` and running
the numbers. I did it — but I didn't capture it in a reproducible
way, which is the part I'd do differently. AI tools also couldn't
help me decide which edge cases were worth including in the docs;
that judgment call required actually understanding how a downstream
engineer would use the hybrid retrieval system, which took reading
the broader codebase, not prompting.

**What would you do differently if you started over?**

Two things. First, after writing any worked numerical example in
documentation, I'd immediately write the corresponding verification
script — even a ten-line Python file that I paste into a PR comment —
so that the math is checkable by anyone, not just me. Second, I'd
treat my PLAN.md edge case list as a checklist with checkboxes, not
just a brainstorm. Every edge case I identify should have a
disposition: documented, deferred (with a reason), or explicitly
out-of-scope. If it's in the plan and absent from the final output,
that's a gap, and I'd want to catch that myself before a reviewer
does.

On issue selection, I'd pick something with a slightly wider blast
radius next time — a documentation contribution is a real contribution,
but I came away wishing I'd also touched a small code change so I
could experience the full review cycle, including having a maintainer
actually run something I wrote.

**What are you most proud of from this module?**

The structure of the hybrid retrieval scoring section. The decision
to sequence it as normalization → formula → defaults → worked example
→ filtering edge cases wasn't the first structure I tried, and getting
there required thinking about the reader's mental model rather than
just transcribing the source code. The worked example in particular —
tracing through a concrete pair of input scores to a final ranked
output — is the kind of thing that makes a document actually useful
instead of just formally complete. Someone can read that and
immediately sanity-check their own system. That's what documentation
is for.
