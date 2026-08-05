# JOURNAL

A running record of progress throughout Module 3. A new section is added each week.

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/ARCHITECTURE.md` mentions that the RAG system uses hybrid retrieval blending
vector similarity and BM25 keyword scores, but it never explains how those scores are
actually combined. There is no description of the default weights, no explanation of how
each score is normalized, and no worked example, so a contributor cannot understand or
tune the ranking behavior from the docs alone. The scoring logic lives in
`rag/retriever/hybrid.py` (`HybridRetriever.retrieve()`), which normalizes each modality
to 0–1 and blends them with a 0.7 vector / 0.3 keyword weighting. A successful fix adds a
"Hybrid Retrieval Scoring" section to `docs/ARCHITECTURE.md` covering the formula, the
default weights, normalization, a numerical example, and relevant edge cases.

**Branch name:** docs/36-hybrid-retrieval-scoring

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/tsunderii/pathreview/commit/df02de1f375ef22545b7e89f2e7e3ac589101118

**Reproduction summary:**
Because this is a documentation gap (not a runtime bug), I reproduced it by confirming
the formula is absent from the docs while it exists in code: `grep -in
"weight|normali|bm25|blend|formula|min_score" docs/ARCHITECTURE.md` returns only the
single one-line mention at line 60 (no weights, no normalization, no example), whereas the
actual blending lives in `rag/retriever/hybrid.py:58-81`. I then reproduced the scoring
math by re-implementing lines 58–81 in a standalone script over a sample candidate set and
observed the exact blended scores I plan to document (A=1.000, C=0.500, B=0.467; D=0.075
dropped by the default `min_score=0.3`), confirming I understand precisely what is missing
and where it belongs.

**PLAN.md link:** https://github.com/tsunderii/pathreview/blob/docs/36-hybrid-retrieval-scoring/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
- Two adjacent code observations may be out of scope for a docs-only fix but are worth
  flagging in the PR: (a) `retrieve()` fetches `all_chunks` at hybrid.py:50 but never calls
  `keyword_searcher.index(...)`, so the keyword arm can be empty; (b) the similarity comment
  at vector_store.py:102 says "euclidean" while the collection is created with cosine space
  (vector_store.py:36). I plan to document intended behavior and note these separately rather
  than fix code in this issue.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Started building the fix from PLAN.md. Sub-tasks 1–2 are in place: I re-read the scoring
logic in `rag/retriever/hybrid.py` and drafted the `#### Hybrid Retrieval Scoring` subsection
in `docs/ARCHITECTURE.md` with the blended-score formula and the default 0.7/0.3 weights
table. Sub-task 3 (the worked numerical example) is partially written — I still need to run
the numbers back through the exact code path to make sure the blended values I quote are
correct before I trust them in the docs. Sub-task 4 (notes/edge cases) is only outlined so far.

**Next steps:**
Validate the numerical example against the real formula, finish the edge-cases list, then
move to sub-task 5: set up the venv, record the `make check` / `make test-unit` baseline,
fill in the PR template, and open the PR against upstream `main`.

**Blockers:**
Local env isn't fully set up yet (`.venv` missing), so I haven't been able to run
`make check` / `make test-unit` to confirm a baseline — planning to build it before opening
the PR. No blockers on the writing itself.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/490

**Branch:** `docs/36-hybrid-retrieval-scoring`

**What you built:**
A documentation-only change that adds a "Hybrid Retrieval Scoring" section to
`docs/ARCHITECTURE.md`. It explains how `HybridRetriever.retrieve()` blends vector and BM25
scores (`blended = 0.7·norm_vector + 0.3·norm_keyword`), how each score is max-normalized to
0–1, and walks through a numerical example, plus edge cases such as the `min_score` threshold.

**Tests added or updated:**
None — this is a documentation-only change (no Python touched), so no unit tests apply. Ran
the existing suite to confirm no regressions.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

