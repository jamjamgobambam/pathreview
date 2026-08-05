## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/149

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The structural chunker splits documents by markdown headings. When a document has no
headings, it returns an empty list. That means the document never gets processed into
chunks and never enters the RAG index. The user sees feedback that appears valid, even
though the file itself was never actually read or analyzed. A fix would make it fall back
to processing the entire document as a single chunk when no headings are found. This
affects `_extract_sections` in `ingestion/chunking/structural_chunker.py`.

**Branch name:** fix/149-structural-chunker-no-headings

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes:**
I chose this issue because it is a Tier 1 task and a good opportunity for me to get
familiar with a codebase of this size for the first time. The fix only requires changes in
one file, so the scope is clear and manageable. I can verify the fix by running the
existing failing test, `test_document_with_no_headings`, and confirming that it passes
after the change. The issue was also easier to understand because it already included
reproduction steps, which helped me identify the problem and how to test the solution.
Once I get more comfortable with the codebase and understand the workflow better, I plan
to take on higher-tier issues with more complex changes.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Elias0305Ha/pathreview/commit/fb7fd060db79c6686936df750e992d0407edcd40

**Reproduction summary:**
I set up the local environment and ran the existing unit test suite for the structural
chunker, where `test_document_with_no_headings` fails with `assert 0 >= 1` — a
heading-less document produces zero chunks instead of one. I then probed the chunker
directly and found the same root cause silently discards any text that isn't preceded by
an ATX heading, including the preamble paragraph before a document's first heading.

### How I reproduced it

Environment (Windows, from the repo root):

```
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Note: I had to build the venv against Python 3.12 rather than my default 3.14, because
several pinned dependencies have no prebuilt wheels for 3.14 on Windows.

Run the failing test:

```
.venv\Scripts\python.exe -m pytest tests/unit/test_structural_chunker.py -v
```

Observed result — 14 passed, 1 failed:

```
tests/unit/test_structural_chunker.py::TestStructuralChunker::test_document_with_no_headings FAILED

    def test_document_with_no_headings(self, chunker):
        """Test document with no headings returns single chunk."""
        text = "This is plain text without any markdown headings. " * 20
        result = chunker.chunk(text, {"source": "test"})

>       assert len(result) >= 1
E       assert 0 >= 1
E        +  where 0 = len([])
```

### What I observed directly

Calling `StructuralChunker().chunk(text, metadata)` on a range of inputs:

| Input | Chunks returned | Expected |
| --- | --- | --- |
| Plain text, no headings | **0** | 1 or more |
| Preamble paragraph, then `# Title`, then body | **1** (preamble silently dropped) | 2 |
| `#NotAHeading` (no space after `#`) | **0** | 1 |
| Setext heading (`Title` underlined with `=====`) | **0** | 1 or more |
| `# Just A Heading` with no body | **0** | 1 |

### Where the bug lives

`_extract_sections` in `ingestion/chunking/structural_chunker.py`:

- Line 111 — `if heading_stack or current_section_lines:` gates content collection, so
  lines seen before the first heading are never appended to `current_section_lines`.
- Line 115 — `if current_section_lines and heading_stack:` gates the final section save,
  so even collected content is discarded when no heading was ever matched.

With no headings anywhere, both guards fail, `_extract_sections` returns `[]`, the loop in
`chunk()` never executes, and `chunk()` returns `[]`. Nothing raises and nothing is logged,
which is what makes the data loss silent.

**PLAN.md link:** https://github.com/Elias0305Ha/pathreview/blob/fix/149-structural-chunker-no-headings/PLAN.md

**Walkthrough video (recommended):** _(not recorded)_

**Blockers or open questions:**
The main decision I had to make this week was scope. The issue as filed is about
heading-less documents, and the failing test only covers that case. But the same two
guards also drop the preamble before a document's first heading, which is real data loss
from the same root cause — I confirmed it while reproducing. I decided to fix both, because
fixing only the reported case would leave the identical bug live four lines away, which is
harder to defend in review than a slightly larger PR. I will flag the wider scope at the
top of the PR description and keep the two changes in separate commits so a maintainer can
ask me to split them cheaply.

Still open going into Week 9: what a chunk with no heading should carry in its metadata.
`heading_path` is currently always a non-empty string, so I need to grep its consumers in
`rag/` and `api/` before deciding between an empty string and omitting the key. Setext
headings I am deliberately leaving out of scope; that is a separate feature, not this bug.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

