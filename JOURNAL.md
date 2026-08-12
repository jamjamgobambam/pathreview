## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/149]

**Issue title:** [Structural chunker silently drops documents that contain no headings
]

**Tier:** [#] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The function, StructuralChunker.chunk(), returns an empty list for any document without markdown headings, and it removes the entire document from the RAG index instead of being it chunked as a single block or falling back to another strategy. I will reproduce the error and then work with the test_document_with_no_headings in tests/unit/test_structural_chunker.py to show a successful fix

**Branch name:** [149-structural-chunker-silently-drops-documents-that-contain-no-headings]

**Setup confirmation:** [#] App runs locally at localhost:5173

**Cohort ledger:** [#] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [e422a33](https://github.com/folusho-adeyemi/pathreview/commit/e422a33bff82ece44e63c35db4ac256909524e05)

**Reproduction summary:**
Ran `StructuralChunker().chunk("This is a plain document with no headings at all. " * 20, {})` and it returned 0 chunks, and `pytest tests/unit/test_structural_chunker.py::TestStructuralChunker::test_document_with_no_headings` failed with `assert 0 >= 1`. Root cause: `_extract_sections()` only collects content and emits a section once a heading has been seen (`if heading_stack ...`), so a document with no headings never populates `heading_stack` and produces no sections. I documented this at the exact guard in `ingestion/chunking/structural_chunker.py`.

**PLAN.md link:** [PLAN.md](https://github.com/folusho-adeyemi/pathreview/blob/149-structural-chunker-silently-drops-documents-that-contain-no-headings/PLAN.md)

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
Need to confirm whether any downstream consumer of the RAG index assumes a non-empty `heading_path` before committing to `heading_path == ""` for heading-less documents (vs. falling back to the source name). This file also has pre-existing ruff/mypy failures that the Week 9 fix commit will need to clean up.
## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

Recorded a baseline of the repo's pre-existing failures before touching anything (`make test-unit`: 53 failed / 375 passed; `make lint`: 182 errors; `make typecheck`: 5 errors), so I could prove my change introduces no new ones.

PLAN.md steps 1–3 are done:

1. **Content collection fixed** — `_extract_sections()` now appends every regular content line instead of gating on `if heading_stack or current_section_lines`.
2. **Section emission fixed** — pulled the duplicated section-dict construction into a new `_build_section()` helper that returns `None` when the collected lines hold no content, and routed both the mid-loop and final emission branches through it. Content outside any heading gets `heading_path == ""` and `heading_level == 0`.
3. **Large-doc path verified** — a 1261-token heading-less document is sub-chunked into 3 chunks through the existing `chunk()` → `SemanticChunker` branch with metadata preserved. No new code needed, as the plan predicted.

I also closed out the Week 8 blocker: I grepped `heading_path`/`heading_level` across `api/`, `core/`, `ingestion/`, `rag/`, `agent/`, `safety/` and `frontend/src/`, and **no code consumes either field** — only a docstring on `BaseChunker.chunk()` mentions them ("heading_path if applicable"). So `heading_path == ""` is safe and the `metadata["source"]` fallback I was considering isn't needed.

Fix committed as `bb391e9` — `fix(ingestion): emit sections for markdown without headings`.

**Next steps:**

PLAN.md steps 4–5: add unit tests for the heading-less, large-heading-less and preamble cases, then re-run `make check` and `make test-unit` against my baseline to confirm no new failures. Then rename the branch to the convention and open the PR.

**Blockers:**

None blocking. Two pre-existing tooling problems I have to work around rather than fix:

- The pre-commit mypy hook has no `tests/` exclude, so it flags all **413** unannotated test functions across all **19** files in `tests/unit/` — while `make typecheck` deliberately scopes to source directories only. I'll match the suite's convention and leave test functions unannotated.
- The pinned pre-commit black (24.1.0) and the black installed by `pip install -e ".[dev]"` (26.5.1) format the same pre-existing code differently and each reverts the other.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/927

**Branch:** `fix/149-structural-chunker-drops-heading-less-docs`

(Renamed from `149-structural-chunker-silently-drops-documents-that-contain-no-headings`, which didn't follow the `<type>/<issue-number>-<short-description>` convention in CONTRIBUTING.md. The earlier PR #242 from the old branch name has been filled in for the record and closed, pointing at #927.)

**What you built:**

`StructuralChunker` silently dropped every markdown document with no headings — `_extract_sections()` only collected content and emitted sections once a heading had been seen, so a heading-less document produced zero sections and `chunk()` returned `[]`. Since `StrategySelector` sends all `readme` documents to this chunker, a heading-less README never entered the RAG index and nothing raised an error. The fix collects content unconditionally and emits a section whenever the collected lines hold content, labelling content outside any heading with an empty breadcrumb and level 0; this also recovers preamble text before the first heading, which was being discarded by the same guard.

**Tests added or updated:**

`tests/unit/test_structural_chunker.py` — four new tests plus one strengthened:

- `test_heading_less_document_has_empty_heading_path` — the `heading_path == ""` / `heading_level == 0` contract.
- `test_heading_less_document_preserves_source_metadata` — caller metadata survives the heading-less path.
- `test_large_heading_less_document_sub_chunked` — a heading-less doc over `SECTION_TOKEN_LIMIT` is sub-chunked via `SemanticChunker` instead of emitted as one oversized chunk.
- `test_preamble_before_first_heading_preserved` — content before the first heading is retained as a leading chunk.
- `test_document_with_no_headings` (the issue's own test) — now also asserts the document text survives, not just the chunk count.

All five fail against the pre-fix chunker and pass against the fix, verified by restoring `main`'s copy of the file and re-running the suite (5 failed / 14 passed → 19 passed). I also completed two assertions in `test_heading_path_format` and `test_heading_path_breadcrumb` that were computed but never checked, so those tests now verify the breadcrumb they describe.

**Self-review confirmation:** [#] make check passes  [#] make test-unit passes

Both in the "introduces no new failures" sense the assignment defines, against the baseline I recorded on `main`:

| Check | Baseline on `main` | With this branch | Delta |
| --- | --- | --- | --- |
| `make test-unit` | 53 failed, 375 passed | 52 failed, 380 passed | 0 new failures; fixes `test_document_with_no_headings`; +4 new tests |
| `make lint` | 182 errors | 178 errors | 0 new errors; clears the 4 in the files I touched |
| `make typecheck` | 5 errors | 5 errors | byte-identical output |

Both files I touched are individually clean: `ruff check ingestion/chunking/structural_chunker.py tests/unit/test_structural_chunker.py` → `All checks passed!`. The 52 remaining test failures are pre-existing and in unrelated modules; the 5 typecheck errors are missing third-party stubs plus a numpy stub syntax error that halts checking before any project file is reached. `make test-integration` was not run — it needs Docker services I don't have available, and this change is a pure-function chunker with no I/O.

**Draft PR feedback received from:** none — I did not get a peer review on a draft before finalising. #242 was open all week from the Week 8 reproduction but attracted no comments or reviews.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [#] No — still awaiting review

**Summary of feedback:**

No review came in. [PR #927](https://github.com/ascherj/pathreview/pull/927) has been open and marked ready for review since Week 9 with `reviewDecision: REVIEW_REQUIRED`, zero reviews, zero comments and zero inline threads. The earlier [#242](https://github.com/ascherj/pathreview/pull/242), open from Week 8, also drew nothing before I closed it. No CI checks run on this fork's branches, so I had no automated feedback either.

Part of this is my own doing and part is the shape of the assignment. Mine: #242 sat open for two weeks with a completely empty PR template — nobody could have reviewed that even if they wanted to, and I never actually asked anyone in Slack. I treated "a PR exists" as equivalent to "I requested review," which it isn't. The structural part: issue #149 has **24 comments, almost all of them people claiming the issue** ("I would like to work on this issue"), spread across several cohorts. A maintainer facing 24 parallel attempts at one bug is not going to review each one.

**How you responded:**

With no external feedback to respond to, I self-reviewed against the two sources of truth I could actually check — `docs/CONTRIBUTING.md` and the repo's own tooling — and that surfaced real problems:

- My branch name `149-structural-chunker-silently-drops-documents-that-contain-no-headings` violated the required `<type>/<issue-number>-<short-description>` format. Renamed to `fix/149-structural-chunker-drops-heading-less-docs`, superseded #242 with #927, and filled in #242's description before closing it so it isn't an empty stub in the record.
- Two existing tests, `test_heading_path_format` and `test_heading_path_breadcrumb`, computed a `found_path` boolean and then never asserted it — ruff caught them as `F841` unused variables. They passed while proving nothing. I completed both assertions.
- I re-derived a baseline of pre-existing failures on `main` and confirmed my branch introduced none, rather than asserting "checks pass" against a repo where they don't.

I also read the other claimants' stated approaches on the issue as a substitute for peer review. [`akshaypsharma-AIA`](https://github.com/ascherj/pathreview/issues/149) planned to "make `chunk()` fall back to the existing SemanticChunker when no headings are found — same pattern the file already uses for oversized sections." That's a reasonable-sounding plan and it's the one I rejected; see the reflection below.

---

### Reflection

**What was harder than you expected?**

Everything except the fix. The actual change is small — stop gating content collection on `heading_stack`, and emit a section whenever the collected lines hold content. I understood the root cause in Week 8. Weeks 9 and 10 went almost entirely into work that isn't "writing the fix."

The specific thing I did not anticipate: **`make check` and `make test-unit` both fail on a clean `main`.** 182 ruff errors, 5 mypy errors, and 53 failing unit tests, none of them related to #149. The assignment's requirement that "checks pass" is undefinable in that state, so before touching anything I had to snapshot `main`'s output to a file and diff against it afterwards to prove my delta was 0 new failures / 4 lint errors cleared / 1 test fixed. That baseline turned out to be the most valuable thing I produced all module, and it wasn't in my PLAN.md.

Then the tooling actively fought me. My first commit was rejected by the pre-commit black hook. My second was rejected by the pre-commit mypy hook — **for 20 pre-existing errors in code I hadn't written.** Chasing that down produced two findings:

- The pre-commit mypy hook has no `tests/` exclude, while `make typecheck` deliberately scopes to `api/ core/ ingestion/ rag/ agent/ safety/`. So the enforced gate and the documented command disagree, and the hook flags **all 413 test functions across all 19 files** in `tests/unit/` as untyped. Not one test file in the repo annotates.
- The pinned hook uses black 24.1.0 while `pip install -e ".[dev]"` installs black 26.5.1, and the two format the same pre-existing string concatenation differently — each one reverts the other's output, forever.

Neither is mine to fix, and that was the genuinely hard part: **deciding what not to fix.** I could have annotated all 20 test functions in my file and gotten a green hook, but that would have made my file the only annotated test file in the repo — satisfying a misconfigured tool by breaking the convention every other file follows. I chose to match the suite, commit with `SKIP=mypy`, and document the reasoning in the PR. I'm still not certain that was right, and it's the first thing I'd want a reviewer's opinion on. Restraint under ambiguity is harder than fixing things, and nothing in the module trained me for it.

The last surprise was that a Week 7 decision cost me in Week 9. I named the branch before reading `CONTRIBUTING.md`. By the time I noticed, #242 existed and my Week 8 journal had a hardcoded link to commit `e422a33` — so rewriting history to fix the one non-conventional commit message (`396bdf4 "started working on issue 149"`) would have changed every SHA after it and broken my own submitted deliverable. I had to leave it and disclose it in the PR. A two-minute read in Week 7 would have removed all of that.

**What did you learn about working in a large codebase?**

**Read the contract, not just the code.** My PLAN.md flagged a real risk: if heading-less content gets `heading_path == ""`, does anything downstream break? My plan hedged with a fallback to `metadata["source"]`. The answer came from two places — a grep for `heading_path`/`heading_level` across `api/`, `core/`, `ingestion/`, `rag/`, `agent/`, `safety/` and `frontend/src/` returned **no consumers at all**, and the docstring on `BaseChunker.chunk()` already said `heading_path if applicable`. The design had anticipated optional heading paths from the start. The empty string wasn't a compromise, it was the documented case, and the fallback I'd planned would have invented behaviour nobody asked for. In my own projects I hold that context in my head; here I had to go find it, and the docstring was worth more than the code.

**The blast radius is never just the lines you touch.** Removing the guard doesn't only fix heading-less documents — it also recovers preamble text before the first heading, which the same guard was silently discarding. That's a second bug fixed for free, but it *changes chunk counts* for any document with a preamble. So I had to go read all 15 existing tests looking for anything pinning an exact count. Nothing did (they use `>=` or iterate), but I couldn't know that without checking, and a reviewer would rightly have asked.

**Fixing the root cause is sometimes less work than the workaround.** The alternative approach another claimant proposed — have `chunk()` fall back to `SemanticChunker` when no headings are found — would pass the failing test. But it adds a second code path to maintain, leaves `_extract_sections()` still silently lossy, does nothing about the preamble bug, and produces chunks with no `heading_path` key at all rather than an empty one. Fixing the guard where it actually lives was fewer lines and strictly more correct. The tempting fix and the right fix pointed in different directions, and the test suite alone couldn't tell me which was which.

**Duplicated logic is where bugs live.** The buggy emission logic existed twice — once mid-loop, once after it — with subtly different guards. That duplication is *why* the bug was possible. Extracting `_build_section()` means the two call sites can't drift again. The refactor wasn't cosmetic; it was the actual fix for the class of bug.

**A passing test suite is not evidence.** `test_document_with_no_headings` only asserted `len(result) >= 1`, and two other tests asserted nothing at all. This suite would have stayed green through several plausible wrong fixes.

**How did AI tools help — and where did they fall short?**

Most useful for mechanical breadth. Sweeping six directories plus the frontend for `heading_path` consumers, quantifying that 413 test functions across 19 files are unannotated, diffing my check output against the baseline, and drafting Google-style docstrings and Conventional Commit bodies in the repo's voice — all fast, all things I'd have done slowly and less thoroughly by hand. It was also good at scaffolding the commit and PR prose once I'd decided what to say.

Where it fell short, concretely:

- **It couldn't make the judgment calls, and those were the whole game.** Annotate the tests or match the convention? Run `make format` and reformat 52 unrelated files, or leave the skew? Rewrite history for one bad commit message and break my own journal link, or disclose it? Each needed a cost/benefit read on *this* project's history and *this* assignment's constraints. AI could lay out the tradeoff cleanly; it could not own the consequence.
- **My AI-assisted plan contained a confident wrong recommendation.** PLAN.md proposed the `metadata["source"]` fallback for `heading_path`. It sounded prudent and was unnecessary — the codebase already answered the question. Plausible-sounding hedges are exactly what I'd have accepted if I hadn't gone and checked.
- **It optimises for the passing test, not the right design.** Prompted at the failing test, the obvious suggestion is the `SemanticChunker` fallback — one path, test goes green. Getting to "fix the guard, extract the helper, and you also fix the preamble bug" required me to ask *why the bug was possible*, which is a different question from *how do I make this test pass*. The other claimant's public plan suggests I'm not the only one the easy answer would have caught.
- **It cannot give you confidence, only output.** The single most valuable step I took was `git checkout main -- ingestion/chunking/structural_chunker.py`, re-running the suite to watch my 5 new tests fail (5 failed / 14 passed), then restoring the fix and watching them pass (19 passed). No amount of AI review substitutes for deliberately trying to falsify your own work. Tests that have never been seen to fail are decoration.

The pattern: AI compressed the hours of searching, reading and drafting. It did not reduce the thinking, and when I let it think for me — the `metadata["source"]` hedge — it was wrong in a way that read as careful.

**What would you do differently if you started over?**

1. **Read `CONTRIBUTING.md` in Week 7, before naming anything.** One read would have prevented the wrong branch name, the rename, the superseded PR, and the unfixable commit message. Cheapest possible fix, highest cost avoided.
2. **Baseline the repo in Week 7.** Recording `main`'s 182 lint / 5 type / 53 test failures on day one would have told me immediately that "make check passes" needs redefining, instead of discovering it under deadline in Week 9.
3. **Open a genuinely reviewable draft PR in Week 8 and actually ask a human.** #242 sat open for two weeks with an empty template while I assumed it counted as requesting review. Had I pushed the failing test with a filled-in description and posted it in Slack with a specific question — *"should test functions be annotated, given the hook and `make typecheck` disagree?"* — I'd have gotten the one input I actually wanted. Requesting review is an action, not a state.
4. **Write the strengthened assertions before the fix, not after.** I reproduced the bug first, correctly, but the sharper assertions (`heading_path == ""`, text survives, preamble retained) were written after the code was green — so I had to reconstruct falsifiability by checking out `main`'s file. Test-first would have given it to me for free.
5. **Weigh contention when choosing the issue.** 24 people claimed #149. I picked it in Week 7 on technical grounds — small, well-scoped, has a failing test — without noticing I was queueing behind two dozen others for one maintainer's attention. A quieter issue would have cost the same effort and had a real chance of the review that is the actual point of the exercise.

**What are you most proud of from this module?**

Deliberately trying to prove my own work wrong. Restoring `main`'s copy of the chunker, re-running the suite to confirm all five new tests genuinely fail (5 failed / 14 passed) and then pass against the fix (19 passed), was nobody's requirement — the tests were already green and I could have shipped. But green tests on a suite that contained two assertions that never ran had stopped being convincing to me, and I wanted evidence rather than a clean terminal.

The same instinct produced the two things I'd actually defend in this PR: the baseline that separates my 0 new failures from the repo's 52 pre-existing ones, and the choice to fix the guard at its root — catching the preamble bug that nobody reported — instead of bolting on the `SemanticChunker` fallback that would have turned the test green and left the real defect in place.

The PR may never be reviewed. It's one issue among 24 claims on a course fork. But I know exactly what it does, exactly what it doesn't, and exactly which of my decisions a reviewer should push back on — and I wrote those down in the PR rather than hoping nobody looked. That feels like the transferable part.
