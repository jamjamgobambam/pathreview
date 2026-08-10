## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36
**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula
**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The current project documentation fails to explain the mathematical logic behind how search results are ranked. Specifically, `docs/ARCHITECTURE.md` states that the system blends vector and keyword scores, but it lacks the exact scoring formulas, normalization steps, and default configuration parameters used by the engine. A successful fix requires reviewing `rag/retriever/hybrid.py` to extract the precise linear combination math and updating the architecture guide with clear equations and an illustrative example so other developers can understand how search queries are processed.

**Branch name:** docs/36-hybrid-retrieval-scoring
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/jal35/pathreview/commit/f559fe3
**Reproduction summary:**
I verified the gap by opening `docs/ARCHITECTURE.md` and finding that the hybrid retrieval system sections completely lacked the specific algebraic scoring formulas and parameter limits used by the active backend engine.

**PLAN.md link:** https://github.com/jal35/pathreview/blob/docs/36-hybrid-retrieval-scoring/PLAN.md
**Walkthrough video (recommended):** **Blockers or open questions:** None. The core formulas have been successfully verified and documented.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)
**Current progress:**
I have fully implemented the missing hybrid scoring formulas, parameter rules, and an edge-case example inside `docs/ARCHITECTURE.md`. 
**Next steps:**
Open the Pull Request and complete final journal logs.
**Blockers:** None.

---

### Check-in 2 (end of week)
**PR link:** https://github.com/ascherj/pathreview/pull/878
**Branch:** `docs/36-hybrid-retrieval-scoring`
**What you built:**
Added detailed documentation for the hybrid retrieval engine scoring formulas, explaining min-max score normalization, linear weight combination rules ($0.7$ vector / $0.3$ keyword), and modal miss handling.
**Tests added or updated:**
None required (Documentation issue).
**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
Two parts. The content of the change was well received, the reviewer said the
scoring formulas were well-structured, the modal-miss edge case was a practical
detail other developers would benefit from, and the parameter defaults were easy
to scan.

The problem was file integrity, not content. A large block of unrelated,
nonsensical text (starting "Looking at the actual screen, yourself watching this
game...") had been embedded in the middle of the High-Level Data Flow diagram in
`docs/ARCHITECTURE.md` — appended to the top border of the Ingestion Pipeline
box, so the ASCII diagram no longer rendered correctly. The reviewer noted that
in a real-world PR this alone would get the review rejected regardless of the
quality of the rest of the change, and recommended building the habit of
diffing before committing (`git diff --staged`) and reading through the full
file rather than only the sections I edited.

**How you responded:**
Removed the injected block, restoring line 16 to the bare box border it was in
the original scaffold commit. Then verified the fix more broadly rather than
just spot-checking the one line:

- Diffed the branch against the pre-existing scaffold commit (`888af31`) to
  confirm the only remaining changes are the intended RAG scoring section,
  nothing else in the diagram, the subsystem sections, or the ADR links was
  touched.
- Scanned every line in the file over 200 characters to catch any other injected
  block; the four hits were all legitimate prose paragraphs.
- Checked the original line in git history to confirm the restoration matched
  exactly, instead of retyping the border from memory.

One thing the review didn't flag that the full-file read surfaced: my rewrite of
the RAG System paragraph dropped two sentences that were in the original, the
ones documenting the generator ("uses prompt templates to produce structured,
evidence-based feedback") and the evaluator ("scores retrieval relevance and
generation faithfulness"). The new text covers retrieval well but no longer
documents those two components at all.

**Follow-up commit link:** https://github.com/jal35/pathreview/commit/67381d7

---

### Reflection

**What was harder than you expected?**
Understanding a working codebase from the outside was harder to grasp than I
expected. When it's my own project I already know why everything is where it is;
here I had to build that mental model from scratch just to be sure I was reading
`rag/retriever/hybrid.py` correctly. Coming up with the solution was also a
challenge, because I didn't want to just hand the problem to AI and paste back
whatever it gave me. I wanted to actually understand the normalization and
weighting math well enough to explain it in my own words, and holding that line
took longer than accepting the first answer would have.

**What did you learn about working in a large codebase?**
The biggest difference is that I couldn't just assume. This issue had been worked
on before, so I wanted to be precise about what the actual gap was rather than
guessing and starting to write. On my own projects I can afford to explore by
changing things and seeing what breaks; here the code was already correct and
working, so my job was to describe it faithfully, not to reshape it. The balance
I had to find was being careful without getting stuck contemplating forever, at
some point I had to commit to an understanding and write it down.

**How did AI tools help — and where did they fall short?**
AI was most useful for orientation: getting my bearings in an unfamiliar codebase
quickly, and helping me work through the scoring logic when I was stuck on how to
express it. Where it fell short was verification. The nonsense text that ended up
inside my `ARCHITECTURE.md` diagram is the clearest example, AI assistance got
content into the file, but nothing except me reading the full file and diffing it
was ever going to catch that it didn't belong there. That's the part I have to
own. AI could help me understand and draft, but it couldn't be responsible for
whether what I submitted was actually clean.

**What would you do differently if you started over?**
I'd probably pick an issue that involved changing actual code rather than
documentation, so I'd get more practice with the test and review cycle. I'd also
build in a real self-review step before committing instead of treating the work
as done once the content was written, reading the whole file, not just my
sections. That said, I'm glad documentation was my first one; it forced me to
genuinely understand the retrieval math instead of hiding behind a passing test,
and it's made me eager to take on more.

**What are you most proud of from this module?**
Sticking with it through the part I didn't understand. The hybrid scoring formula
was genuinely confusing at first, and it would have been easy to write something
vague that sounded right. Instead I stayed with it until I could explain the
min-max normalization and the $0.7$/$0.3$ weighting clearly enough that another
developer could follow it, and the reviewer specifically said that part was
well-structured and useful.