_Written Thursday rather than Wednesday — I was a day late starting the build._

**Current progress:**

All five implementation sub-tasks from `PLAN.md` are done, in three commits.

First I settled the open question I carried out of Week 8. I grepped `heading_path` across
the repo: outside `structural_chunker.py` and its own test file, **nothing reads it** — not
`rag/`, not `api/`, not `agent/`. So the "stray ` > ` in a citation breadcrumb" risk I was
worried about does not exist, and I can write `heading_path: ""` with `heading_level: 0`
and keep the metadata shape uniform across every chunk. I also checked
`test_chunk_metadata_includes_heading_level`, which asserts `heading_level in [1, 2, 3]`:
its fixture document opens with `# Level 1` and has no preamble, so it never sees a level-0
chunk. That means I did not have to touch an existing assertion, which was the outcome I
wanted — quietly editing someone else's test to make my change pass is exactly what a
reviewer should catch.

Steps 1–4 (the fix) landed as two commits, split so the second is droppable. Tracing the
code before writing anything corrected an assumption in my plan: I had thought line 111 was
the preamble bug and line 115 the heading-less bug, one each. It is not that clean. For a
document with no headings, `heading_stack` and `current_section_lines` are *both* empty on
every line, so the line-111 guard drops the content before line 115 is ever reached — the
reported bug needs both guards relaxed. So the split is by symptom, not by line:

- `fix(ingestion): emit a chunk for documents with no headings` — relaxes both guards and
  moves section building into a new `_append_section` helper that skips whitespace-only
  content. This alone closes #149.
- `fix(ingestion): keep content that precedes the first heading` — routes the
  heading-boundary save through the same helper without the `heading_stack` gate, so a
  preamble becomes its own section.

I verified the second commit is genuinely separable: with only the first applied, preamble
lines are collected but still discarded at the heading boundary, so #149 stays fixed and
the preamble behaviour is unchanged. If a maintainer calls the wider scope creep, dropping
that commit costs nothing.

Fixing the empty-content case turned up a bug I had listed as an edge case but had not
realised was already live: a document of bare headings (`# A` / `## B` / `## C`) emits
chunks with **empty text** on `main` today, because the old inline save path appended
`"".strip()` without checking. `_append_section` guards it, so that is fixed as a side
effect of the refactor rather than as a separate change.

Step 5 (tests) is a third commit adding nine tests to `tests/unit/test_structural_chunker.py`,
matching the existing fixture and assertion style. I checked they are real regression tests
by restoring the pre-fix chunker and running them against it: eight of the nine fail. The
ninth, `test_content_after_last_heading_is_kept`, passes both before and after — it guards
existing behaviour rather than proving the fix, and I kept it for that reason.

**Pre-existing failures.** I recorded a baseline before changing anything, which turned out
to matter: `make test-unit` fails **53 tests across 16 files** on a clean checkout. Exactly
one of those, `test_document_with_no_headings`, is mine. `make check` is worse — ruff
reports 182 errors, black would reformat 52 files, and mypy stops early on missing stubs
for `jose`, `passlib` and `rank_bm25`. After my changes: 52 failures, 385 passing, up from
375. The only difference from baseline is my test flipping to pass. No new failures.

I deliberately did **not** run `make check`, because it invokes `black .`, which rewrites
all 52 files repo-wide. Burying a three-file fix in a repo-wide reformat is a good way to
get a PR ignored. I ran `black --check` on my two files instead, and formatted only the
code I added — the pre-existing `section_metadata.update({...})` blocks in the same file
are still non-compliant and I left them alone. Ruff on my two files reports the same 4
pre-existing errors as baseline (unused variables in tests I did not write); my additions
add none. I will document all of this in the PR description.

**Next steps:**
Open the draft PR, ask for peer review in Slack, and act on anything that comes back. Then
fill in Check-in 2 with the PR link, mark it ready for review, and submit the branch URL.

**Blockers:**
None on the code. The real risk is the peer review — it is the one item that depends on
someone else's schedule, and I am asking late in the week, so I am opening the PR before
polishing anything further rather than the other way round.

`make` is not installed in my Git Bash environment, so I ran the underlying commands from
`.venv/Scripts/` directly (`pytest tests/unit -m unit`, `ruff check`, `black --check`,
`mypy`) — same commands the Makefile targets wrap.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/684

