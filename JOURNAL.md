## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: `None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker currently assumes every context chunk has a string in
its `text` field, but one valid edge case is `text: None`. In
`rag.evaluator.faithfulness_checker`, the code uses `chunk.get("text", "")`,
which still returns `None` when the key exists, and that causes `" ".join(...)`
to crash with a `TypeError`. This breaks faithfulness evaluation for otherwise
valid inputs and can fail test coverage in `test_none_context_chunk_text`.
A successful fix should sanitize chunk text values so missing or `None` values
are treated as empty strings and `check()` can continue safely.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**"Is this right for me?" checklist:**
- [x] I can explain this issue in my own words and define what success looks like.
- [x] I identified the affected area (`rag.evaluator.faithfulness_checker`) and the related unit test (`test_none_context_chunk_text`).
- [x] Tier acknowledged: this is a Tier 1 issue, which matches my current comfort level because the fix is localized and low-risk.
- [x] Scope-fit reasoning: this issue is a good fit because it is a focused bug fix (handling `None` safely in chunk text processing) that should be solvable in one code path with supporting test coverage.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/jess4342/pathreview/commit/c857ad603c037d3a6c84e4a1206af359dfa8d754

**Reproduction summary:**
I reproduced the issue with:
`C:/Users/jess/Documents/codepathAI2026/pathreview/.venv/Scripts/python.exe -m pytest tests/unit/test_faithfulness_checker.py -k none_context_chunk_text -q`.
The test fails with `TypeError: sequence item 0: expected str instance, NoneType found` in `rag/evaluator/faithfulness_checker.py` when `check()` builds `context_text` using `" ".join(...)` and a chunk contains `{"text": None}`.

**PLAN.md link:** https://github.com/jess4342/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Blockers or open questions:**
Need to decide whether to sanitize only `None` values or all non-string `text` values (e.g., numbers, lists) to keep this code path robust.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I've completed the reproduction and planning phases from PLAN.md. Sub-task 1
(reproduce the bug with a focused pytest command) is done — running
`test_none_context_chunk_text` fails with
`TypeError: sequence item 0: expected str instance, NoneType found`, confirming
the root cause in `FaithfulnessChecker.check()` where `context_text` is built
with `" ".join([chunk.get("text", "") for chunk in context_chunks])` and a
chunk of `{"text": None}` slips a `None` into the join. I've mapped the exact
lines to change (`rag/evaluator/faithfulness_checker.py`, the context-text
build) and confirmed the target test already exists in
`tests/unit/test_faithfulness_checker.py`. The code fix itself (sub-task 2) is
not yet written — that's my focus for the rest of the week.

**Next steps:**
- Implement the fix: normalize chunk text in `check()` so `None`/missing values
  become empty strings before joining (sub-task 2).
- Keep the existing `test_none_context_chunk_text` and `test_missing_text_key_in_chunk`
  passing, and decide whether to add a test for non-string `text` values (sub-task 3).
- Run the targeted faithfulness tests, then the broader evaluator unit subset to
  catch regressions (sub-tasks 4–5), and run `make check` for lint/format/types.
- Open a draft PR early and request peer/mentor feedback before finalizing.

**Blockers:**
Still deciding the sanitization scope: coerce only `None` to `""`, or defensively
handle all non-string `text` values (numbers, lists) via `str(...)`. `str(...)`
avoids future crashes but could inject noisy tokens into scoring; `None`-only is
minimal but narrower. Leaning toward normalizing any non-string to `""` to keep
the fix focused on the bug without changing scoring for valid strings — will
confirm before finalizing.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/372

**Branch:** `fix/153-faithfulness-checker-none-text`

