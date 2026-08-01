# Module 3 Journal

## Week 7 — Issue Selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/78

**Issue title:** API response for profile creation doesn't include the profile_id field

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
When a client creates a profile via `POST /profiles`, the API returns a
`ProfileResponse` that exposes the record's primary key under the name `id`,
but never under the name `profile_id` that clients rely on for follow-up
requests (for example `GET /profiles/{profile_id}`). The value itself exists on
the database model, but the response schema in `api/schemas/profile.py` doesn't
surface a `profile_id` field, so clients have no field by that name to read. A
successful fix adds `profile_id` to the profile creation response, mapped from
the model's `id`, so the API contract matches what clients expect while keeping
existing behavior intact. This is scoped to the API layer, primarily the
`ProfileResponse` schema.

**Branch name:** `fix/78-profile-response-missing-profile-id`

**Setup confirmation:** [x] App runs locally at localhost:5173.  

**Cohort ledger:** [x] Issue added to cohort ledger

---

### Selection Notes — "Is This Issue Right for Me?" Checklist

*Part 1: Understanding the Issue*

- *In My Own Words*: When a profile is created, the API currently returns the profile identifier as `id` instead of `profile_id`. Since clients need the `profile_id` field for future requests, the response is missing a field they depend on.
- *Part of The App Affected*: This issue is in the API layer, specifically the response schema in `api/schemas/profile.py`. This schema is used by the `POST /profiles` route in `api/routes/profiles.py`. I located and reviewed both files in the repository.
- *Before and After*: Before the fix, `POST /profiles` returns a response containing `{"id": ...}` but does not include `profile_id`. After the fix, the response should include `profile_id` with the profile's identifier.

*Part 2: Tier Fit*

- *Why This Tier Fits*: Tier 1 is the right match because this change is scoped to the `ProfileResponse` schema in a single file. It does not require major changes across different parts of the application or a deep understanding of the entire codebase. For a first open-source contribution, this is a manageable and well-defined issue.

*Part 3: Codebase Readiness*

- *Files Reviewed*: I looked through `ProfileResponse` in `api/schemas/profile.py`, the `Profile` model in `core/models/profile.py` (where the primary key is stored as `id`), and the `create_profile_endpoint` route that creates responses using `ProfileResponse.model_validate(new_profile)`.
- *Important Constraint Discovered*: The schema uses `from_attributes`, meaning new fields need to map to attributes that already exist on the ORM object. Since the model has `.id` but not `.profile_id`, simply adding a `profile_id` field may not work without additional mapping logic.
- *Testing Plan*: There is currently no dedicated profile test file under `tests/unit/`, so I plan to add tests for this behavior while following the structure of existing test files, such as `tests/unit/test_review_service.py`.

*Part 4: Scope And Time*

- *Estimated Effort*: The issue is estimated at 1–2 hours, plus time for writing tests, which makes it achievable before the Week 9 deadline.
- *Blockers or Dependencies*: No blockers or external dependencies are mentioned in the issue.
- *Claim Status*: I commented on the issue to claim it. The cohort ledger entry is still pending because I am waiting for the ledger link, and I will complete it before starting Week 8.

---

## Week 8 — Reproduction & Solution Planning

**Reproduction commit link:** https://github.com/sehr-abrar/pathreview/commit/35edb900b56be115e46fc8ac91c9386f707a0d56


**Reproduction summary:**
I reproduced the issue with a new failing test, `tests/unit/test_profile_schema.py`,
which validates a Profile-like object through `ProfileResponse` and asserts the
serialized payload contains a `profile_id` field. Running
`pytest tests/unit/test_profile_schema.py` fails with
`AssertionError: ProfileResponse is missing the 'profile_id' field (issue #78)`,
and the dumped payload confirms the response contains `id` but no `profile_id`.

**PLAN.md link:** https://github.com/sehr-abrar/pathreview/blob/fix/78-profile-response-missing-profile-id/PLAN.md

**Walkthrough video (recommended):** N/A — not recorded.

**Blockers or open questions:**
One open question for implementation (not a blocker): whether to keep the existing
`id` field alongside the new `profile_id` or replace it. My current plan keeps both
for backward compatibility, pending a quick check of `frontend/src/` for existing
consumers of `.id`.

---

## Week 9 — Solution Building & PR Submission

### Check-in 1 (mid-week)

**Current progress:**
- Sub-task 1 (reproduction) — done in Week 8: `tests/unit/test_profile_schema.py`.
- Sub-task 2 (expose `profile_id`) — done: added a Pydantic `@computed_field`
  property `profile_id` to `ProfileResponse` in `api/schemas/profile.py` that
  returns `self.id`, keeping the existing `id` field.