> "Passes" here follows the course rule for a codebase with documented pre-existing failures:
> **this change introduces no new failures.** Baselines observed before my change (all in
> Python/config files this branch does not touch): `make test-unit` = 53 failed / 375 passed;
> `ruff check .` = 182 errors; `black --check .` = 52 files; `mypy` = 5 errors. After my
> markdown-only change the numbers are identical (0 new failures); this branch modifies only
> `.md` files, which none of these tools inspect.

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No review has come in. PR
[#490](https://github.com/ascherj/pathreview/pull/490) ("docs(rag): document hybrid
retrieval scoring formula") has been open against upstream `main` since 2026-08-01 and
as of 2026-08-04 shows 0 comments, 0 reviews, and no requested changes; nobody has been
assigned as a reviewer and no maintainer has commented on issue #36 either. Per the Su26
note, reviewer feedback isn't a feature this term, so this is the expected outcome.

**How you responded:**
Nothing to respond to. I re-checked the PR state before writing this entry rather than
assuming, left the branch as submitted, and did not push cosmetic churn just to look
active. Two things I did leave in the PR description for whoever eventually picks it up:
the two adjacent code smells I deliberately kept out of scope — `retrieve()` fetching
`all_chunks` at `rag/retriever/hybrid.py:50` without ever calling
`keyword_searcher.index(...)` (so the keyword arm can silently be empty), and the
"euclidean" comment at `rag/retriever/vector_store.py:102` contradicting the cosine space
the collection is actually created with at line 36. If a maintainer responds after the due
date, the natural follow-ups are those two as separate issues, plus their call on whether
the 0.7/0.3 weight rationale belongs inline or in its own ADR.

---

### Reflection

**What was harder than you expected?**
Proving I was right about the numbers. The docs change itself was maybe two hours of
writing; making sure the worked example was *actually* what the code produces took longer
than the writing did. In Week 9 Check-in 1 I had a draft example written from reading
`hybrid.py` and reasoning about it — and I didn't trust it, so I re-implemented lines 58–81
in a standalone script and ran a sample candidate set through it. That's how the final
numbers (A=1.000, C=0.500, B=0.467, and D=0.075 getting dropped by the default
`min_score=0.3`) got confirmed rather than guessed. Reading code and believing you know
what it outputs are two very different confidence levels, and a doc that quotes wrong
numbers is worse than a doc with no numbers, because now a reader will trust it.

The other genuinely hard part was the environment, and it was hard in a demoralizing way
rather than an interesting one. I couldn't get a clean baseline until late because `.venv`
wasn't set up, and when I finally ran the suite the baseline was 53 failing unit tests, 182
ruff errors, 52 files failing `black --check`, and 5 mypy errors — all pre-existing, none in
anything I touched. Figuring out that "make check passes" had to mean "introduces no new
failures" rather than "is green," and then documenting that honestly with before/after
numbers instead of just ticking the box, was a judgment call I didn't expect a docs PR to
require.

**What did you learn about working in a large codebase?**
That the hardest part isn't writing the change, it's establishing the boundary of the
change. On my own projects, finding `hybrid.py:50` never re-indexing the keyword searcher
would mean fixing it in the same commit — it's right there, it looks like a real bug, it
would take ten minutes. Here the right move was to *not* fix it: it's a behavioral change
riding inside a documentation PR, it needs its own reproduction and its own review, and
bundling it would make a reviewable 60-line markdown diff into something a maintainer has
to reason about carefully. Writing it down in PLAN.md under "Risks & unknowns" and flagging
it in the PR turned out to be more useful than fixing it would have been.

I also learned that in someone else's production code, the source is the specification.
There was no design doc telling me why 0.7/0.3 — that ratio just exists in a constructor
default at `hybrid.py:14`, unvalidated, with nothing saying whether it was tuned or
guessed. I could document *what* it does with confidence and had to be honest in the
edge-cases list that the weights aren't validated and don't have to sum to 1, rather than
inventing a rationale. The temptation to smooth over gaps in your own understanding is much
stronger when writing docs than when writing code, because docs never fail a test.

And the pre-existing red suite taught me something about scale: a codebase this size is
never fully healthy, and "don't make it worse" is a real, defensible standard. That felt
like lowering the bar at first. It isn't — it's the only standard that lets anyone land
anything.

**How did AI tools help — and where did they fall short?**
Most useful for orientation and for structure. Tracing the actual data path — that vector
similarity is `1 / (1 + distance)` at `vector_store.py:103`, that both modalities get
max-normalized per query, where the `min_score` filter and `max_chunks` truncation sit
relative to the blend — was fast with AI help in a way that manually reading four files in
`rag/retriever/` would not have been. It was also good at the mechanical writing: turning
my confirmed facts into a formula block, a weights table, and a clean edge-case list that
matches the surrounding tone of ARCHITECTURE.md.

Where it fell short: it will produce a confident, plausible, well-formatted numerical
example without ever running the code. Early drafts of the worked example looked completely
correct and were not something I was willing to put in a maintainer's docs on vibes. The
standalone re-implementation of the scoring block was the step that mattered, and that was
me deciding to verify rather than the tool telling me to. Same with scope: AI was perfectly
happy to keep going and fix the keyword-indexing bug while we were in there. Knowing that a
docs issue stays a docs issue, and that a maintainer's review budget is a real resource
you're spending, is judgment about the social side of contributing that the tool doesn't
have. It's an accelerant on the parts I could already check, and a liability on the parts I
couldn't.

**What would you do differently if you started over?**
Set up the environment in Week 7, not Week 9. I picked the issue and confirmed the app ran
at localhost:5173, then didn't build `.venv` until I needed to run `make check` right before
opening the PR — which is exactly when discovering a 53-failure baseline is most disruptive.
It cost me a Check-in 1 where "blockers" was an environment problem instead of a substantive
one. Two hours in Week 7 would have bought a calm Week 9.

I'd also verify the numbers *before* drafting the prose around them, not after. I wrote the
example first and validated second, which meant rewriting sentences to fit the corrected
values. Verification-first would have been strictly cheaper.

On issue selection I'd make the same call. A Tier 1 docs issue sounds like the safe,
low-ambition pick, and it did have a genuinely small diff — but it forced me to read the
retrieval implementation closely enough to find two real code smells nobody had filed, which
a Tier 2 code fix in a corner of the app wouldn't have. The one thing I'd change is asking
the maintainer up front whether the 0.7/0.3 rationale belonged inline or in an ADR, instead
of picking inline and offering the ADR as a follow-up in the PR. That's a cheap question
that de-risks the whole review.

**What are you most proud of from this module?**
The self-review note in Week 9. It would have been easy — and nobody would have caught it —
to tick "make check passes" and move on, since my change touches only `.md` files that none
of those tools even read. Instead I recorded the actual baseline numbers before and after
and wrote down explicitly that "passes" means "introduces no new failures" in a repo with
documented pre-existing failures. That's the habit I actually want to keep out of this
module: when a claim is technically true but misleading, say the more precise thing, even
when the box would have been ticked either way and no reviewer was ever going to look.