**Branch:** `fix/149-structural-chunker-no-headings`

**What you built:**
`StructuralChunker` dropped every document that contained no ATX headings, returning zero
chunks so the document was embedded as nothing and never reached the RAG index — silently,
with no exception and no log line. I relaxed the two guards in `_extract_sections` that
assumed a heading had always been seen, so content lines are collected unconditionally and
the trailing section is flushed regardless of whether `heading_stack` is empty. Section
building moved into a new `_append_section` helper that skips whitespace-only content,
which keeps empty and whitespace-only input returning `[]` and also stops a document of
bare headings from emitting chunks with empty text — a bug that was already live on `main`.

**Tests added or updated:**
`tests/unit/test_structural_chunker.py` — nine new tests, no existing test modified.

Heading-less documents: `test_headingless_document_preserves_full_text`,
`test_headingless_document_metadata` (asserts `heading_path == ""` and `heading_level == 0`),
`test_headingless_document_preserves_source_metadata`, and
`test_large_headingless_document_is_sub_chunked`, which asserts the document really does
exceed `SECTION_TOKEN_LIMIT` before checking it splits into multiple non-empty chunks.

Preamble: `test_preamble_before_first_heading_is_kept` and `test_preamble_is_its_own_chunk`,
the latter checking the preamble is not silently merged into the first heading's section.

Edge cases from `PLAN.md`: `test_headings_only_document_emits_no_empty_chunks`,
`test_content_after_last_heading_is_kept`, and
`test_hash_without_space_is_treated_as_content` for `#NotAHeading`, which CommonMark does
not treat as a heading.

I checked these are genuine regression tests rather than tests that merely describe the new
code: I restored the pre-fix `_extract_sections` and ran them against it, and eight of the
nine fail. The ninth, `test_content_after_last_heading_is_kept`, passes both before and
after — it guards existing behaviour against regression, and I kept it knowingly.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Both boxes are checked in the sense the assignment defines for a codebase with documented
pre-existing failures: **my changes introduce no new failures.** Neither command passes
outright on this repository, and did not before I touched it. Measured against a baseline I
recorded on a clean checkout before making any changes:

| Check | Baseline | After this PR |
| --- | --- | --- |
| `pytest tests/unit -m unit` | 53 failed, 375 passed | 52 failed, 385 passed |
| `ruff check .` | 182 errors | 182 errors |
| `black --check .` | 52 files would reformat | 52 files would reformat |
| `mypy` (6 packages) | 5 errors, checking halted | 5 errors, checking halted |

Diffing the sorted failure lists from before and after gives exactly one line of
difference: `test_document_with_no_headings` flipping from fail to pass. The 52 remaining
failures are spread across sixteen files — `test_review_service.py` (13),
`test_bias_detector.py` (9), `test_pii_scrubber.py` (5) and others — none of them related
to chunking. The mypy errors are missing library stubs for `jose`, `passlib` and
`rank_bm25`, plus a numpy stub requiring Python 3.12. All of this is documented in the PR
description so a reviewer does not have to take my word for it.

I deliberately did not run `make check` itself, because it invokes `black .`, which rewrites
52 files repo-wide. Burying a three-file bugfix inside a repo-wide reformat would make the
PR much harder to review and much easier to ignore. I ran `black --check` on my two files
and formatted only the code I added; the pre-existing non-compliant blocks in the same file
are untouched. I said so in the PR and offered to reformat if the maintainer prefers it.

**Draft PR feedback received from:** none — requested in `#ai201-community-su26`, no
response before submission.

This is the part of the week I handled worst, and I would rather record that accurately than
dress it up. I started building on Thursday instead of Monday, which left no real window for
someone to read the PR before the deadline. Posting it in Slack on the last day and waiting
would have meant missing the submission, so I opened it as a ready PR rather than a draft
and shared the link in `#ai201-community-su26` anyway. Review can still arrive on an open PR
and I will respond to anything that comes back within the 48 hours `CONTRIBUTING.md` asks
for.

The lesson is specific rather than general: of everything due this week, peer review was the
only item that depended on another person's schedule, and it was therefore the only one I
could not compress by working harder on the last day. That is the item that should have gone
first. The code took a few hours; the review window needed days, and I spent them on
planning I had largely finished in Week 8.

