# PathReview Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker is the piece of the RAG evaluator that decides how much of the generated feedback is actually backed by the retrieved context. Before it can score anything, it stitches all the context chunks together into one string. The bug is in how it pulls the text out of each chunk. It uses `chunk.get("text", "")`, which people usually assume hands back an empty string when there is no text. That default only kicks in when the key is missing entirely. If a chunk comes through as `{"text": None}`, the key is present, so `.get` happily returns `None`, and the `" ".join(...)` right after it blows up with a TypeError. A good fix makes the checker treat a missing value and a `None` value the same way, so a single malformed chunk no longer takes down the whole evaluation, and I want to add a regression test so this exact case stays covered.

**Branch name:** fix/153-faithfulness-none-text-chunk

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### "Is this right for me?" checklist reasoning

I spent some time reading the actual code before committing to this one, and that changed how confident I felt. The whole thing lives in a single file, `rag/evaluator/faithfulness_checker.py`, and the failure is a one line assumption about how `dict.get` behaves. That felt honest for a first contribution. I am not touching the database, the API routes, or the frontend, so the blast radius is small and I can reason about the fix without holding the entire system in my head.

What sold me was that there is already a test file at `tests/unit/test_faithfulness_checker.py` and the issue even points to a named test for this case. That means I can reproduce the crash quickly, watch it fail, and then watch it pass, which is the kind of tight feedback loop I wanted while I am still learning the repo. I could also explain the root cause out loud, which the checklist treats as a real signal that you understand the problem rather than just pattern matching a fix.

The one thing I want to stay careful about is scope creep. It would be tempting to start cleaning up the claim extraction logic while I am in there, but that is not what the issue asks for, so I am going to keep the change focused on the None handling and the test that proves it.

