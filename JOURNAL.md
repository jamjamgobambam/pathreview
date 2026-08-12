## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/44

**Issue title:** Orchestrator catches all exceptions from tool calls and continues without logging the failure

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Why I chose this issue:**
Tier 2 fits where I am right now: I haven't contributed to an open-source project before, but I have worked in large, unfamiliar codebases before, so tracing a bug across two cooperating modules (`orchestrator.py`'s plan-execute loop and `error_handling.py`'s retry decorator) is a reasonable stretch without being a leap into full-system territory. I also specifically wanted an issue touching the agent system rather than ingestion or the frontend, and this is squarely that. Before claiming it, I checked scope: the issue names exactly two files, has zero existing comments/claims, and — I confirmed by tracing call sites — `Orchestrator` isn't wired into the live review pipeline yet (the API currently calls a hardcoded stub instead), which means my fix stays contained to the module itself and its first unit tests, rather than ballooning into also wiring it into `review_service.py`.

**Problem summary:**
The plan-execute loop in the agent orchestrator wraps each tool call in a broad `except Exception` handler that catches the failure, logs it, and then just moves on — the loop continues as if nothing happened. Currently, a failed tool call produces no distinct failure signal: its result is stuffed into the same results dict as successful tools (as an `{"error": ..., "success": False}` entry), so nothing downstream is forced to notice or react to it, and a review can come back with missing sections and zero indication to the user that something broke. This affects `agent/orchestrator.py` (the loop itself) and `agent/error_handling.py` (the retry/backoff logic tool calls go through before they reach that handler). A successful fix makes tool failures impossible to silently absorb — raising or clearly flagging them so calling code must handle the failure explicitly — backed by unit tests (there currently are none for this module) that prove a failing tool is no longer indistinguishable from a successful one.