**What I would still change.** Three things I chose not to do, recorded so they are
decisions rather than omissions. `chunk_index` is already wrong — it is set to `len(chunks)`
only on the non-sub-chunked branch, so indices collide once `SemanticChunker` contributes
chunks. My fix produces more chunks and makes it more visible, but it is a separate bug and
I offered to file it rather than quietly widening the PR. Setext headings are still
unsupported; after this fix those documents at least stop vanishing. And `# Just A Heading`
with no body still yields no chunk, which is arguably wrong but is a behaviour decision I
did not think was mine to make unilaterally.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in. I posted the PR link in `#ai201-community-su26` at the end of Week 9
asking for a peer read, and nothing came back before the Week 10 deadline. PR #684 on
`ascherj/pathreview` is still open with no comments from maintainers or classmates.

Two separate things are worth keeping distinct here, because only one of them is on me.
Maintainer review is not part of the Summer 2026 cohort, so its absence is expected and not
something I could have changed. **Peer** review was available, and I did not get it because
I asked on the last day. That one is mine, and I recorded it as such in Check-in 2 rather
than letting it blur into the first.

**How you responded:**
No changes to make. The branch stands as submitted in Week 9. If a comment arrives on the
open PR after this deadline I will still answer it inside the 48 hours `CONTRIBUTING.md`
asks for — the PR outliving the course is the point of contributing to a real repository.

The three follow-ups I flagged in Week 9 are the ones I would want a reviewer's opinion on,
and I am recording them here so they survive the course rather than dying with it: whether
fixing the preamble bug alongside the reported bug was scope creep (I kept it as a separate,
droppable commit precisely so a maintainer could say yes), whether the broken `chunk_index`
should be a separate issue I file, and whether `# Just A Heading` with no body ought to
produce a chunk.

---

### Reflection

**What was harder than you expected?**

Two things, and neither was the fix itself — the actual code change is about sixty lines and
took a few hours.

The first was that the repository was already broken. `pytest tests/unit -m unit` fails **53
tests across 16 files** on a clean checkout, `ruff` reports 182 errors, and `black` would
reformat 52 files. I had assumed "run the test suite" would give me a clean signal. It gave
me a wall of red that had nothing to do with me. The only reason this did not derail the
week is that I recorded a baseline *before* touching anything, which let me diff sorted
failure lists before and after and show exactly one line of difference:
`test_document_with_no_headings` flipping from fail to pass. Without that baseline I would
have been staring at 52 failures with no way to prove which were mine — and no way to make
the "no new failures" claim in my PR without a reviewer just having to trust me.

The second was that my plan was wrong about the mechanism, and I only found out by tracing
the code line by line before writing anything. I had a clean story going in: the guard on
line 111 causes the preamble bug, the guard on line 115 causes the heading-less bug, one
each. It is not that tidy. For a document with no headings, `heading_stack` and
`current_section_lines` are *both* empty on every line, so the first guard drops the content
before the second is ever reached — the reported bug needs both relaxed. That meant my
commit split had to be by symptom rather than by line. The plan was still worth writing; it
was just wrong in a way I would not have caught if I had started from the plan and typed.

**What did you learn about working in a large codebase?**

That most of the work is deciding what *not* to touch, and being able to defend each of
those decisions.

Three concrete cases from this fix. Before choosing what a chunk with no heading should
carry in its metadata, I grepped `heading_path` across the whole repo and found that outside
the chunker and its own test file, **nothing reads it** — not `rag/`, not `api/`, not
`agent/`. That single grep turned a risk I had written down in `PLAN.md` (a stray `" > "`
appearing in a citation breadcrumb) into a non-issue and let me pick the uniform
`heading_path: ""` / `heading_level: 0` shape with confidence. In my own project I would
have just picked one.

Second, I found that `chunk_index` is already wrong — it is set to `len(chunks)` only on the
non-sub-chunked branch, so indices collide once `SemanticChunker` contributes chunks. My fix
produces more chunks and makes it more visible. It was tempting to fix it while I was in
there. I left it and offered to file it separately, because a PR that fixes the bug it
claims to fix is reviewable and a PR that fixes three things is a negotiation.

