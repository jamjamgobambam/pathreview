## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The FaithfulnessChecker's `check()` method builds its context string from RAG
chunk dictionaries using `chunk.get("text", "")`, assuming this always returns
a string. But `.get()`'s default only applies when a key is missing — if a
chunk's `"text"` key exists but is explicitly set to `None`, `.get()` still
returns `None`, and the following `" ".join(...)` call then crashes with a
`TypeError` since you can't join a `None` value with strings. This lives in
`rag/evaluator/faithfulness_checker.py`, the part of the RAG evaluation
pipeline that checks whether AI-generated review claims are actually
supported by retrieved context. A successful fix would coerce a `None` text
value to an empty string before joining, so faithfulness checking degrades
gracefully instead of crashing whenever ingestion produces a chunk with
missing text content.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/vaishnavibollapalli/pathreview/commit/c762598

**Reproduction summary:**
Ran the existing test `test_none_context_chunk_text` in
`tests/unit/test_faithfulness_checker.py` and confirmed it fails with
`TypeError: sequence item 0: expected str instance, NoneType found` at line
34 of `rag/evaluator/faithfulness_checker.py`, where `chunk.get("text", "")`
returns `None` instead of the default when the chunk's `"text"` key is
explicitly `None`.

**PLAN.md link:** https://github.com/vaishnavibollapalli/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** [add Loom link here if you record one]

**Blockers or open questions:**
Still need to grep `ingestion/` and `agent/` to confirm whether the same
`.get("text", ...)` pattern appears elsewhere before finalizing the full fix
scope for Week 9.

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in `rag/evaluator/faithfulness_checker.py` — changed
`chunk.get("text", "")` to `chunk.get("text") or ""` (sub-tasks 1–2 from
PLAN.md). Added 2 new unit tests in `tests/unit/test_faithfulness_checker.py`
covering all-None-chunks and mixed-None-and-valid-chunk cases (sub-task 4).
Ran the full `tests/unit` suite and confirmed the fix introduces no new
failures — 377 passed both before and after, with 52 pre-existing failures
unrelated to this change (verified 3 of those in my own test file fail
identically on unmodified `main` via `git stash`). Applied `black`
formatting to both touched files.

**Next steps:**
Open a draft PR, request peer/mentor feedback in Slack, and finalize the PR
description before Sunday's deadline.

**Blockers:**
None.


### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/387

**Branch:** fix/153-faithfulness-checker-none-text

**What you built:**
Fixed a `TypeError` crash in `FaithfulnessChecker.check()` that occurred
when a context chunk's `"text"` field was explicitly `None`. Changed
`chunk.get("text", "")` to `chunk.get("text") or ""` so `None` values are
coerced to empty strings before being joined into the context string.

**Tests added or updated:**
Added `test_all_none_context_chunks` and
`test_mixed_none_and_valid_context_chunks` to
`tests/unit/test_faithfulness_checker.py`, covering the case where every
context chunk has `None` text and the case where a `None` chunk is mixed
with a valid one. The existing `test_none_context_chunk_text` (previously
failing) now passes with this fix.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(confirmed via equivalent `ruff`/`black`/`mypy` commands on the two files
this PR touches, since `make` isn't available on Windows PowerShell; 52
pre-existing failures across the full suite are unrelated to this change,
documented in the PR description)

**Draft PR feedback received from:** None

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback came in on PR #387 by the end of the
module. I also requested peer feedback in Slack during Week 9 before
marking the PR ready for review, but did not receive a response before
that deadline either.

**How you responded:**
N/A — no feedback was received to respond to.

### Reflection

**What was harder than you expected?**
Environment setup took far longer than the actual code fix. `make` isn't
available on Windows PowerShell at all, so I had to translate every
Makefile target (`setup`, `run`) into the equivalent manual commands
(venv creation, `pip install -e ".[dev]"`, `alembic upgrade head`, running
uvicorn and the Vite dev server in separate terminals). On top of that,
Docker Desktop wasn't running when I first tried `docker compose up -d`,
and then a separate flaky-network issue caused image pulls to fail
partway through with `EOF` errors on the exact same layer, requiring a
`wsl --shutdown` before a retry finally succeeded. None of that was
related to the actual bug I was fixing — it was pure infrastructure
friction, and it ate most of Week 7.

**What did you learn about working in a large codebase?**
The single biggest lesson was that "does my code work" and "does the
project's test suite pass" are two different questions in an established
codebase. When I ran the full `tests/unit` suite, 52 tests were already
failing before I changed anything — spanning bias detection, PII
scrubbing, resume parsing, and more, none of which I touched. I had to
learn to isolate my own diff (`git diff main -- <file>`) and use
`git stash` to prove a set of failures existed identically on unmodified
`main`, rather than either panicking about them or silently ignoring them.
Documenting "this PR introduces no new failures" turned out to be a real
skill, not a formality — it's the difference between a reviewer trusting
your PR and a reviewer having to re-verify everything themselves. I also
learned that a project's local pre-commit hooks and its official CI
target (`make check`) aren't always the same thing — my pre-commit `mypy`
hook flagged 26 errors in the test file that the project's own
`mypy api/ core/ ingestion/ rag/ agent/ safety/` target would never catch,
since it doesn't even check `tests/`.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for translating between environments (Makefile
targets to PowerShell commands), diagnosing unfamiliar error messages
(the Docker npipe connection error, the asyncpg `ConnectionRefusedError`
traceback, the ruff/black/mypy output), and structuring the planning
documents (PLAN.md, PR description) so nothing required by the rubric was
missed. Where it fell short was code I generated myself without careful
review: I introduced two indentation bugs by hand (a broken `context_text`
block in `faithfulness_checker.py`, and a completely de-indented test
method in the test file) that weren't caught until pytest's collection
step failed. AI could tell me *why* the traceback happened, but it
couldn't have caught the mistake before I ran it — that required me to
actually read the diff carefully before committing.

**What would you do differently if you started over?**
I'd read the actual Makefile before assuming `make setup` would just work,
since knowing upfront that it depended on Docker, Redis, and a vector DB
would have let me start Docker Desktop and diagnose the network issue in
parallel with other setup steps instead of hitting it as a surprise mid-way
through. I'd also run `git diff` against my own changes immediately after
every edit, rather than after pytest failed — that would have caught both
indentation bugs before wasting a debugging cycle on them.

**What are you most proud of from this module?**
Being able to definitively separate "failures I caused" from "failures
that already existed" using `git stash` and isolated diffs, and documenting
that clearly enough in the PR description that a reviewer wouldn't need to
redo that investigation themselves. That felt like the most transferable,
professional skill from the whole module — more than the one-line fix
itself.