# Issue #47 reproduction: agent state lost across API restarts

**Issue:** https://github.com/ascherj/pathreview/issues/47

Confirmed locally on 2026-07-27. When the API process dies partway through
an orchestrator run, every tool result completed before the crash is thrown
away, and the re-run starts over from the beginning.

## Why it happens

In the pre-fix code (`main` branch):

* `agent/memory/context_manager.py` keeps all tool results in a plain dict
  in process memory. Nothing is written anywhere else.
* `agent/orchestrator.py` only calls `self.session_store.set(...)` once,
  after the entire plan finishes. If the process dies mid-run, that line is
  never reached, so Redis never sees any of the completed work.

## How to reproduce

No Redis or running API needed. The script `scripts/reproduce_issue_47.py`
uses an in-memory stand-in for the Redis `SessionStore` and simulates the
restart with a `KeyboardInterrupt` subclass, which the orchestrator's
per-tool `except Exception` cannot swallow, the same way a real process
kill interrupts the loop.

```
git checkout main
python scripts/reproduce_issue_47.py
```

The script:

1. Runs a 4-tool plan where `tech_detector` and `readme_scorer` complete,
   then the process "dies" while `skill_extractor` is executing.
2. Prints what the session store contains at crash time.
3. Simulates the restart with a fresh `Orchestrator` (fresh in-memory
   `ContextManager`, same session store, same profile id) and re-runs.
4. Counts total executions per tool across both runs.

## Observed output on `main` (pre-fix)

```
>>> simulated restart: API process killed while running skill_extractor
>>> tools completed before the crash: 2
>>> session store contents at crash time: EMPTY

RESULT
tech_detector: executed 2 time(s) total
readme_scorer: executed 2 time(s) total

BUG REPRODUCED: 2 tool result(s) that had already completed before the
restart were thrown away and recomputed from scratch. Nothing was
persisted until the full run finished.
```

Two tools finished their work before the crash, the store held nothing,
and both ran a second time after the restart. That is the state loss the
issue describes.

## Observed output on `fix/47-agent-state-persistence`

Running the same script on the fix branch shows the target behavior. At
crash time the store holds a checkpoint with both completed results and an
`_in_progress` marker (`completed_steps: 2, total_steps: 4`), and the
re-run logs `context_hydrated entries=2` and finishes with:

```
RESULT
tech_detector: executed 1 time(s) total
readme_scorer: executed 1 time(s) total

FIXED BEHAVIOR: completed tool results were checkpointed to the session
store as they finished, and the re-run resumed from the last completed
step via cache hits.
```