**Branch name:** fix/44-orchestrator-silent-tool-exceptions

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [ba2cf7f](https://github.com/ascherj/pathreview/commit/ba2cf7f) (branch `fix/44-orchestrator-silent-tool-exceptions`)

**Reproduction summary:**
Added `tests/unit/test_orchestrator.py`, which runs `Orchestrator.run()` with a tool that always raises `RuntimeError`. The test fails against current code: `run()` returns normally with no top-level failure indicator — the exception is caught in the plan-execute loop (`orchestrator.py:60-62`) and buried inside `tool_results["tech_detector"]` as an `{"error": ..., "success": False}` entry, indistinguishable in shape from a successful tool's output.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):**

**Blockers or open questions:**
Still deciding whether a fully-failed run should raise from `run()` entirely vs. always return normally with a `success: False` flag (see Risks & unknowns in PLAN.md). Also need to confirm via grep whether `RetryContext` in `error_handling.py` is dead code before Week 9, since it looks unused outside the module.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Resolved the open question from Week 8: went with always returning normally with `success: False` + `failed_tools` rather than raising, since `run()` aggregates several independent tool calls and one bad tool shouldn't blow up the whole profile analysis. Implemented the fix in `agent/orchestrator.py` — `run()`'s plan-execute loop now tracks a `failed_tools` list alongside `results`, and the returned dict gains top-level `success: bool` and `failed_tools: list[str]` keys. Confirmed `RetryContext` in `error_handling.py` is genuinely dead code (grepped the whole repo — referenced nowhere outside its own module); left it alone since removing it is unrelated to this issue, but flagged it as a separate follow-up task rather than silently ignoring it.

Before touching anything, ran `make check` / `make test-unit` and recorded the pre-existing baseline: 54 pre-existing unit test failures (unrelated modules — bias detector, resume parser, review service, etc.), 175 pre-existing ruff errors, 49 files failing black formatting, and mypy stopping early on a pre-existing numpy/Python-version stub incompatibility. None of these touch `agent/orchestrator.py` or `agent/error_handling.py`.

Tests added: extended `tests/unit/test_orchestrator.py` from the single Week 8 reproduction test to 7 tests (full success, partial failure, total failure, empty plan, cache-hit-not-misreported, session-store persistence). Added `tests/unit/test_error_handling.py` (didn't exist before) with 3 tests confirming `retry_with_backoff` actually re-raises after exhausting retries rather than swallowing — the behavior the orchestrator fix depends on. All 10 new/updated tests pass; re-ran the full suite and confirmed no new failures beyond the documented baseline (54 → 53, since the reproduction test itself flipped from failing to passing).

**Next steps:**
Open a draft PR for early feedback, finish self-review against `docs/CONTRIBUTING.md` (branch name and commit messages already follow convention), fill out the PR template with the pre-existing-failures note, and get peer/mentor feedback in Slack before marking it ready for review.

**Blockers:**
None currently.

---

### Check-in 2 (end of week)

**PR link:** [#652](https://github.com/ascherj/pathreview/pull/652)

**Branch:** `fix/44-orchestrator-silent-tool-exceptions`

**What you built:**
`Orchestrator.run()`'s plan-execute loop now tracks which tools failed and returns top-level `success: bool` / `failed_tools: list[str]` keys, so a caller can tell in one check whether anything went wrong instead of having to inspect every entry in `tool_results`. This covers both ways a tool can fail: raising an exception, and returning `ToolResult(success=False, ...)` without raising at all (which the first version of the fix missed — a tool like `GitHubTool` reporting a 404 or missing input was silently dropped to an empty dict before this).

**Tests added or updated:**
Extended `tests/unit/test_orchestrator.py` from the original Week 8 reproduction test to 9 tests total: full success, partial failure, total failure, empty plan, a cached result not being misreported as a failure, session-store persistence, session-store merge with prior state, and — the fix's second pass — a tool that reports failure via `ToolResult(success=False, ...)` without raising. Added `tests/unit/test_error_handling.py` (didn't exist before), 3 tests confirming `retry_with_backoff` re-raises rather than swallowing after exhausting retries, since the orchestrator fix depends on that contract.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both pass with only pre-existing, documented failures unrelated to this change — see the PR description's Testing section for the exact baseline: 54 pre-existing unit test failures, 175 pre-existing ruff errors, 49 files failing black, and a pre-existing mypy/numpy stub mismatch, none in `agent/orchestrator.py` or `agent/error_handling.py`.)

**Draft PR feedback received from:** none yet — opened as draft for Slack peer/mentor review before Sunday's deadline. One round of self-review did catch a real gap (tools failing via `ToolResult(success=False, ...)` without raising weren't counted), which is already fixed and included above.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
[PR #652](https://github.com/ascherj/pathreview/pull/652) has been open and marked ready for review since August 3, with no reviewers assigned and no comments left. I checked the PR again this week specifically for this entry and confirmed there's genuinely nothing to respond to yet, rather than assuming.

**How you responded:**
Since no feedback landed, I used the week to re-read my own diff with fresh eyes instead of treating "no review" as "nothing to do." One thing I flagged in the PR description but never resolved myself: whether an "unregistered tool name" error should be reported through the same `failed_tools` path as a genuine execution failure, or whether it deserves a distinct category (it's arguably a planning/config bug, not a runtime tool bug). I left it as-is rather than making a unilateral change this late, since it's exactly the kind of judgment call that benefits from a second opinion, and re-flagged it clearly in the PR so a reviewer can weigh in before I'd touch it again.

---

### Reflection

**What was harder than you expected?**
Deciding *what shape a fix should take* was harder than writing the fix itself. The actual code change — adding `success` and `failed_tools` to the return dict — was small. The hard part was Week 8's open question (raise vs. return-with-flag) and the Week 9 discovery that my first pass missed a whole failure path (`ToolResult(success=False, ...)` returned without raising). Both took longer than the line-count of the eventual diff would suggest, because they required actually understanding every way a tool call can fail in this codebase, not just the one the issue description mentioned.

**What did you learn about working in a large codebase?**
The pre-existing-failures baseline mattered more than I expected going in. Before touching anything I had to run `make check`/`make test-unit` and write down exactly what was already broken (54 unit test failures, 175 ruff errors, 49 files failing black, a pre-existing mypy/numpy mismatch) so that later I could prove my change didn't add to that pile rather than just eyeballing "tests still pass." In a codebase I'd built myself I'd never have needed that step — I'd know what was broken because I broke it. In someone else's production code, "did I make things worse" isn't answerable without a documented before/after. I also learned to grep before assuming: I initially treated `RetryContext` in `error_handling.py` as possibly load-bearing until I confirmed by searching the whole repo that it's unreferenced dead code — cheap to check, expensive to get wrong.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for the mechanical scaffolding: generating the initial spread of test cases (full success, partial failure, empty plan, cache-hit, session-store merge) once I'd decided what the fix should do, and for drafting PLAN.md structure so I could focus my own attention on the actual design question. It fell short exactly where judgment was required — deciding whether `run()` should raise or return a flag, and later noticing that the first fix only handled the "tool raises" path and silently missed "tool returns failure without raising." Both of those needed me to trace actual call sites in `orchestrator.py` and `error_handling.py` and reason about the contract between them; no amount of prompting substituted for reading the code closely enough to notice the gap myself.

**What would you do differently if you started over?**
I'd write the test for "tool reports failure via `ToolResult(success=False)` without raising" in Week 8, during reproduction, instead of catching it in Week 9's self-review. The issue title emphasizes "catches all exceptions," which anchored my first pass on the raise path and let the non-raising path hide in plain sight. Enumerating all the ways a component can fail before writing any fix — not just the one named in the issue — is a habit I want to carry into the next codebase I touch.

**What are you most proud of from this module?**
Catching my own bug during self-review rather than needing a reviewer to catch it for me. The first version of the fix looked complete and passed every test I'd written — it was only by deliberately asking "what's another way this could fail that I haven't tested?" that I found the `ToolResult(success=False, ...)` gap, fixed it, and added a test that would have failed against my own first draft. That's the kind of scrutiny I want reviewing my own work to look like going forward, review or no review.