- Sub-task 3 (verify the shared schema / route layer) — done: confirmed
  `ProfileResponse` is reused by the create, get, and update endpoints in
  `api/routes/profiles.py`, so all three now include `profile_id` (additive).
- Resolved the Week 8 open question: searched `frontend/src/` and found
  `ProfileForm.tsx` reads `profile.id` from the create response, so replacing
  `id` would break the frontend. Decision: keep `id`, add `profile_id`.

**Next steps:**
- Expand test coverage (sub-task 4): backward-compat (`id` still present), UUID
  JSON serialization, and optional-fields-null cases — then finalize the PR.
- Open a draft PR and request peer feedback before marking ready.

**Blockers:**
None. Note: the repo has pre-existing `make check` and `make test-unit` failures
in unrelated modules (see Check-in 2); confirmed my changes don't add to them.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/jamjamgobambam/pathreview/pull/144

**Branch:** `fix/78-profile-response-missing-profile-id`

**What you built:**
Added a `profile_id` field to the `ProfileResponse` schema
(`api/schemas/profile.py`) via a Pydantic `@computed_field` that returns the
existing `id` value. Profile responses (create, get, and update, which share the
schema) now include `profile_id` for clients while keeping `id` unchanged, so no
existing consumer breaks.

**Tests added or updated:**
Added `tests/unit/test_profile_schema.py` (5 tests) covering: `profile_id` is
present in the serialized response; `profile_id` equals both the source `id` and
the response `id`; `id` is still present (backward compatibility); `profile_id`
serializes to the same UUID string as `id` in JSON; and `profile_id` is returned
even when all optional fields (`github_username`, `portfolio_url`,
`resume_filename`) are `None`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> Note on "passes": the repo has documented pre-existing failures on `main`
> unrelated to this issue — `make check` reports ~161 ruff errors (e.g.
> `test_tech_detector.py`, `test_skill_extractor.py`) and `make test-unit`
> reports 55 failing tests, in modules this PR does not touch. After my changes
> the counts do not increase (unit failures: 55 → 53; my 5 new tests pass), so
> my contribution introduces no new failures. My two changed files
> (`api/schemas/profile.py`, `tests/unit/test_profile_schema.py`) individually
> pass ruff, black, and mypy.

**Draft PR feedback received from:** None

---

## Week 10 — Iteration & Reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]

**How you responded:**
[What changes did you make, or what did you reply? If no feedback, leave blank.]

---

### Reflection

**What was harder than you expected?**
Finding the relevant code was harder than the fix itself. Before I could plan
anything I had to search the codebase to confirm where the bug actually lived and
trace the path from the `ProfileResponse` schema to the `Profile` model to the route
in `api/routes/profiles.py`. I expected the "hard part" to be writing the fix, but
the actual code change ended up being a few lines. The real work was locating the
right file and understanding how the pieces connected well enough to be sure a change
wouldn't break something else.

**What did you learn about working in a large codebase?**
That documentation matters more than pure coding. On my own projects I mostly just
write code, but here the fix was tiny and most of my effort went into the JOURNAL,
the PLAN, and the PR description, plus following someone else's conventions (branch
naming, conventional commit messages, and the pre-commit hooks). Contributing to
someone else's production code means fitting into their standards and proving your
change is safe, not just making it work on your machine. A good example was deciding
to keep the existing `id` field instead of replacing it, which I only felt confident
about after checking that the frontend reads `profile.id`.

**How did AI tools help — and where did they fall short?**
This was my first time contributing to open source, and AI was most useful as a guide
through the parts I had never done before: the fork vs. upstream git workflow, reading
an unfamiliar multi-service codebase quickly, and understanding why the pre-commit
mypy hook failed when my local mypy passed. Where it fell short was the actual
decisions. I still had to choose which issue to take, decide to keep `id` for backward
compatibility, and judge that the pre-existing test failures were unrelated to my
change and safe to document rather than fix. AI could surface the options, but the
calls were mine to make.

**What would you do differently if you started over?**
I would probably take a more challenging issue. Now that I have seen how straightforward
the overall process is once you understand the workflow, a Tier 1 fix felt very
contained. Starting over, I would pick something closer to Tier 2 that touches more than
one module, since the parts that intimidated me (git, conventions, reproducing the issue)
turned out to be the manageable parts.

**What are you most proud of from this module?**
Contributing to open source for the first time. Going from never having opened a PR on
someone else's project to a complete, standards-following contribution with tests and
documentation is the thing I am most proud of.

