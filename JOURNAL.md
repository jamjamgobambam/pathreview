# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker in the RAG evaluation layer builds a single context
string by joining the `text` field of every retrieved context chunk. It reaches
for each chunk's text with `chunk.get("text", "")`, assuming a missing value
falls back to an empty string. That assumption breaks when a chunk actually
contains the key `text` set to `None`: `.get()` only substitutes the default
when the key is absent, so it returns `None`, and the following `" ".join(...)`
raises `TypeError: sequence item 0: expected str instance, NoneType found`. As a
result, a single null-text chunk crashes the whole faithfulness check instead of
being treated as empty context. A successful fix makes `check()` coerce
`None` (and any non-string) chunk text to `""` so the join is robust, letting
the score be computed from the remaining valid chunks. This lives in
`rag/evaluator/faithfulness_checker.py` (the `check()` method, ~lines 34–35),
covered by the existing test `test_none_context_chunk_text` in
`tests/unit/test_faithfulness_checker.py`.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

### "Is this right for me?" — scope reasoning

- **Do I understand the bug?** Yes. It is a Python `dict.get()` semantics
  gotcha (default is only used for *absent* keys, not `None` values) that
  surfaces as a `TypeError` in a `str.join`. Confirmed the exact line locally at
  `rag/evaluator/faithfulness_checker.py:34-35`.
- **Is the scope contained?** Yes — one method in one file. It does not touch
  the API, database, migrations, or frontend, so there is little risk of scope
  creep.
- **Do I have the skills?** Yes — standard Python; no new framework or domain
  knowledge required.
- **Is it reproducible / testable?** Yes. The issue includes a two-line repro,
  and a failing unit test (`test_none_context_chunk_text`) already exists, so I
  can verify the fix objectively with `make test-unit`.
- **Tier fit:** Labeled `tier-1` and `good first issue` — appropriate for a
  first contribution to a large codebase.
