---
name: Documentation
about: Improve or add documentation
labels: docs
---

## What Needs Documenting?
`FaithfulnessChecker.check()` in `rag/evaluator/faithfulness_checker.py` — specifically how context chunks with an explicit `{"text": None}` value are handled.

The method previously crashed with a `TypeError` when a chunk contained `text: None`. A defensive normalization was added (`(chunk.get("text") or "")`), but there is currently no clear documentation explaining:
- why the original `.get("text", "")` was insufficient
- what edge cases are now safely handled
- that scoring behavior for valid inputs is unchanged

## Why This Matters
Without this documentation, future contributors may:
- reintroduce the original crash by “simplifying” the line back to `.get("text", "")`
- misunderstand why `None` must be treated differently from a missing key
- assume the evaluator is brittle against upstream retrieval data

Clear docs protect the reliability of the RAG evaluation pipeline.

## Current State
- The code contains a one-line defensive fix but no explanatory comment or docstring update describing the `None` edge case.
- `PLAN.md` and the PR description contain the reasoning, but that knowledge is not captured next to the code itself.
- Existing tests cover the case, yet a new contributor reading only the source would not understand the failure mode that was fixed.

## Relevant Files
- `rag/evaluator/faithfulness_checker.py` — `check()` method
- `tests/unit/test_faithfulness_checker.py` — regression test for `{"text": None}`
- `PLAN.md` (on the issue branch) — detailed root-cause analysis

## Suggested Improvements
- Add a short comment above the context aggregation line explaining that both missing keys **and** explicit `None` values must be coerced to `""`.
- Optionally expand the `check()` docstring with a brief note about input resilience.
- Keep the comment minimal so it does not clutter the method.

## Acceptance Criteria
- [ ] Documentation is clear, accurate, and follows the existing style
- [ ] Any code examples or commands included are correct and tested
- [ ] The updated documentation is easy for a new contributor to follow
- [ ] Relevant files and references are identified clearly

## Project / Grading Requirements
- [ ] A PR is opened if this work is part of the course workflow
- [ ] The PR description explains what changed and why
- [ ] Any required journal/check-in updates are completed if applicable