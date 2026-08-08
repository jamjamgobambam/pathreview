# Week 7 — Issue Selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/153  
**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`  
**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3


## Problem Summary

I chose this issue to strengthen the reliability of PathReview’s Retrieval-Augmented Generation (RAG) evaluation pipeline without changing scoring behavior or any user-facing functionality.

The `FaithfulnessChecker` (`rag/evaluator/faithfulness_checker.py`) determines whether model-generated claims are supported by retrieved context. When an upstream retrieval step returns a context chunk shaped like `{"text": None}`, the checker’s context aggregation logic fails. Although the code calls `dict.get("text", "")`, Python returns the explicit `None` value because the key exists, so the fallback empty string is never used. As a result, `" ".join(...)` receives a `NoneType` and raises a `TypeError`.

The planned fix introduces a small defensive normalization step at the evaluator boundary so every context value is safely converted to a string before concatenation. This prevents crashes caused by malformed retrieval output while preserving the existing scoring algorithm and behavior for all valid inputs.

---

# Week 8 — Reproduction & Solution Planning

**Reproduction commit link:**  
https://github.com/alexh30486-ui/pathreview/commit/5735928

## Reproduction Summary

The issue was reproduced locally using the following code:

```python
FaithfulnessChecker().check(
    "Knows Python.",
    [{"text": None}]
)
```

Running this immediately produced the following exception:
=======
## Problem summary

This issue is narrow, reproducible, and isolated to the RAG evaluation path. The bug appears in `FaithfulnessChecker.check()` when context chunks are combined into one string for overlap scoring. If a retrieved chunk contains `{"text": None}`, the join operation crashes before any claim evaluation can happen.

## Root cause

The original aggregation logic used:

```python
context_text = " ".join([
    chunk.get("text", "") for chunk in context_chunks
])
```

That works when the `text` key is missing, but it fails when the key is present with an explicit `None` value. In that case, `dict.get()` returns `None`, and `" ".join(...)` raises:


```text
TypeError: sequence item 0: expected str instance, NoneType found
```


Investigation confirmed that Python's `dict.get("text", "")` returns `None` whenever the `"text"` key exists but explicitly contains `None`. Since the default value is ignored in this case, the subsequent `" ".join(...)` operation attempts to concatenate a list containing a `NoneType`, causing the crash.

Additional testing verified that:

- Normal string values work correctly.
- Missing `"text"` keys correctly fall back to an empty string.
- Only explicit `None` values trigger the failure.

This isolated the bug to context normalization before claim evaluation.

**PLAN.md link:**  
https://github.com/alexh30486-ui/pathreview/blob/fix/153-faithfulness-none-text/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:** None.

---

# Week 9 — Solution Building & PR Submission

## Check-in 1 (Mid-Week)

### Current Progress

Completed the following implementation tasks from `PLAN.md`:

- Successfully isolated and reproduced the `TypeError` inside `rag/evaluator/faithfulness_checker.py`.
- Documented the root cause, affected module, expected behavior, and edge cases within `PLAN.md`.
- Implemented the defensive normalization by replacing context extraction with:

```python
(chunk.get("text") or "")
```

This safely converts explicit `None` values into empty strings before concatenation while preserving behavior for all existing valid inputs.

### Next Steps

- Add a focused regression test covering the `{"text": None}` case in `tests/unit/test_faithfulness_checker.py`.
- Execute:

```bash
make check
make test-unit
```

to verify no regressions have been introduced.

- Open draft Pull Request **#245**.
- Request mentor and peer feedback.
- Address review comments.
- Mark the PR ready for review after validation.

### Blockers

None.

---

# Test Coverage

**Name:** Test Coverage

**Labels:** `tests`

## What Needs Testing?

`FaithfulnessChecker.check()` should be tested specifically for its handling of context chunks where the `"text"` field explicitly contains a `None` value:

```python
{"text": None}
```

The goal is to ensure malformed retrieval output no longer crashes the evaluator.

## Current State

Current test coverage does **not** include regression tests for explicit `None` values.

Specifically:

- Existing tests cover valid string context.
- Existing tests cover missing `"text"` keys (`{}`).
- No tests verify behavior when `"text"` exists but is explicitly `None`.

Because of this gap, the following runtime error can occur during context aggregation:

```text
TypeError: sequence item 0: expected str instance, NoneType found
```

This occurs before claim evaluation begins, preventing the faithfulness checker from returning a score.

## Relevant Files

### Source

- `rag/evaluator/faithfulness_checker.py`

This file contains `FaithfulnessChecker.check()`, where defensive normalization should be applied using:

```python
(chunk.get("text") or "")
```

### Tests

- `tests/unit/test_faithfulness_checker.py`

Regression tests should be added here following the existing project testing patterns.

## Acceptance Criteria

- [ ] Tests follow existing conventions used throughout `tests/`.
- [ ] All newly added tests pass.
- [ ] No existing tests fail after the change.
- [ ] At least one test calls `FaithfulnessChecker.check()` using a context list containing:

```python
{"text": None}
```

and verifies that the method completes without raising a `TypeError`.

- [ ] A regression test verifies that a mixed context list containing:
  - valid string values,
  - missing `"text"` keys,
  - and explicit `None` values

can be processed successfully, joining only valid text and returning a valid faithfulness score.

- [ ] Existing faithfulness scoring behavior remains unchanged for valid inputs.

## Expected Outcome

After the fix:

- Explicit `None` values are safely normalized to empty strings.
- Context aggregation no longer raises a `TypeError`.
- The evaluator continues processing remaining valid context.
- Faithfulness scoring remains identical for all previously supported inputs.
- Future regressions involving malformed context data are prevented through automated unit tests.
=======
## Fix applied

The context normalization step now treats both missing keys and explicit `None` values as empty strings before concatenation:

```python
context_text = " ".join((chunk.get("text") or "") for chunk in context_chunks)
```

This preserves the existing scoring logic and public interface while making the evaluator resilient to malformed upstream retrieval data.

## Verification

The regression case was verified directly:

```python
from rag.evaluator.faithfulness_checker import FaithfulnessChecker