Third, I did not run `make check`, even though the self-review checklist asks for it,
because it invokes `black .` and rewrites 52 files repo-wide. Burying a three-file bugfix
inside a repo-wide reformat is how you get a PR ignored. I ran `black --check` on my two
files instead, formatted only code I added, left the pre-existing non-compliant blocks in
the same file alone, and explained all of it in the PR description with an offer to reformat
if the maintainer prefers.

The through-line is that in my own project the cost of a change is whether it works. Here
the cost is also how much of someone else's attention it consumes, and how much unrelated
risk it drags along. That constraint shaped nearly every decision I made, and none of it
shows up in the diff.

**How did AI tools help — and where did they fall short?**

Most useful for orientation and for mechanical breadth. Finding my way around an unfamiliar
repository, tracing which callers reach `StructuralChunker` (only the `source_type ==
"readme"` path, which is what bounded my blast radius), and drafting nine tests in the
existing fixture and naming style all went faster with assistance than they would have
otherwise. Turning my reproduction notes into the structured `PLAN.md` sections was the same
kind of win — real, but essentially secretarial.

Where it fell short is more interesting, and it is the same place every time: **anything
that required checking a claim against the actual repository rather than against a plausible
model of it.**

The wrong-mechanism story above is the clearest case. "Line 111 is the preamble bug, line
115 is the heading-less bug" is a *tidy* reading of that code, and tidy readings are exactly
what you get from a confident assistant working from a quick scan. It survived into my
written plan and did not survive contact with the actual control flow. Tracing it myself is
what caught it.

The same pattern held for the pre-existing failures. Nothing prompts you that the suite is
already 53 tests red on a clean checkout. You have to think to record a baseline *before*
you start, because you suspect the ground might not be solid — and that suspicion came from
having been burned by assumptions elsewhere, not from the tooling.

And the same for verifying my tests were real. It is easy to generate nine tests that pass
against the code you just wrote; that proves nothing, because they were written by reading
that code. Restoring the pre-fix chunker and running them against it — finding that eight of
the nine fail, and that the ninth, `test_content_after_last_heading_is_kept`, passes both
before *and* after and is therefore a regression guard rather than proof of my fix — was a
step I had to decide to take. Nothing was going to suggest it to me.

So: very good at producing a plausible first draft of almost anything. The judgment about
which claims needed verifying, and the discipline to actually run the verification, stayed
with me. That was the genuinely useful lesson of the module.

**What would you do differently if you started over?**

Sequence the week by dependency instead of by difficulty.

Of everything due in Week 9, peer review was the **only** item that depended on another
person's schedule, and therefore the only one I could not compress by working harder on the
final day. It is the item that should have gone first. Instead I started building on
Thursday, opened the PR on the last day, posted in Slack, and got nothing — not because
anyone let me down, but because I gave them no window. The code took hours. The review
window needed days, and I spent those days re-polishing planning I had largely finished in
Week 8.

The corrected version is unglamorous: open a rough PR early, even an ugly one, purely so the
review clock starts, then keep improving it while people read. I optimised for the PR being
polished when it landed, when what actually mattered was it existing while someone still had
time to look at it.

Smaller change: I would file the `chunk_index` issue rather than only offering to. Offering
costs a maintainer a round trip to say yes; filing it costs them one click to close if they
disagree.

I would not change the issue selection. #149 was the right size — small enough to finish
properly, with a failure mode (silent data loss producing confident but ungrounded output)
that made the care worth spending.

**What are you most proud of from this module?**

That I verified my own tests instead of trusting them.

Nine new tests is easy to write and easy to overclaim. I restored the pre-fix
`_extract_sections` and ran them against it: eight fail, one passes. That ninth test,
`test_content_after_last_heading_is_kept`, guards existing behaviour rather than proving my
fix, and I kept it *and said so in the PR* instead of quietly counting nine.

The same instinct showed up in the thing I am second-most pleased with: I modified **zero**
existing tests. There is an existing assertion, `heading_level in [1, 2, 3]`, and my change
introduces level 0. Rather than adjust it, I checked whether it could actually see a level-0
chunk — its fixture opens with `# Level 1` and has no preamble, so it cannot. Editing
someone else's test to make your change pass is precisely what a reviewer should catch, and
I wanted the diff to contain nothing a reviewer would have to catch.

None of that is visible in the sixty lines of source I changed. But it is the part I would
want someone to look at if they were deciding whether to trust the fix.
