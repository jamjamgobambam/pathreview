## Week 7 — Issue selection

<!--   Email: user1@example.com
  Password: password1

  Email: user2@example.com
  Password: password2

  Email: user3@example.com
  Password: password3 -->

**Issue link:** https://github.com/ascherj/pathreview/issues/105

**Issue title:** Add accessibility tests for the review page using `jest-axe`

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The review page (`frontend/src/pages/ReviewPage.tsx`) has no automated
accessibility checks, so regressions like poor color contrast, missing form
labels, or broken heading hierarchy can slip in unnoticed. The page renders
different DOM depending on state — polling/loading, failed, and complete —
so an a11y violation could exist in one state and not another. The fix adds
`jest-axe`-based tests in `frontend/src/pages/__tests__/ReviewPage.test.tsx`
that render each of these states and assert none has detectable a11y
violations. This gives the frontend a regression net for accessibility
across the full lifecycle of one of the app's core screens.

**Acceptance checklist:**
- [ ] `jest-axe`'s `toHaveNoViolations` matcher wired into the test setup
- [ ] Test renders the polling/loading state and asserts zero axe violations
- [ ] Test renders the failed state and asserts zero axe violations
- [ ] Test renders the complete state (with review sections) and asserts zero axe violations
- [ ] All new tests pass via `make test-unit`

**Why this issue fits (scope-fit reasoning):**
- Tier 2, 4–6h estimated effort — matches what I can commit this week
- `jest-axe` is already a devDependency in `frontend/package.json`, so no new
  tooling setup is required, just test code
- The repo already has React Testing Library test patterns to follow
  (`ProfileForm.test.tsx`, `ReviewSection.test.tsx`), so I'm extending an
  established pattern rather than inventing one
- Scope is one new file (`ReviewPage.test.tsx`); no backend, API, or
  component changes needed, keeping blast radius small
- `useReviewStatus` is a mockable hook, so all three render states can be
  driven in tests without a live backend

**Branch name:** test/105-review-page-accessibility-tests

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/thisiswhale/pathreview/commit/7cc60f1eb7d3a1147f97794d75a5551ab537ec4e

**Reproduction summary:**
This is a missing-coverage issue, not a bug, so "reproducing" it meant
confirming the gap: `ls frontend/src/pages/__tests__/` fails (directory
doesn't exist), and `jest-axe` is present only as a devDependency with no
usage anywhere in `frontend/src`. Also confirmed `ReviewPage.tsx` has three
conditionally-rendered states (polling, failed, complete) that would each
need their own axe check, per the plan's Understand section.

**PLAN.md link:** https://github.com/thisiswhale/pathreview/blob/test/105-review-page-accessibility-tests/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
- Whether `jest-axe`'s `toHaveNoViolations` matcher is already registered
  globally in a `setupTests`/`vitest.config.ts` file, or needs adding per-file
- Whether to wrap `ReviewPage` in `MemoryRouter` or mock `react-router-dom`
  directly for `useParams`/`useNavigate` — following whichever existing
  tests already lean toward
- jsdom (used by vitest) doesn't do real layout/paint, so `jest-axe` may not
  catch color-contrast violations in this environment — scoping expectations
  to what's actually testable

  ## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All 5 sub-tasks from PLAN.md's Plan section are implemented and committed
individually in `frontend/src/pages/__tests__/ReviewPage.test.tsx`: (1)
`jest-axe`'s `toHaveNoViolations` matcher wired into global test setup
(`src/test/setup.ts`), (2) test file scaffolded with `react-router-dom` and
`useReviewStatus`/`apiClient` mocks, (3) `jest-axe` checks for the polling,
failed, and complete states, (4) a check for stacked error banners (`error`
+ `fetchError` rendered together), and (5) full suite run — 5/5 tests pass.
Also ran `make check`/`make test-unit` to baseline pre-existing failures
(53 pytest failures, 182 ruff errors, 5 mypy errors, all in Python files
this change never touches) and confirmed no new failures introduced.

**Next steps:**
Open the PR with the pre-existing-failures note in the description, and
resolve the two open questions from Week 8: router mocking approach
(went with mocking `react-router-dom`'s `useParams`/`useNavigate` directly,
no `MemoryRouter`) and matcher registration (went with global, in
`setup.ts`, rather than per-file) — both now resolved by the implementation,
just need to reflect that back into Week 8 if graded together.

**Blockers:**
None currently. One thing to watch: `make format` (black) mutates files in
place rather than just checking — accidentally reformatted 52 unrelated
Python files when I ran `make check` for baselining; reverted with
`git checkout --` before it touched staging. Using `black --check .`
instead going forward to avoid repeating that.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/thisiswhale/pathreview/pull/1

**Branch:** test/105-review-page-accessibility-tests

**What you built:**
Automated accessibility coverage for `ReviewPage` using `jest-axe`, with a
separate check per conditionally-rendered state (polling, failed, complete)
plus one for the stacked polling-error/fetch-error banners, since a
violation could exist in one state and not another.

**Tests added or updated:**
- `frontend/src/pages/__tests__/ReviewPage.test.tsx` (new) — 5 tests: a
  smoke render of the polling state, and `jest-axe` zero-violations checks
  for polling, failed, complete, and stacked-error-banner states
- `frontend/src/test/setup.ts` — registers `jest-axe`'s `toHaveNoViolations`
  matcher globally so any test file can use it

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Both are Python-only and don't cover this frontend-only change; checked
under this codebase's documented-baseline definition — no new failures
introduced. Baselined pre-existing failures before starting (53/428 pytest
failures, 182 ruff errors, 5 mypy errors, 52 unformatted files, all in
Python files this PR never touches — confirmed disjoint from this diff).
Frontend: `npx vitest run` on the new file is 5/5 passing; one pre-existing
frontend failure (`ReviewSection.test.tsx`) and one pre-existing broken
file (`ProfileForm.test.tsx`, missing dep) predate this change too. Full
detail in the PR description.

**Draft PR feedback received from:** none 