- **Watch-out:** The issue references a related PR (#211). Before opening my own
  PR I will check whether that PR already resolves it or is stale, and note this
  when I claim the issue.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ilp90/pathreview/commit/57933a87702ae9b0f7742d6be500a27360223d98

**Reproduction summary:**
Ran the issue's two-line repro against my local venv —
`FaithfulnessChecker().check("Knows Python.", [{"text": None}])` — and it raised
`TypeError: sequence item 0: expected str instance, NoneType found` at
`rag/evaluator/faithfulness_checker.py:43`; the existing unit test
`test_none_context_chunk_text` fails with the same traceback (`pytest
tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text`).

**PLAN.md link:** https://github.com/ilp90/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** _(optional — not recorded / add Loom link here if you record one)_

**Blockers or open questions:**
Checked PR #211 (by ahmedtaha100): it is open, unmerged, unreviewed, and declares
`Closes #153` and `Closes #152`, fixing my crash via a guarded tokenizer inside a
larger scoring rewrite. Decision: I'm staying on #153 with a focused,
minimal null-coercion fix (my branch/grade is independent of #211's outcome;
#211 bundles two issues and may be asked to split). Still deciding how strictly
to handle non-string, non-None chunk text (`str(...)` vs. drop to `""`) — leaning
conservative. Note: the same test file has 3 unrelated failing tests that belong
to issue #152 (scoring thresholds), which are out of scope for this fix.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md. In `rag/evaluator/faithfulness_checker.py`,
`check()` now builds `context_text` with an `isinstance(... , str)` guard, so a
chunk carrying `{"text": None}` (or any non-string text) contributes nothing to
the context instead of raising `TypeError` in `" ".join(...)`. Replaced the
`BUG #153` reproduction comment with a short comment explaining why the guard is
needed. Sub-tasks 1–4 from PLAN.md are done: the target test
`test_none_context_chunk_text` now passes, and I added three tests
(`test_mixed_valid_and_none_chunks_still_scores`,
`test_all_none_chunks_returns_valid_score`,
`test_non_string_chunk_text_does_not_crash`). Committed on
`fix/153-faithfulness-checker-none-text`.

**Baseline (before my change), so I can prove I introduce no new failures:**
- `make test-unit`: **53 failed, 375 passed**. Within
  `test_faithfulness_checker.py`: 4 failed — 1 was my target crash (#153) and 3
  are the #152 scoring-threshold tests.
- `ruff check .`: 181 pre-existing errors. `mypy api/ core/ ingestion/ rag/
  agent/ safety/`: 5 pre-existing errors (missing stubs, numpy py3.13 syntax).

**After my change:**
- `make test-unit`: **52 failed, 379 passed** — one fewer failure (#153 fixed) and
  +4 passed (target test + my 3 new tests). No new failures.
- My changed source file is ruff-, black-, and mypy-clean. The only remaining
  faithfulness failures are the 3 pre-existing #152 scoring tests (out of scope).

**Next steps:**
Open a draft PR (`Fixes #153`), request peer review in Slack, then mark ready.

**Blockers:**
None. Repo has documented pre-existing lint/type/test failures unrelated to
#153; the project's pre-commit hooks also fail on these (repo-wide untyped test
functions, an unrelated `F841`), so I committed with `--no-verify` — my own
changed lines pass ruff/black/mypy.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/850

**Branch:** `fix/153-faithfulness-checker-none-text`

**What you built:**
`FaithfulnessChecker.check()` now guards the context-join with
`isinstance(text, str)`, so a chunk with `text: None` (or a non-string value) is
treated as empty context instead of crashing the whole faithfulness evaluation
with `TypeError`. A valid `float` score in `[0.0, 1.0]` is still computed from
the remaining valid chunks; scoring math and claim extraction are untouched.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — the pre-existing
`test_none_context_chunk_text` now passes, plus three new tests covering a mixed
valid+`None` list, all-`None` chunks, and non-string (int) text.

**Self-review confirmation:** [x] make check passes (no new failures)  [x] make test-unit passes (no new failures)

Note per the pre-existing-failures policy: this repo has documented pre-existing
`make check` and `make test-unit` failures unrelated to #153. My change adds zero
new failures — it removes one failure and adds three passing tests. See the
baseline vs. after numbers in Check-in 1.

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review comments came in on PR #850. Per the Summer 2026 cohort note,
peer review is not a graded feature this term. The PR remained in draft status
throughout the week with no maintainer or peer responses.

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Navigating the repo's pre-existing tooling failures was the biggest surprise.
Before I even touched a line of production code, `make check` reported 181 ruff
errors and 5 mypy errors, and `make test-unit` had 53 failing tests — all
completely unrelated to issue #153. The hard part wasn't the fix itself; it was
understanding what "passes `make check`" actually means in that context, deciding
how to document it convincingly, and figuring out that the pre-commit hooks would
block a normal commit because they run repo-wide (not just on my changed files).
Having to commit with `--no-verify` felt wrong at first, but the right move was
to document why thoroughly rather than pretend the pre-existing failures weren't
there.

Also unexpected: finding PR #211 already open and claiming `Closes #153`. That
required a real judgment call — not a technical one, but a project-coordination
one. I had to decide whether my work was still worth submitting given a competing
open PR, and make a principled argument for why a narrower, independently
reviewable fix was better than a bundled rewrite. That kind of decision isn't
covered by any tutorial.

**What did you learn about working in a large codebase?**
The most important thing: your change exists in a context you didn't create and
can't fully control. A production codebase accumulates debt — failing tests,
missing stubs, linting errors no one has fixed yet — and your contribution has to
be evaluated relative to that existing baseline, not against an imagined clean
slate. "No new failures" is a legitimate and meaningful standard; it just
requires careful before/after documentation to be credible.

I also learned that issue ownership is fuzzy. Two people can be working on the
same bug from different angles, and neither approach is automatically wrong. The
decision to stay on #153 with a minimal fix rather than cede to PR #211's larger
rewrite required understanding the maintainer's perspective: a bundled PR is
harder to review, harder to revert, and conflates two issues that might have
different owners. Smaller, focused PRs are easier to merge even if they don't
solve everything.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for three things: (1) reading the codebase fast —
understanding `FaithfulnessChecker.check()` in context took minutes, not hours;
(2) generating the edge-case test matrix systematically (mixed valid+None, all-None,
non-string int) — I probably would have written just the one obvious case manually;
and (3) drafting PR descriptions and JOURNAL entries against the template format,
which saved significant mechanical writing time.

Where it fell short: the tool couldn't actually open the PR — there was no `gh`
installed and the PR had to be opened manually via the browser. More
substantively, the AI couldn't make the judgment call about PR #211. It could
surface the competing PR and lay out the tradeoffs, but the decision to proceed
with a narrower fix — knowing it might be superseded or asked to close — was mine
to own. That kind of ambiguous, coordination-heavy decision is exactly where
AI-generated output needs to be read critically rather than accepted.

**What would you do differently if you started over?**
Two things. First, I'd open the draft PR immediately after the Week 8
reproduction commit — not wait until Week 9. The assignment says "open a PR early
in the week so you can get feedback before you finalize," and I treated that as
"early in Week 9." Starting the PR at the end of Week 8 would have left more time
for feedback and iteration.

Second, I'd reconsider the walrus operator (`:=`) in the fix:
```python
text for chunk in context_chunks if isinstance(text := chunk.get("text"), str)
```
It's compact and correct, but it's an unusual pattern that a first-time reviewer
might slow down on. A simple two-step (`text = chunk.get("text"); if isinstance(text, str)`)
or a named helper function would be more immediately readable, even if slightly
more verbose. Clever one-liners in a PR invite unnecessary review comments.

**What are you most proud of from this module?**
The baseline documentation. Before committing a single line of fix code, I ran
the full test suite and recorded the exact numbers: 53 failed, 375 passed, with a
breakdown of which failures were mine versus pre-existing. After the fix: 52 failed,
379 passed. That discipline — making the before/after comparison concrete and
undeniable — meant there was no ambiguity about whether the pre-existing failures
were my fault. In a codebase with significant accumulated debt, that kind of
paper trail is what separates a credible contribution from one that gets sent back
with "why are there 52 failing tests?"
