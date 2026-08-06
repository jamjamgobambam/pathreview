## Solution plan

**Issue:** Issue 119: Add inline docstrings to all public methods in core/services/

**Link**: https://github.com/ascherj/pathreview/issues/119

### Understand

What is the root cause of this issue? What behavior is expected vs. actual?

The root cause is a documentation gap, not a runtime defect. Every public function in the
service layer carries only a one-line summary docstring with no structured account of its
arguments, return values, or failure modes. As a result, callers (the API route layer)
cannot tell from the docstrings which functions raise, which return sentinel values
(`None`/`False`), or which mutate transaction state.

- **Expected:** each public service function reads as self-documenting — a Google-style
  docstring covering description, `Args`, `Returns`, and `Raises`, where `Raises` honestly
  distinguishes functions that genuinely raise from pure reads that only surface underlying
  database errors.
- **Actual:** one-line summaries only. Load-bearing behaviors are undocumented — e.g.
  `get_profile` collapses "not found" and "not owned" into a silent `None`, `create_profile`
  can raise on `commit` without rolling back, and `delete_profile` re-raises after a rollback.

### Map

Which files, functions, or modules are involved?
List the specific files you expect to touch.

Two modules, eight public functions in scope:

- `core/services/profile_service.py`
  - `create_profile` — write (commit; no rollback)
  - `get_profile` — pure read
  - `update_profile` — read-then-write (commit; no rollback)
  - `delete_profile` — cascade write (rollback-then-reraise)
- `core/services/review_service.py`
  - `create_review` — write (commit; no rollback)
  - `get_review` — pure read
  - `list_reviews` — pure read (paginated, returns a tuple)
  - `process_review` — background task (swallows all exceptions; never propagates)

Out of scope by default: the private `_run_*` helpers in `review_service.py` (see Risks).
No non-docstring code changes; call sites in `api/routes/` are unaffected.

### Plan

What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. **Compare if there are any other docstrings in this repo**: Would help to understand the format I should explain the functions.
2. **Classify each function into a failure bucket** (drives the `Raises` text): pure read /
   write-no-rollback / rollback-then-reraise / swallow-all. Verify against the actual
   `commit()` and `try/except` boundaries, not assumptions.
3. **Write docstrings for `profile_service.py`** (4 functions), typing `db` as `AsyncSession`
   so "underlying database errors" has a concrete referent.
4. **Write docstrings for `review_service.py`** (4 public functions), being explicit that
   `process_review` records `status="failed"` instead of raising.
5. **Verify accuracy** — re-read each docstring against its function body; confirm no invented
   exceptions and no omitted sentinel-return behavior.
6. **Confirm nothing else broke** — imports still resolve, no signature changes; optionally
   run the existing test suite.

### Inputs & outputs

What does your fix take as input? What should it produce or change?

- **Input:** the current source of both service modules (function signatures + bodies) and the
  confirmed runtime behavior (reproduced via the API and a direct `get_profile` call).
- **Output:** the same two files with each public function's one-line docstring replaced by a
  complete Google-style docstring (description, `Args`, `Returns`, `Raises`). No behavior,
  signature, or control-flow changes — documentation only.

### Risks & unknowns

What could go wrong? What are you still unsure about?

- **Scope of the `_run_*` helpers:** the issue says "public methods," so the four private helpers
  are excluded — but `process_review`'s contract references them, and `_run_ingestion_pipeline`
  genuinely can raise on its final unguarded `commit()`. Open question: document them too
  (one-liner + `Returns`) for coherence, or leave strictly to scope?
- **Signature nit vs. docstring:** `resume_filename: str = None` / `resume_text: str = None`
  should really be `Optional[str] = None`. That's a code fix, not a docstring — flag to the
  maintainer rather than silently change it here.
- **Over-claiming in `Raises`:** the main risk is inventing exceptions the code can't throw, or
  labeling a pure read as raising. Mitigated by step 4 (verify against the body).

### Edge cases

What inputs or states should your fix handle gracefully?

The docstrings must accurately describe how each function handles these states:

- **Not found vs. not owned** (`get_profile`, `update_profile`, `get_review`): both collapse to
  `None` — the caller cannot distinguish them.
- **Delete of a missing profile** (`delete_profile`): returns `False`, does not raise.
- **Commit failure mid-cascade** (`delete_profile`): rolls back and re-raises.
- **Background-task failure** (`process_review`): caught and recorded as `status="failed"`; never
  propagates to the caller.
- **Empty result sets** (`list_reviews`): returns `([], 0)`, not an error.
- It should be a matter of crawling through each function and seeing the conditionals if it accounts for those cases.
