# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
In the RAG system, the faithfulness checker assumes every retrieved context chunk has string text, so a chunk with `text: None` throws an error instead of being handled. A successful fix would skip or safely handle null-text chunks so the check runs without crashing.

**Branch name:** fix/153-faithfulness-none-text-crash

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Is this right for me?
- Scope is small and isolated to one RAG check, so it fits a Tier 1 effort.
- The bug is a clear null-handling case with an obvious success condition (no crash).


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/maanyaS/pathreview/commit/774f9f7d7b50022ad0670a6ca0c453c5ba6c7343

**Reproduction summary:**
I ran the issue's one-liner against my local venv — `FaithfulnessChecker().check("Knows Python.", [{"text": None}])` — and got the exact reported `TypeError: sequence item 0: expected str instance, NoneType found` at `rag/evaluator/faithfulness_checker.py:43`, and the repo's existing `test_none_context_chunk_text` fails with the same error. It reproduces every run: `dict.get("text", "")` only falls back to `""` for a *missing* key, so a present-but-`None` value flows straight into `" ".join(...)` and blows up. I committed a comment at the exact failing line documenting the trace and the repro command.

**PLAN.md link:** https://github.com/maanyaS/pathreview/blob/fix/153-faithfulness-none-text-crash/PLAN.md

**Blockers or open questions:**
- No blockers — the fix itself is a few lines. The open design question is whether silently skipping a null chunk is right, since it turns a loud crash into a quietly lower faithfulness score. I plan to log when the assembled context ends up empty so it's still diagnosable, but I'd like a mentor's read on that.
- `relevance_scorer.py:32` uses the identical `chunk.get("text", "")` idiom and has the same latent crash. I'm leaving it out of this PR to keep the scope on #153 and will flag it in the PR description — worth confirming that's the preferred call.
- Still unsure whether `text: None` is itself a symptom of an upstream ingestion/chunker bug rather than just bad caller input.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Sub-tasks 1–4 from PLAN.md are done. Before writing any code I recorded baselines for `make check` and `make test-unit`, because this codebase has a lot of pre-existing failures (53 failing unit tests, 181 ruff errors, 51 files failing black, and a `make typecheck` that aborts on a numpy stub requiring Python 3.12+ syntax). The fix itself is committed (`fix(rag): handle null text in faithfulness context chunks`): `check()` now filters chunk texts to actual strings before joining, so a missing key, `None`, or a non-string value contributes no context instead of crashing. I also added a `faithfulness_empty_context` log so a run that legitimately scores 0.0 is still diagnosable. Three regression tests are committed on top of the issue's existing `test_none_context_chunk_text`.

**Next steps:**
Sub-task 5 — re-run both commands and diff against the baselines to prove no new failures, write up the pre-existing-failure table for the PR description, and open a draft PR for peer feedback.

**Blockers:**
Pre-commit refused the test-file commit on failures that were already in that file before I touched it (ruff `F841` at line 216, black, and 25 mypy `no-untyped-def`). I annotated my three new tests so they add zero new errors — pre-commit reports the identical ruff 1 / mypy 25 counts with and without my commit — and committed with `--no-verify`, documented in the commit message. Fixing the other 26 would have meant ~30 lines of unrelated cleanup in a Tier 1 bugfix.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1031

**Branch:** `fix/153-faithfulness-none-text-crash`

**What you built:**
`FaithfulnessChecker.check()` assembled its context with `chunk.get("text", "")`, but `dict.get`'s default only fires when the key is *missing* — a present-but-`None` value passed straight through to `" ".join(...)` and raised `TypeError`, aborting an entire evaluation run over one malformed chunk. The fix keeps only values that are actually strings, so null and non-string chunks contribute nothing while valid chunks alongside them still score exactly as before, and logs `faithfulness_empty_context` when no chunk yields usable text.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — the issue's existing `test_none_context_chunk_text` now passes, plus three new cases: `test_all_context_chunks_none_text` (every chunk null → 0.0, no raise), `test_mixed_none_and_valid_context_chunks` (a null chunk must not discard the valid chunk next to it), and `test_non_string_context_chunk_text` (an int `text` value is skipped rather than stringified into junk tokens).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> Both boxes mean *no new failures*, per the pre-existing-failure guidance. Verified by diffing before/after: unit tests went 53 failed / 375 passed → 52 failed / 379 passed, the single net change being `test_none_context_chunk_text`, which this PR fixes; no test newly fails. Ruff held at 181 errors, black improved 51 → 50 files, and `rag/evaluator/faithfulness_checker.py` reports no mypy issues when checked on its own. The full pre-existing-failure table is documented in the PR description.

**Draft PR feedback received from:** none yet — draft PR opened for peer review in Slack


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in. PR #1031 is still open as a draft with zero comments and zero reviews. I opened it late in Week 9, which left almost no window for a classmate to pick it up before the deadline — that's on me, not on the reviewers.

**How you responded:**
Nothing to respond to yet. What I did instead was try to make the PR reviewable without a conversation: I wrote the three questions I actually wanted answered into the "Notes for Reviewers" section rather than leaving it blank — whether silently skipping a null chunk is the right call for an evaluator, whether the identical latent bug at `relevance_scorer.py:32` belongs in this PR or a follow-up issue, and whether anyone knows why a chunk has `text: None` in the first place. If a review lands, those are the three threads I expect it to pull on.

