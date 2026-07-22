# Core Service Docstrings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add accurate Google-style docstrings to every public function currently present in `core/services/` without changing application behavior.

**Architecture:** Keep the change documentation-only in the two existing service modules. Add a small AST-based unit test that validates docstring structure without importing the application or requiring database services, then update the four public profile functions and four public review functions in separate reviewable commits.

**Tech Stack:** Python 3.11+, `ast`, pytest, Ruff, Black, mypy, SQLAlchemy async-session semantics.

## Global constraints

- Follow issue #119: public service functions need Google-style descriptions plus `Args`, `Returns`, and accurate `Raises` documentation.
- Do not change function signatures, database queries, status transitions, exception handling, or other runtime behavior.
- Do not create `core/services/notification_service.py`; it is named by the issue but does not exist in the current checkout.
- Exclude private helpers whose names begin with `_` from issue scope.
- Use the repository's Conventional Commit format and run `make check && make test-unit` before Week 9 submission.

---

## Solution plan

**Issue:** [Add inline docstrings to all public methods in `core/services/`](https://github.com/ascherj/pathreview/issues/119)

### Understand

The eight public async functions in `core/services/profile_service.py` and `core/services/review_service.py` already have short descriptions, but they do not document parameters, return values, or propagated failures in the repository's required Google style. The local reproduction in `REPRODUCTION.md` uses Python's AST to inspect all public top-level functions and reports `public_functions=8 failures=8` because every function is missing `Args:`, `Returns:`, and `Raises:` markers.

Expected behavior is complete, semantically accurate developer documentation with no runtime changes. Most functions can propagate SQLAlchemy session failures; `delete_profile` rolls back and re-raises caught exceptions, while `process_review` catches ordinary processing exceptions and records/logs failure instead of propagating them.

### Map

- Create `tests/unit/test_service_docstrings.py`: AST-only regression coverage for public service docstrings; no application imports or external services.
- Modify `core/services/profile_service.py:13`: `create_profile` docstring.
- Modify `core/services/profile_service.py:36`: `get_profile` docstring.
- Modify `core/services/profile_service.py:51`: `update_profile` docstring.
- Modify `core/services/profile_service.py:75`: `delete_profile` docstring.
- Modify `core/services/review_service.py:15`: `create_review` docstring.
- Modify `core/services/review_service.py:35`: `get_review` docstring.
- Modify `core/services/review_service.py:50`: `list_reviews` docstring.
- Modify `core/services/review_service.py:82`: `process_review` docstring.
- Reference `core/database.py:18`: confirms service callers provide an async SQLAlchemy session.
- Reference `api/routes/profiles.py` and `api/routes/reviews.py`: confirms how IDs, schemas, return values, and the background `process_review` task are consumed.
- Reference `docs/CONTRIBUTING.md`: defines Google-style docstrings and the required verification commands.

### Plan

#### Task 1: Add a failing structural docstring test

**Files:**

- Create: `tests/unit/test_service_docstrings.py`
- Inspect: `core/services/profile_service.py`
- Inspect: `core/services/review_service.py`

**Interfaces:**

- Consumes: Python source files under `core/services/`.
- Produces: pytest assertions that every public top-level function has a description, `Args:`, and `Returns:`, plus `Raises:` when ordinary exceptions can propagate.

- [ ] **Step 1: Create the AST-based test.**

```python
"""Structural tests for public service docstrings."""

import ast
from pathlib import Path

import pytest

SERVICE_DIR = Path("core/services")
NO_PROPAGATED_EXCEPTIONS = {"review_service.py:process_review"}


def _public_functions(path: Path) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Return public top-level functions declared in a Python module."""
    tree = ast.parse(path.read_text())
    return [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    ]


@pytest.mark.unit
def test_public_service_functions_have_google_style_docstrings() -> None:
    """Require descriptions and input/output sections on public services."""
    discovered = 0

    for path in sorted(SERVICE_DIR.glob("*.py")):
        for function in _public_functions(path):
            discovered += 1
            docstring = ast.get_docstring(function)
            qualified_name = f"{path.name}:{function.name}"

            assert docstring, f"{qualified_name} has no docstring"
            assert docstring.splitlines()[0].strip(), (
                f"{qualified_name} has no summary description"
            )
            assert "\nArgs:" in docstring, f"{qualified_name} has no Args section"
            assert "\nReturns:" in docstring, (
                f"{qualified_name} has no Returns section"
            )

            if qualified_name not in NO_PROPAGATED_EXCEPTIONS:
                assert "\nRaises:" in docstring, (
                    f"{qualified_name} has no Raises section"
                )

    assert discovered == 8, f"expected 8 public service functions, found {discovered}"
```

- [ ] **Step 2: Run the focused test and verify the reproduction remains red.**

Run:

```bash
.venv/bin/pytest tests/unit/test_service_docstrings.py -v
```

Expected: one failing test whose first assertion identifies `profile_service.py:create_profile` as missing `Args:`. The failure proves the test detects the reproduced gap before docstrings are changed.

- [ ] **Step 3: Commit the red test.**

```bash
git add tests/unit/test_service_docstrings.py
git commit -m "test: require Google-style service docstrings"
```

#### Task 2: Document the public profile service functions

**Files:**

- Modify: `core/services/profile_service.py:13-104`
- Test: `tests/unit/test_service_docstrings.py`

**Interfaces:**

- Consumes: `AsyncSession`-compatible `db`, UUID ownership identifiers, `ProfileCreate`, and `ProfileUpdate`.
- Produces: unchanged `Profile`, `Profile | None`, and `bool` runtime results with accurate developer-facing contracts.

- [ ] **Step 1: Replace the four short profile docstrings with these Google-style contracts.**

```python
"""Create and persist a profile for a user.

Args:
    db: Async SQLAlchemy session used to persist the profile.
    user_id: Unique identifier of the user who owns the profile.
    data: Validated GitHub username and portfolio URL values.
    resume_filename: Original resume filename, or None when unavailable.
    resume_text: Extracted resume text, or None when unavailable.

Returns:
    The newly persisted and refreshed profile.

Raises:
    SQLAlchemyError: If the profile cannot be committed or refreshed.
"""
```

```python
"""Return a profile when it exists and belongs to the requesting user.

Args:
    db: Async SQLAlchemy session used to query profiles.
    profile_id: Unique identifier of the profile to retrieve.
    user_id: Unique identifier of the expected profile owner.

Returns:
    The matching profile, or None when no owned profile is found.

Raises:
    SQLAlchemyError: If the profile query fails.
"""
```

```python
"""Update editable fields on a profile owned by the requesting user.

Args:
    db: Async SQLAlchemy session used to query and persist the profile.
    profile_id: Unique identifier of the profile to update.
    user_id: Unique identifier of the expected profile owner.
    data: Validated profile fields; None-valued fields remain unchanged.

Returns:
    The refreshed profile, or None when no owned profile is found.

Raises:
    SQLAlchemyError: If querying, committing, or refreshing fails.
"""
```

```python
"""Delete an owned profile and its reviews and ingested sources.

Args:
    db: Async SQLAlchemy session used for the cascade deletion.
    profile_id: Unique identifier of the profile to delete.
    user_id: Unique identifier of the expected profile owner.

Returns:
    True when the profile is deleted, or False when it is not found.

Raises:
    Exception: Re-raised after rollback if a delete or commit operation fails.
"""
```

- [ ] **Step 2: Run the focused test.**

Run:

```bash
.venv/bin/pytest tests/unit/test_service_docstrings.py -v
```

Expected: still FAIL because the public functions in `review_service.py` remain undocumented. No profile-service function should appear in the failure.

- [ ] **Step 3: Commit the profile documentation.**

```bash
git add core/services/profile_service.py
git commit -m "docs: document public profile services"
```

#### Task 3: Document the public review service functions

**Files:**

- Modify: `core/services/review_service.py:15-168`
- Test: `tests/unit/test_service_docstrings.py`

**Interfaces:**

- Consumes: `AsyncSession`-compatible `db`, review/profile/user UUIDs, and pagination integers.
- Produces: unchanged `Review`, `Review | None`, `tuple[list[Review], int]`, and `None` runtime results with accurate status/error-handling documentation.

- [ ] **Step 1: Replace the four short review docstrings with these Google-style contracts.**

```python
"""Create and persist a pending review for a profile.

Args:
    db: Async SQLAlchemy session used to persist the review.
    profile_id: Unique identifier of the profile being reviewed.
    user_id: Identifier of the authenticated user initiating the review.

Returns:
    The newly persisted and refreshed pending review.

Raises:
    SQLAlchemyError: If the review cannot be committed or refreshed.
"""
```

```python
"""Return a review when its profile belongs to the requesting user.

Args:
    db: Async SQLAlchemy session used to query reviews.
    review_id: Unique identifier of the review to retrieve.
    user_id: Unique identifier of the expected profile owner.

Returns:
    The matching review, or None when no owned review is found.

Raises:
    SQLAlchemyError: If the review query fails.
"""
```

```python
"""Return one page of a user's reviews and the unpaginated count.

Args:
    db: Async SQLAlchemy session used to query reviews.
    user_id: Unique identifier of the profile owner.
    page: One-based page number used to calculate the query offset.
    page_size: Maximum number of reviews returned on the page.

Returns:
    A tuple containing the page of reviews and total matching review count.

Raises:
    SQLAlchemyError: If either review query fails.
"""
```

```python
"""Process a review through ingestion, analysis, RAG, and safety checks.

The review advances from pending to processing and then to complete. Missing
records, failed safety checks, and caught processing errors leave or set the
review to failed and are logged instead of being propagated to the caller.

Args:
    db: Async SQLAlchemy session used throughout review processing.
    review_id: Unique identifier of the review being processed.
    profile_id: Unique identifier of the source profile.

Returns:
    None.
"""
```

- [ ] **Step 2: Run the focused test and verify it turns green.**

Run:

```bash
.venv/bin/pytest tests/unit/test_service_docstrings.py -v
```

Expected: PASS with one test passed and no external services required.

- [ ] **Step 3: Commit the review documentation.**

```bash
git add core/services/review_service.py
git commit -m "docs: document public review services"
```

#### Task 4: Verify documentation quality and repository compatibility

**Files:**

- Verify: `core/services/profile_service.py`
- Verify: `core/services/review_service.py`
- Verify: `tests/unit/test_service_docstrings.py`
- Update after implementation: `PLAN.md` and `JOURNAL.md`

**Interfaces:**

- Consumes: the completed docstrings and structural test from Tasks 1–3.
- Produces: formatter-, linter-, type-checker-, and unit-test evidence suitable for the Week 9 journal and pull request.

- [ ] **Step 1: Confirm the semantic AST regression test reports no undocumented public functions.**

Run:

```bash
.venv/bin/pytest tests/unit/test_service_docstrings.py -v
```

Expected: PASS. The original reproduction audit in `REPRODUCTION.md` intentionally mirrors the issue's literal all-sections wording; the regression test applies the semantically accurate exception for `process_review`, which catches ordinary processing exceptions instead of propagating them.

- [ ] **Step 2: Run the repository's complete required checks.**

```bash
make check && make test-unit
```

Expected: Ruff, Black, mypy, and all unit tests exit 0.

- [ ] **Step 3: Review the final diff for documentation-only scope.**

```bash
git diff main...HEAD -- core/services tests/unit/test_service_docstrings.py
git diff --check
```

Expected: only the new structural test and docstring bodies differ; no function signature, query, status transition, or control-flow change appears, and `git diff --check` exits 0.

- [ ] **Step 4: Record final commands and any plan changes in the Week 9 journal entry, then commit.**

```bash
git add PLAN.md JOURNAL.md
git commit -m "docs: record issue 119 implementation results"
```

### Inputs & outputs

**Inputs:** The eight existing public async functions, their current parameters and annotations, SQLAlchemy session behavior, UUID ownership identifiers, profile schemas, review status transitions, and the repository's Google-style documentation requirement.

**Outputs:** Complete public-function docstrings that state purpose, parameter meaning, return semantics, and genuinely propagated exceptions; an AST-based unit test that prevents regression; no changes to function signatures, return values, database behavior, or API behavior.

### Risks & unknowns

- `core/services/notification_service.py` is named in issue #119 but absent from the branch. Creating it would expand a documentation issue into a new feature, so the plan excludes it; confirm with the maintainer if that file was renamed or omitted accidentally.
- The issue wording lists `Raises` for all methods, but `process_review` catches ordinary `Exception` instances and records failure internally. Adding a false `Raises` section would be misleading, so the plan documents its suppression behavior and exempts only that function from the structural `Raises:` assertion unless maintainers require an explicit no-propagation convention.
- `create_review` accepts `user_id` but does not read it. The docstring must describe it as caller context without claiming the function currently performs an ownership check; changing that behavior is outside issue #119.
- SQLAlchemy may wrap driver-specific failures as different subclasses. Use `SQLAlchemyError` as the public documentation boundary for uncaught query/commit/refresh failures, and do not promise narrower exception classes without a targeted failure test.
- `resume_filename` and `resume_text` default to `None` despite being annotated as `str`. Document the observed optional behavior but leave annotation cleanup for a separately scoped issue.

### Edge cases

- `get_profile`, `update_profile`, and `get_review` return `None` for missing or non-owned records; docstrings must not imply these cases raise not-found errors.
- `delete_profile` returns `False` when the profile is absent but rolls back and re-raises operational failures during the cascade.
- `list_reviews` can return an empty list with total `0`, and its total is calculated before pagination.
- `process_review` can return early for a missing review, set failed for a missing profile or failed safety check, and catch/log processing failures without propagating them.
- Optional resume values and partially populated `ProfileUpdate` values must be described without implying fields are always present.
- Private `_run_ingestion_pipeline`, `_run_agent_orchestration`, `_run_rag_retrieval_generation`, and `_run_safety_checks` helpers remain outside public-method scope.
- Any future public function added under `core/services/` should be discovered automatically by the AST regression test and held to the same documentation contract.