## Week 8 — Reproduction & solution planning
**Reproduction commit link:** [https://github.com/Yd025/ai201-pathreview/commit/a56837386879814f18742d96974c63b0fb1efcf1](https://github.com/Yd025/ai201-pathreview/commit/a56837386879814f18742d96974c63b0fb1efcf1)

**Reproduction summary:**
I reproduced the crash two ways. First I called the checker directly with `FaithfulnessChecker().check('Knows Python.', [{'text': None}])` and watched it raise `TypeError: sequence item 0: expected str instance, NoneType found`. Then I ran the existing unit test `test_none_context_chunk_text`, which fails on the same line, `rag/evaluator/faithfulness_checker.py:34`, so I know exactly where the bug lives and I have a test that will flip to green once I fix it.

**PLAN.md link:** https://github.com/Yd025/ai201-pathreview/blob/fix/153-faithfulness-none-text-chunk/PLAN.md

**Blockers or open questions:**
My one open question going into Week 9 is whether null text should ever reach the evaluator at all, or whether something further up in the retriever is letting bad chunks through. My fix makes the checker resilient either way, but I want to grep the retriever and generator before I decide the null guard is the whole story.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have the fix drafted locally and the null test passing. Before I touched anything I ran the full unit suite and wrote down the baseline, which was 53 failing tests across the repo that have nothing to do with my issue. The change I am leaning toward is swapping the context concatenation in `faithfulness_checker.py` from `chunk.get("text", "")` to `chunk.get("text") or ""`, which lines up with sub-tasks 1 through 3 of my PLAN. With that in place `test_none_context_chunk_text` goes green for me, and I am sketching two more regression tests, one for a null chunk mixed in with a good chunk and one for an all null context list, before I commit the code and open the PR.

**Next steps:**
I want to close the loop on my open question from Week 8 and grep the retriever and generator to see where a null text value could come from, then finish the PR description and run make check one more time before I mark it ready.

**Blockers:**
None that are stopping me. The wrinkle I hit was that three other tests in the same file fail because of a separate scoring bug, so I had to be careful that my new mixed chunk test asserted on not crashing rather than on a specific score, since the score path is broken for a different reason.

---

### Check-in 2 (end of week)

**PR link:** [https://github.com/ascherj/pathreview/pull/334](https://github.com/ascherj/pathreview/pull/334)

**Branch:** `fix/153-faithfulness-none-text-chunk`

**What you built:**
The faithfulness checker used to crash with a TypeError whenever a retrieved context chunk carried `text: None`, because `dict.get` returns the real `None` value rather than the empty string default when the key is present. I changed the read to `chunk.get("text") or ""` so a null value collapses to an empty string, which means one malformed chunk no longer takes down the whole evaluation.

**Tests added or updated:**
I touched `tests/unit/test_faithfulness_checker.py`. The pre-existing `test_none_context_chunk_text` goes from failing to passing, and I added `test_none_chunk_mixed_with_valid_chunk` and `test_all_none_context_chunks` to cover a null chunk alongside a good one and a context list that is entirely null.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

_Note on the boxes above:_ the repo has documented pre-existing failures that are unrelated to my issue. I recorded the baseline before starting (53 failing unit tests, plus pre-existing ruff and black findings in files I did not write). After my change the unit suite goes from 53 failing to 52 failing with three more passing, so I fixed one test and added two, and introduced no new failures. My own two changed files are clean under ruff, black, and mypy. In line with the assignment guidance, I am reading "passes" as "my changes introduce no new failures," not "the entire codebase is green."

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No maintainer or peer review has come in on the pull request itself, which is expected for Summer 2026 since PR review is not a feature this term. The checkbox above stays at No for that reason. I want to be careful about the distinction here, because I did receive feedback this module, but it was the grading feedback on my Week 9 submission rather than a comment on the open PR. I have documented that separately below so the two are not confused.

**How you responded:**
There is nothing to respond to on the PR thread yet. If a maintainer does comment before the module closes, I will read it in full before replying, thank them, make the changes I agree with, and explain my reasoning on anything I want to discuss rather than silently closing the thread.

---

### Week 9 grading feedback (separate from PR review)

This is feedback from the Week 9 grade, not from a reviewer on the PR. I am recording it here because it was genuinely useful and I acted on it.

**What the grader said:**
They were positive about the overall structure, the clean separation into subsystems, the use of base classes like `BaseTool` and `BaseParser`, and the consistent structured logging with structlog. The two areas they pushed on were, first, that the backend where most of the complex logic lives was thin on unit tests compared to the frontend, and they named `SemanticChunker`, `SkillExtractor`, `ReadmeScorer`, and the `Orchestrator` as pure-logic modules with edge cases that deserve dedicated coverage. Second, they flagged that `review_service.py` has placeholder functions like `_run_agent_orchestration` and `_run_rag_retrieval_generation` that return hardcoded dictionaries, and suggested marking stubs clearly with TODO comments or `NotImplementedError` so collaborators can tell scaffolding apart from finished work.

**How I responded:**
On the testing point, I looked at the four modules they named and found that the orchestrator was the one genuinely missing a test file, so I added `tests/unit/test_orchestrator.py` covering the pure planning logic in `_build_plan`. Those seven tests exercise the edge cases the grader was pointing at, an empty profile producing no plan, a username with no repos correctly skipping the GitHub tool, only the first repo being planned when several exist, and the market analyzer only being scheduled when there is other work to do. They need no database, Redis, or network, which was exactly the grader's point about pure-logic modules being the highest leverage place to build the testing habit.

On the placeholder point, I did not raise `NotImplementedError`, because these stubs are actually called in the mock processing path and raising would break the running app. Instead I took the grader's other suggestion and made the stubs unmistakable. I rewrote the comments in `review_service.py` to a single greppable `TODO(stub)` marker and added a short STUB note to the docstrings of `_run_agent_orchestration` and `_run_rag_retrieval_generation` saying plainly that they return mock data and are scaffolding, not finished work. Now a collaborator can search for `TODO(stub)` and see every unfinished path in one pass.

---

### Reflection

**What was harder than you expected?**
The actual one line fix was easy. The hard part was that a completely separate bug was leaking into the same test file and muddying my signal. When I ran `test_faithfulness_checker.py`, four tests failed, and I assumed at first that they were all mine. Three of them turned out to belong to a different issue, a scoring problem where supported claims come back as 0.0, which lives in the same file but has nothing to do with the None crash I was fixing. Untangling that took real work. I had to read each failing test, run them one at a time, and trace why they failed before I could say with confidence that only `test_none_context_chunk_text` was mine. It got trickier when I wrote my own regression test for a null chunk sitting next to a valid chunk, because I instinctively wanted to assert that the valid chunk produced a positive score, and that assertion kept failing for the same unrelated reason. I had to step back and make my test assert only on what my change actually guarantees, which is that the checker runs to a valid score instead of crashing. Learning to prove a failure was not mine, and to write a test that stayed inside the boundary of my own change, was the part that stretched me.

**What did you learn about working in a large codebase?**
The biggest lesson was that in a shared codebase, failures are not automatically yours. On my own projects a red test suite means I broke something. Here a red suite was the normal starting state, and the skill was separating my signal from the surrounding noise. I learned to record the baseline before I touched anything, 53 failing unit tests across the repo, so that afterward I could point to a concrete before and after and show my change made things better and not worse. I also learned to stay a guest in someone else's house. It would have felt productive to fix those three scoring tests or to reformat the file while I was in there, but that would have buried a one line fix under a large unrelated diff and made the reviewer's job worse. Keeping the change to exactly one issue was a discipline, not a shortcut. The grading feedback later reinforced the same idea from the other direction, that the highest leverage work is often quiet groundwork like tests and clear stub markers rather than more features.

**How did AI tools help — and where did they fall short?**
AI was most useful for orientation and triage. It helped me trace where the bug lived, understand why `dict.get` returns None rather than the default when the key is present, and quickly recognize that the three other failing tests were about scoring and not about my crash. It was also fast at scaffolding the new orchestrator tests once I had decided what to cover. Where it fell short was judgment about scope and process. It could suggest a fix or a test instantly, but deciding that the scoring failures were out of scope, deciding to mark the stubs with a TODO rather than raise an error that would break the mock path, and deciding whether bypassing pre-commit hooks that fail on pre-existing issues was honest were all calls I had to make and be able to defend. The mechanical part was cheap. Knowing what not to do was the actual work.

**What would you do differently if you started over?**
I would run the full test suite on a clean checkout before I picked my issue, not after. Seeing up front that the file I was about to touch already had three unrelated failing tests would have set my expectations correctly and saved me the early worry that I had broken something. I would also open the draft PR earlier in the week instead of getting the fix perfect first, since the whole point of a draft is to get eyes on it while there is still time to change course. And I would start writing tests alongside the code from the very first day rather than treating them as the last step, which is exactly the habit the grading feedback pointed me toward.

**What are you most proud of from this module?**
I am most proud of the scope discipline. The moment where I could have drifted was when I found those three extra failing tests, because fixing them would have felt like doing more good work. Instead I proved they belonged to a different issue, left them alone, documented them in the PR so the reviewer would not be surprised, and made my own test assert only on what my fix actually promises. Then when the grading feedback came in, I was able to act on it in the same spirit, adding real test coverage where it was genuinely missing and making the placeholder code honest about itself, without sprawling outside what each change was meant to do. The fix is one line, but I can explain every decision around it, and that feels like a real contribution rather than a drive by.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review has come in yet. I will update this section if a maintainer or peer comments on the PR before the module closes. For now the PR is open and passing the checks that are actually mine to own.

**How you responded:**
Nothing to respond to yet. If feedback arrives I plan to read it fully before replying, thank the reviewer, make the changes I agree with, and explain my reasoning on anything I want to push back on rather than just silently closing the thread.

---

### Reflection

**What was harder than you expected?**
The actual one line fix was easy. The hard part was that a completely separate bug was leaking into the same test file and muddying my signal. When I ran `test_faithfulness_checker.py`, four tests failed, and I assumed at first that they were all mine. Three of them turned out to be a different issue, a scoring problem where supported claims come back as 0.0, which lives in the same file but has nothing to do with the None crash I was fixing. Untangling that took real work. I had to read each failing test, run them one at a time, and trace why they failed before I could say with confidence that only `test_none_context_chunk_text` belonged to issue #153. It got even trickier when I wrote my own regression test for a null chunk sitting next to a valid chunk, because I instinctively wanted to assert that the valid chunk produced a positive score, and that assertion kept failing. The reason was that same #152 scoring bug, not my fix. I had to step back and make my test assert only on what my change actually guarantees, which is that the checker runs to a valid score instead of crashing on the join. Learning to prove that a failure was not mine, and to write a test that stayed inside the boundary of my own change, was the part that stretched me.

**What did you learn about working in a large codebase?**
The biggest lesson was that in a shared codebase, failures are not automatically yours. On my own projects a red test suite means I broke something. Here a red suite was the normal starting state, and the skill was separating my signal from the surrounding noise. I learned to record the baseline before I touched anything, 53 failing unit tests across the repo, so that afterward I could point to a concrete before and after and show that I fixed one and added two without introducing anything new. I also learned to stay a guest in someone else's house. It would have felt productive to fix those three #152 tests while I was in the file, but that would have blurred my PR into two unrelated changes and made the reviewer's job harder. Keeping the change to exactly one issue was a discipline, not a shortcut.

**How did AI tools help — and where did they fall short?**
AI was most useful for orientation and triage. It helped me trace where the bug lived, understand why `dict.get` returns None rather than the default when the key is present, and quickly recognize that the three other failing tests were about scoring and not about my crash. Where it fell short was the judgment calls. Deciding that the #152 failures were out of scope, deciding how to word my test so it did not depend on a broken code path, and deciding whether bypassing the pre-commit hooks that fail on pre-existing issues was honest were all calls I had to make and be able to defend. The mechanical part was cheap. Knowing what not to do was the actual work.

**What would you do differently if you started over?**
I would run the full test suite on a clean checkout before I picked my issue, not after. If I had seen up front that the file I was about to touch already had three unrelated failing tests, I would have understood the terrain much sooner and spent less time worried that I had broken something. I would also have opened the draft PR earlier in the week rather than polishing the fix first, since the point of a draft is to get eyes on it while there is still time to change direction.

**What are you most proud of from this module?**
I am most proud of the scope discipline. The moment where I could have drifted was when I found those three extra failing tests, because fixing them would have felt like doing more good work. Instead I proved they belonged to a different issue, left them alone, documented them in the PR so the reviewer would not be surprised, and made my own test assert only on what my fix actually promises. The change is one line, but I can explain every decision around it, and that feels like a genuine contribution rather than a drive by.