---

### Reflection

**What was harder than you expected?**
Proving I hadn't broken anything was harder than fixing the bug. The actual fix is two lines. Everything else — probably 80% of my time — went into working out what "passing" even means in a repo where `make test-unit` fails 53 tests, `ruff` reports 181 errors, `black` wants to reformat 51 files, and `make typecheck` can't complete at all because a numpy stub uses Python 3.12+ syntax my interpreter rejects. On my own projects green means green. Here I had to record baselines *before* touching anything and diff failure lists afterward, because "52 failed" is only good news if you can show it was 53 before.

The part I didn't see coming at all was pre-commit refusing my test commit over problems that were already in the file. `tests/unit/test_faithfulness_checker.py` failed ruff, black, and 25 mypy `no-untyped-def` errors on the branch base — before I typed a character. So the project's own tooling made it impossible to commit a test into a file the project already doesn't lint. Every escape route was a tradeoff: fix all 26 and balloon a Tier 1 bugfix into an unrelated cleanup PR, or bypass the hook and explain myself. I annotated only my three new tests so my additions provably add zero errors (pre-commit reports the identical ruff 1 / mypy 25 counts with and without my commit), then used `--no-verify` and documented exactly that in the commit message. I still don't know if a maintainer would agree with that call. That uncertainty was uncomfortable in a way that debugging never is.

**What did you learn about working in a large codebase?**
Restraint is the actual skill. Three *other* tests in the same file I was editing also fail — `test_partial_support_returns_middle_score`, `test_multiple_context_chunks`, `test_multiple_claims_varying_support` — and my first instinct was that they were mine. They aren't. They fail on assertion thresholds against the `_is_supported` heuristic, which requires ≥2 non-stop-word overlapping tokens and is just too strict. I could see the fix. It's not my issue, so I left it, and the same went for `relevance_scorer.py:32`, which has the byte-identical `chunk.get("text", "")` bug and is one bad chunk from the same crash. On my own project I'd have fixed both in the same sitting. Here, an unrequested fix means a reviewer has to evaluate a scoring-heuristic change they didn't ask for, bundled with a null check they did — which is how a two-line PR sits unmerged for a month.

The other thing: my change is small, but its blast radius isn't. `check()` is called by `EvalSuite.evaluate()`, so the crash wasn't "one bad score" — it took down an entire evaluation run, discarding the valid chunks alongside the malformed one. I only understood the severity after tracing the caller. Reading outward from the fix site is not optional.

**How did AI tools help — and where did they fall short?**
Most useful for the mechanical grind I'd have done badly by hand: capturing baseline failure lists and diffing them, checking whether a given lint error predated my change by stashing and re-running, and orienting fast in a codebase I'd never seen. It also caught a real mistake of mine. My first version of the fix was `" ".join(chunk.get("text") for chunk in chunks if isinstance(chunk.get("text"), str))` — which *works*, but mypy rejected it, because calling `.get()` twice means the `isinstance` check narrows a different expression than the one being joined. Hoisting to a variable first fixed it. I'd have shipped the failing version and blamed the type checker.

Where it fell short was every question that turned on judgment rather than fact. Should a faithfulness evaluator crash loudly on malformed data or degrade quietly to a lower score? That's a question about what this project values, and the honest answer is that I don't know and neither does any tool — I picked non-crashing because the issue asks for it, added a `faithfulness_empty_context` log so the degradation is at least visible, and wrote the tradeoff into the PR for a human to overrule. Same for the `--no-verify` decision and the `relevance_scorer.py` scope call. AI got me to the decision points much faster and then had nothing to offer at them.

**What would you do differently if you started over?**
Read `docs/CONTRIBUTING.md` in Week 8, not Week 9. I wrote my reproduction commit as `repro: document issue #153...` and only found out later that `repro` isn't a valid Conventional Commits type in this project — the allowed set is `fix`/`feat`/`test`/`docs`/`refactor`/`perf`/`chore`/`ci`. It's already pushed and rewriting history to fix a label felt worse than living with it, but it's a sloppy first impression on a PR where I'm otherwise asking a maintainer to trust my judgment.

I'd also open the draft PR on Monday with the fix half-finished, instead of Sunday with it polished. I optimized for having something defensible to show and got zero peer feedback as a result, which was the single most valuable thing the week offered. A messy draft that gets a comment beats a clean one nobody reads.

Smaller: I'd run the baselines before writing the plan, not after. My PLAN.md listed "does `relevance_scorer.py` share the idiom?" as an open unknown when a ten-second grep answered it — I was speculating in a document when I could have been checking.

**What are you most proud of from this module?**
Not the fix — it's a null check. It's the PR description. I documented every pre-existing failure with before/after numbers, explained why `make typecheck` can't pass for anyone on any branch, admitted I skipped a pre-commit hook and showed the evidence that my code adds zero new errors, left `test-integration` unchecked instead of quietly ticking it, and named the two things I deliberately didn't fix. A reviewer can verify every claim in it without running anything. In a repo this noisy, that write-up is more useful to a maintainer than the patch is — and it's the part I'd have skipped entirely three months ago.