FaithfulnessChecker().check("Knows Python.", [{"text": None}])
```

Observed result:

```text
0.0
```

The targeted unit suite was also run successfully:

```bash
pytest -q tests/unit/test_faithfulness_checker.py
```

Result:

```text
22 passed in 0.46s
```
## Check-in 2 (End of Week)

**PR link:** https://github.com/ascherj/pathreview/pull/245

**What was built:**  
Fixed a TypeError in FaithfulnessChecker that occurred when a context chunk contained `{"text": None}`. Added defensive normalization so the evaluator no longer crashes on malformed retrieval data.

**Branch:** `fix/153-faithfulness-none-text`

**Tests:**  
- File: `tests/unit/test_faithfulness_checker.py`  
- Added a regression test that calls `FaithfulnessChecker().check()` with a context chunk containing `{"text": None}` and verifies it returns a score without raising a TypeError.

**Self-review:**
- [x] `make check` passes
- [x] `make test-unit` passes

## Final review

The change is limited to defensive context normalization in the evaluator. It does not alter claim extraction, overlap thresholds, or the overall faithfulness scoring behavior for valid inputs. The implementation is now aligned with the issue report, the regression test coverage, and the verified runtime behavior.



## Week 10 — Iteration & reflection

### Reviewer feedback
**Feedback received:** [ ] Yes  [x] No — still awaiting review. 

**Summary of feedback:**
No review came in. Per the Summer 2026 guidelines, reviewer feedback is not an active feature for this term.
Functional codebase taught me that reading and understanding existing patterns is just as important as writing new code. I learned how to navigate complex dependency trees, respect established testing conventions, and ensure that my changes didn't introduce side effects in unrelated modules.Working in a large, established codebase taught me that reading and understanding existing patterns is just as important as writing new code. I learned how to navigate complex dependency trees, respect established testing conventions, and ensure that my changes didn't introduce side effects in unrelated modules.
**How you responded:**
Does not apply to Summer Cohort but AI tools were excellent for explaining complex, unfamiliar code blocks and suggesting boilerplate for tests, which significantly sped up my workflow. However, they occasionally hallucinated library methods or suggested patterns that didn't align with the project's specific architectural constraints, requiring me to double-check everything against the existing codebase.
## Reflection

What was harder than you expected?
The codebases definitely surprised me. I didn’t expect them to be that difficult. I had never really coded in other people’s repositories before, and this process opened my mind to how universal and important GitHub is as a skill in the working world. Another aspect of the course that surprised me was the variety of projects proposed and the different requirements and tools we had to use—such as AI/LLM agents and workflows.
What did you learn about working in a large codebase?
Contributing to someone else’s production code is very different from building your own project from scratch. In your own work you control the architecture, naming, and structure. In a shared codebase you have to adapt to existing conventions, understand how different parts connect, and be careful not to break things that other people rely on. Reading and navigating large, unfamiliar code becomes a core skill.

How did AI tools help — and where did they fall short?
AI assistance was most useful for quickly understanding unfamiliar sections of code and overall concepts for me personally, I used them to scan the scope of the work and work through the process myself, generating boilerplate, suggesting approaches, and helping debug smaller issues. It fell short when the problem required deep context about the specific project’s architecture or when the solution needed careful judgment about design trade-offs. In those cases I still had to dig into the codebase myself and reason through the system.

What would you do differently if you started over?
If I were to start over I would give myself more time to build solid foundations—brushing up on what current AI models are actually capable of, learning agentic workflows, and spending more time on planning. Many of the projects I didn’t plan properly for, which led me to fall behind compared with classmates who seemed to have a clearer grasp of these processes. I would also make better use of the collaboration time during breakout sessions.

What are you most proud of from this module?
I’m most proud of pushing through the discomfort of working in real, unfamiliar codebases and learning how to contribute effectively. Getting comfortable with GitHub, reading other people’s code, and using AI tools as part of a real workflow feels like a meaningful step toward professional-level work.