# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/47

**Issue title:** Agent state isn't persisted across API restarts, causing in-progress reviews to be lost

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
When the agent runs a long review (multiple repos/tools), it tracks progress only
in the orchestrator's local memory and writes that progress to Redis a single
time, after every tool in the plan has finished. If the API process restarts
while a review is still in progress — a deploy, a crash, anything — none of the
work done so far is saved, and the review has to start completely over. The
code lives in `agent/orchestrator.py` (the `Orchestrator.run()` loop) and
`agent/memory/session_store.py` (the Redis-backed store it writes to). A
successful fix checkpoints each tool's result to Redis as soon as that tool
finishes, and on a fresh run checks that saved state first so completed tools
are skipped and only the unfinished ones actually re-execute.

**Scope reasoning ("Is this right for me?"):** This is a Tier 3 issue, a bigger
jump than the recommended Tier 1 starting point for a first contribution. I
chose it deliberately over the smaller Tier 1 health-check bug I'd originally
selected (#154). It's still tractable: it touches two files I could read in
full, the fix is a scoped change to *when* an existing Redis write happens
(not a new subsystem), and I verified my understanding by reading both files
end-to-end before writing any code. The estimated effort in the issue (7–10
hours) is real, mostly because a correct fix needs a second behavior beyond
checkpointing — actually skipping already-completed tools on resume — which
isn't obvious from the issue title alone.

**Branch name:** fix/47-persist-agent-progress-across-restarts

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [4c0550b — docs: reproduce issue #47 and add Week 8 solution plan](https://github.com/LuisMend12/pathreview/commit/4c0550b)

**Reproduction summary:**
The fix for #47 (`cb5cc09`) and its regression tests
(`tests/unit/test_orchestrator.py`) were already committed on this branch
before I got to this week's reproduction step, so instead of writing a new
failing test from scratch I reproduced the original bug directly: I
temporarily replaced `agent/orchestrator.py` with its pre-fix version
(`git show cb5cc09^:agent/orchestrator.py`) and reran the existing
regression suite against it.

```
$ ./.venv/Scripts/python -m pytest tests/unit/test_orchestrator.py -q
...
FAILED tests/unit/test_orchestrator.py::TestOrchestratorCheckpointing::test_progress_is_checkpointed_after_each_tool_not_only_at_the_end
FAILED tests/unit/test_orchestrator.py::TestOrchestratorCheckpointing::test_restart_mid_review_resumes_without_rerunning_completed_tools
FAILED tests/unit/test_orchestrator.py::TestOrchestratorCheckpointing::test_previously_failed_tool_is_retried_on_resume
3 failed, 1 passed in 1.62s
```

The failure in `test_previously_failed_tool_is_retried_on_resume` shows the
bug concretely: `tools["tool_a"].execute.call_count` is `1` when it should
be `0` — the pre-fix orchestrator re-executes a tool that a prior run
(simulated via a seeded `session_store`) had already completed
successfully, because the loop in `Orchestrator.run()` never checked
existing session state per-tool and only persisted results once, after the
whole loop finished. I then restored `agent/orchestrator.py` via
`git checkout -- agent/orchestrator.py` and confirmed all 4 tests pass again
on the fixed version. This confirms the bug is real and pins it exactly to
the loop body in `Orchestrator.run()` described in `PLAN.md`.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):** _not recorded this week_

**Blockers or open questions:**
None blocking. Open question carried into Week 9: whether the "already
done" check should key off something more explicit than dict shape
(`success` key) so a future tool with a different result shape can't be
misread as complete — see Risks & unknowns in `PLAN.md`.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The implementation and its tests (`agent/orchestrator.py`,
`agent/memory/session_store.py`/`context_manager.py`,
`agent/error_handling.py`, `tests/unit/test_orchestrator.py`) were already
complete going into this week — all 5 sub-tasks from `PLAN.md`'s Plan
section are done. This week's work was verification and PR prep, not new
implementation: I ran `make test-unit` and confirmed the 53 failing tests
in the suite are pre-existing by diffing the failure list against the same
run on this branch's base commit (`54cc749`) — identical set, so this
change introduces no new failures. Same check for `ruff`/`mypy`: repo-wide
error counts went *down* (182→175 lint, 103→90 typecheck) because the fix
commit's type annotations closed 13 pre-existing mypy errors in the files
it touched, and none of the 5 changed files have any lint/typecheck/format
issues of their own.

**Next steps:**
PR #199 against `ascherj/pathreview` was already open from before Week 8
but had an empty template body — filled it in with the real summary,
changes, and testing/verification details this week. Still need to
request peer/mentor review in Slack.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/199

**Branch:** `fix/47-persist-agent-progress-across-restarts`

**What you built:**
`Orchestrator.run()` now checkpoints each tool's result to Redis
immediately after it completes, instead of once at the very end of the
tool loop, and checks previously-saved session state before running each
tool so a restart resumes from where it left off — completed tools are
skipped, failed ones are retried.

**Tests added or updated:**
`tests/unit/test_orchestrator.py` (new, 4 tests): incremental
checkpointing after each tool, resume-after-restart across two
`Orchestrator` instances sharing one `session_store`, retry of a
previously-failed tool, and unchanged no-persistence behavior when
`session_store=None`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
_(both confirmed with zero new failures relative to this branch's base
commit — see Check-in 1 for the verification method; full breakdown in the
PR description)_

**Draft PR feedback received from:** none yet — PR was already open
(not draft) from before Week 8; requesting peer/mentor review in Slack
this week

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review has come in. Su26 note: reviewer feedback isn't a feature this
term, so this is expected rather than a stall. I confirmed directly via
`gh pr view 199 --repo ascherj/pathreview --json comments,reviews` that
PR #199 has zero comments and zero reviews as of the Week 10 deadline.

**How you responded:**
N/A — nothing to respond to. I left the PR description as finalized in
Week 9 rather than editing it speculatively.

---

### Reflection

**What was harder than you expected?**
Understanding `agent/orchestrator.py`'s flow before I could touch it safely.
The bug itself (checkpoint once at the end instead of per-tool) is a
one-line-sounding description, but `Orchestrator.run()` interacts with
`agent/memory/session_store.py` and `agent/error_handling.py` in ways that
aren't obvious from reading any single file — I had to trace how a tool
result becomes a Redis write, and separately how a fresh run decides
whether a tool is "already done," before I trusted myself to change the
loop. The Week 8 reproduction step (reverting to the pre-fix version and
watching specific tests fail) is what actually made the control flow click;
reading the code alone didn't.

**What did you learn about working in a large codebase?**
Existing conventions constrain the fix more than the bug report does. I
couldn't just design the "was this tool already done" check however I
wanted — it had to match the shape `session_store.py` already used to
persist results (the `success` key that Week 8's open question flagged as
fragile), because introducing a new convention just for this fix would
have meant touching more of the codebase than the issue warranted. In my
own projects I'd have just redesigned the storage shape; here the scope of
"correct" is set by what's already there, not by what's cleanest.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for test scaffolding — generating the
boilerplate for `tests/unit/test_orchestrator.py`'s four cases (incremental
checkpointing, resume across two `Orchestrator` instances sharing one
`session_store`, retry of a failed tool, and the `session_store=None`
no-op path) so I could focus on getting the assertions right. It fell short
on the actual domain logic: deciding what "already done" should mean for a
tool result, and whether keying off a `success` field was robust enough,
required reasoning about this specific codebase's data shapes that no
amount of prompting substituted for. That's still an open question I
flagged in Week 8 and didn't fully resolve.

**What would you do differently if you started over?**
I'd record a walkthrough video during Week 8 instead of skipping it. I
noted "not recorded this week" in the Week 8 entry, and in hindsight a
short recording of the reproduction (reverting to `cb5cc09^`, showing the
three tests fail, restoring the fix) would have been useful both as a
reviewer aid and as documentation I could point back to instead of
re-deriving the failure details from memory while writing this journal.

**What are you most proud of from this module?**
Choosing the Tier 3 issue (#47) over the smaller Tier 1 health-check bug
(#154) I'd originally picked. It was a real jump in scope — a two-file,
cross-cutting fix instead of an isolated bug — but I made that call
deliberately in Week 7 after confirming I could read both files end-to-end,
and it held up: the fix needed a second behavior (skipping completed tools
on resume, not just checkpointing) that wasn't obvious from the issue title,
and I only caught that because I'd taken the issue seriously enough to plan
it properly instead of picking the safe option.
