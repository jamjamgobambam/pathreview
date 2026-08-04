# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/93

**Issue title:** Review history page displays dates in UTC instead of the user's local timezone

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Review creation timestamps are stored and returned by the backend in UTC, and
the review history page renders them without converting to the viewer's local
timezone. As a result a review created at 11:00 PM EST is shown as 4:00 AM the
next day, so the listed date can be wrong for anyone not on UTC. The relevant
code lives in the frontend — `frontend/src/utils/dateFormatters.ts` (the
`formatDate`/`formatRelativeDate` helpers) and `frontend/src/pages/ReviewHistory.tsx`,
which consumes them. A successful fix parses the incoming timestamps as UTC and
formats them in the browser's local timezone so the displayed date matches what
the user actually experienced.

**Branch name:** fix/93-review-history-local-timezone

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/umacy/pathreview/commit/914ba39

**Reproduction summary:**
I added a Vitest reproduction (`frontend/src/utils/__tests__/dateFormatters.test.ts`)
that pins a non-UTC timezone and feeds `formatDate` the exact offset-less UTC
string the API returns (`datetime.utcnow()` serializes with no `Z`); the tests
assert the correct local day and currently FAIL — `formatDate('2026-07-12T03:00:00')`
returns `Jul 12, 2026` when it should return `Jul 11, 2026`, confirming
`new Date()` parses the naive string as local time and shifts the calendar day.

**PLAN.md link:** https://github.com/umacy/pathreview/blob/fix/93-review-history-local-timezone/PLAN.md

**Blockers or open questions:**
Deciding whether to also fix the backend to emit timezone-aware UTC (`...Z`) or
keep the fix frontend-only; the frontend helper will be written to be idempotent
either way. Also need to confirm every date-rendering consumer routes through
these helpers so no display is missed.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in `frontend/src/utils/dateFormatters.ts`: added a
`parseIsoAsUtc` helper that appends `Z` to timezone-less ISO strings (only when
no `Z`/`±hh:mm` designator is present, so it's idempotent) and routed both
`formatDate` and `formatRelativeDate` through it. The Week 8 reproduction tests
now pass. PLAN.md sub-tasks 1 (normalize to UTC) and 2 (extend tests) are done.

**Next steps:**
Broaden the test suite (explicit-offset and relative-date cases — done), verify
in the running app, and confirm `make check` / `make test-unit` show no new
failures against the documented pre-existing baseline. Then open a draft PR for
peer review.

**Blockers:**
Discovered that setting `process.env.TZ` in a Vitest `beforeAll` does not change
V8's cached timezone, so timezone-pinned assertions were unreliable. Resolved by
rewriting the tests to assert timezone-agnostic invariants (naive form must equal
the explicit-`Z` form), which hold on any machine.

---

### Check-in 2 (end of week)

**PR link:** PR_LINK_PLACEHOLDER

**Branch:** `fix/93-review-history-local-timezone`

**What you built:**
A frontend fix for review-history dates showing on the wrong day for non-UTC
users. The API returns UTC timestamps without an offset (from
`datetime.utcnow()`), which `new Date()` parsed as local time; the fix normalizes
timezone-less ISO strings to UTC before formatting, so dates render on the
correct day in the viewer's local zone.

**Tests added or updated:**
`frontend/src/utils/__tests__/dateFormatters.test.ts` — six cases covering: a
naive-UTC string rendering on the correct local day, naive-vs-`Z` equivalence,
idempotence for already-`Z` strings, explicit `+hh:mm` and `-hh:mm` offsets left
unadjusted, and `formatRelativeDate` bucketing/equivalence. All pass; verified to
fail against the pre-fix code.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> Note on "passes": this repo has documented pre-existing failures unrelated to
> this issue. Baseline before my changes — `make test-unit`: 53 failed / 375
> passed; `make check`: 182 ruff errors, 52 files black-would-reformat. After my
> changes the counts are **identical** (my change is frontend TypeScript only,
> which `make check`/`make test-unit` do not cover), so this PR introduces **no
> new failures**. On the frontend, `ProfileForm.test.tsx` (missing
> `@testing-library/user-event` dep) and one `ReviewSection.test.tsx` case fail
> on the clean baseline too — proven by stashing my changes — and are untouched
> by this PR. My own test file passes 6/6.

**Draft PR feedback received from:** none (peer review pending in Slack)

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No substantive reviewer feedback came in before this final journal entry. The
PR was prepared with a detailed summary, testing notes, and reviewer guidance,
but peer review was still pending.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The hardest part was not the code change itself, but proving the exact failure
mode with confidence. Timezone bugs look simple at first, but the real issue was
the interaction between Python emitting a naive UTC timestamp and JavaScript
parsing that offset-less string as local time. It also took more effort than I
expected to build a stable reproduction because test environments cache timezone
state in ways that make naive timezone-forcing unreliable.

**What did you learn about working in a large codebase?**
I learned that even a small fix has to be justified in terms of system behavior,
not just local code. In my own projects I can change an implementation quickly
and move on, but in someone else's codebase I had to trace where the data was
produced, how it was serialized, where it was rendered, and whether a frontend
or backend fix was the safer scope for the current issue. I also had to account
for existing failing checks and separate baseline noise from regressions caused
by my change.

**How did AI tools help — and where did they fall short?**
AI was most useful for speeding up exploration, summarizing likely code paths,
and helping draft targeted tests and PR documentation once I understood the bug.
Where it fell short was in the parts that required precise judgment: validating
timezone semantics, deciding what counted as a trustworthy regression test, and
distinguishing repo-specific baseline failures from new problems. For those
steps, I still had to verify behavior manually and reason from the actual code
and tool output.

**What would you do differently if you started over?**
I would create the failing reproduction even earlier and treat it as the anchor
for the whole issue. I spent time thinking through multiple fix locations before
the test made the failure mode undeniable. I would also document the baseline
failures sooner so validation results were easier to explain once the PR was
ready.

**What are you most proud of from this module?**
I'm most proud of turning a subtle user-facing bug into a small, precise fix
with a solid regression test and a clear explanation of why the change is
correct.