**What you built:**
`FaithfulnessChecker.check()` crashed with a `TypeError` when a context chunk
had `{"text": None}`, because `chunk.get("text", "")` returns `None` (not the
default) when the key exists, and `" ".join(...)` cannot join `None`. I added a
`_normalize_chunk_text` helper that returns a chunk's `text` only when it is a
string and an empty string otherwise, so `None`, missing, and non-string values
are all treated as empty and scoring continues normally.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — the pre-existing
`test_none_context_chunk_text` now passes, and I added
`test_non_string_context_chunk_text` (a non-string `text` value is coerced
safely) and `test_mixed_valid_and_none_chunks` (a `None` chunk beside a valid
chunk does not crash and support comes from the valid chunk).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
<!-- The repo has documented pre-existing failures in both commands; "passes"
here means my changes introduce no new failures. Baseline on main: 53 failing
unit tests; after my change: 52 failing / 378 passing (one fewer failure plus my
two new passing tests, no regressions). Pre-existing ruff/mypy/black issues are
unrelated to this change and are documented in the PR's Notes for Reviewers. -->

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer comments came in on PR #372 by the end of the week.
(Per the Summer 2026 cohort note, PR reviewer feedback is not provided this
term.) I checked the open PR for comments and none were present.

**How you responded:**
N/A — no feedback to respond to. If review had come in, the first thing I would
have wanted a second set of eyes on was whether coercing non-string chunk text
to an empty string is the right call versus surfacing malformed upstream data.

---

### Reflection

**What was harder than you expected?**
The hardest part wasn't the fix — it was working around everything the repo
already had wrong. When I ran `make test-unit` and `make check` for a baseline,
there were 53 failing unit tests, 182 ruff errors, and 103 mypy errors before I
touched anything. Then the pre-commit hooks blocked my commit because the test
file I was editing had no type annotations on any of its functions — a
pre-existing issue that had nothing to do with my one-line bug. Figuring out
whether "passing" meant a green suite or just "no new failures," and proving my
change only moved the count from 53 to 52 failures, took more care than writing
the actual `_normalize_chunk_text` helper. The root cause itself was also
sneakier than I expected: `dict.get("text", "")` looks safe, but the default
only applies when the key is missing, not when it's present with a `None` value.

**What did you learn about working in a large codebase?**
On my own projects, "done" means everything works. Here, "done" meant "don't
make it worse" — the codebase already had documented pre-existing failures, and
the expectation was that my contribution not add new ones, not that I fix the
whole repo first. That reframed how I worked: I took a baseline before changing
anything, kept my diff as small as possible (I reverted formatter changes that
would have touched unrelated lines), matched the existing conventions instead of
my own (Google-style docstrings, the `@staticmethod` helper pattern, the repo's
black/ruff line-length config), and documented the pre-existing failures in the
PR so a reviewer could tell my change apart from the noise. Reading the existing
tests before writing mine mattered more than I expected.

**How did AI tools help — and where did they fall short?**
AI was most useful for exploring an unfamiliar codebase quickly — locating the
crash, understanding the conventions in the test file, and drafting the helper,
tests, and PR description in the repo's style. It was also good at diagnosis:
why `git` wasn't on my PATH, why the pre-commit hooks were failing, why a commit
link survives a branch rename. Where it fell short was judgment: whether to
bypass the hooks or annotate an entire pre-existing test file, whether to rename
my branch mid-stream, how defensive the sanitization should be — those were
decisions I had to make and own. It also once let a formatter reformat unrelated
lines, which I had to catch and revert to keep the diff clean; the tooling will
happily do the technically-correct thing that's the wrong thing for the change.

**What would you do differently if you started over?**
Two things. First, branch naming — I named my branch `fix/faithfulness-checker-
none-text` without the issue number and had to rename it to
`fix/153-faithfulness-checker-none-text` to match CONTRIBUTING.md; I'd read the
contribution standards before creating the branch, not after. Second, I'd open
the draft PR much earlier and actually chase down a peer or mentor review —
I never got a second set of eyes, and I can already see edge cases I only
thought of late (what if `context_chunks` itself is `None` or not a list?) that
a reviewer might have flagged. I'd also run the `make check` / `make test-unit`
baseline on day one so the pre-existing failures never surprised me.

**What are you most proud of?**
That I resisted the urge to just wrap the join in a `try/except` and move on. I
traced the bug to the exact reason `dict.get` returned `None`, fixed it at that
point with a small readable helper, and proved with before/after numbers that I
improved the suite without breaking anything else. The discipline of keeping the
diff minimal and being transparent about what was pre-existing versus mine is
the part I'd be comfortable defending in a real review.