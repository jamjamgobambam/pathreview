# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/97

**Issue title:** Review progress indicator doesn't update in real time during long-running reviews

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
When a portfolio review is running, the review page only shows a static spinner
with the text "Analyzing your portfolio...", so the user gets no sense of how far
along the review actually is. A previous change replaced a real progress bar with
this spinner, even though the backend already reports progress: the
`GET /reviews/{id}/status` endpoint (in `api/routes/reviews.py`) returns a
`progress_pct` field, and the `useReviewStatus` hook already polls that endpoint
every few seconds. The gap is on the frontend — the `Review` type
(`frontend/src/types/index.ts`) doesn't include `progress_pct`, so the value is
dropped, and `ReviewPage.tsx` renders the spinner instead of a progress bar. A
successful fix threads `progress_pct` through the type and the `useReviewStatus`
hook and renders a live, percentage-driven progress bar during the polling state,
restoring meaningful real-time feedback for long-running reviews.

**Branch name:** fix/97-review-progress-indicator

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

### "Is this right for me?" — checklist reasoning

- **Scope is bounded and understood.** The fix is concentrated in two frontend
  files (`frontend/src/pages/ReviewPage.tsx`, `frontend/src/hooks/useReviewStatus.ts`)
  plus a small type addition in `frontend/src/types/index.ts`. The backend already
  emits `progress_pct`, so no API or database changes are required — this is
  primarily wiring an existing value through to the UI.
- **I can reproduce and explain it.** I traced the data flow end to end: backend
  returns `progress_pct` → hook polls the status endpoint every 3s → page ignores
  the field and shows a static spinner. That gives me a clear before/after.
- **Tier awareness and skill fit.** This is labeled **Tier 3** (advanced,
  estimated 5–8 hours), which is above the Tier 1 starting point recommended for a
  first contribution. I'm comfortable taking it because the work is frontend React/
  TypeScript — an area I'm confident in — and my end-to-end trace showed the hard
  part (backend progress reporting) is already done, leaving a bounded UI wiring
  task. The main risk is scope creep around "real-time" expectations, so I'm
  keeping the goal narrow: surface the existing `progress_pct` in a progress bar
  during polling, not redesign the review pipeline or add websockets.
- **Open questions / risks to watch:** confirm `progress_pct` is populated during
  processing (not just 0 → 100); decide on graceful fallback if the field is
  missing; add/adjust a test for the hook. These are contained and don't expand
  the blast radius.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Nothoon/pathreview/commit/de1aa0d8928f011e517a0dbbfd976eb1b1e2d7e7

**Reproduction summary:**
I added `tests/repro_issue_97.py`, a stdlib-only script that statically inspects
every file on the progress-reporting path and asserts each gap. Running
`python tests/repro_issue_97.py` reports 4/4 checks FAIL, confirming the issue:
`progress_pct` is dropped at every layer — the `Review` model has no such column,
`process_review` never writes progress, so `get_review_status`'s
`getattr(review, "progress_pct", 0)` is always `0`, the frontend `Review` type
omits the field, and `ReviewPage` renders a static spinner during polling.

**PLAN.md link:** https://github.com/Nothoon/pathreview/blob/fix/97-review-progress-indicator/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
Reproduction revealed the fix is broader than the Week 7 frontend-only framing:
the backend reports `progress_pct: 0` on every poll, so the bar would sit at 0%
until complete unless `process_review` emits progress per pipeline stage. Open
question for a mentor: are coarse per-stage milestones (5 fixed values) an
acceptable scope, or is finer progress expected?

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Sub-tasks 1–3 of the five in PLAN.md are done, plus most of 4:

- **Plan step 1 — backend: persist progress.** Added a `progress_pct`
  `Mapped[int]` column to `Review` in `core/models/review.py` with
  `default=0` / `server_default="0"`, and wrote the matching migration
  `alembic/versions/003_add_progress_pct_to_reviews.py`. The server default was
  the risk I flagged in PLAN.md — existing `reviews` rows now read `0` instead of
  `NULL`, so nothing downstream has to handle a missing value.
- **Plan step 2 — backend: emit progress.** `process_review` in
  `core/services/review_service.py` now commits progress at the five milestones
  named in the plan (processing 10, ingestion 35, agent orchestration 60, RAG 85,
  complete 100) through a new `_set_progress` helper that clamps to 0–100. I also
  removed the now-pointless `getattr(review, "progress_pct", 0)` fallback in
  `api/routes/reviews.py::get_review_status`, so the endpoint reads the real
  column.
- **Plan step 3 — frontend: thread the type.** Added `progress_pct?: number` to
  the `Review` interface in `frontend/src/types/index.ts`. No change was needed
  in `useReviewStatus.ts` — it stores the whole `Review`, so the value survives
  to consumers once the type admits it.
- **Plan step 4 — frontend: render the bar (done, still eyeballing styling).**
  The `isPolling` block in `frontend/src/pages/ReviewPage.tsx` now renders a
  percentage-driven bar instead of the static spinner, reusing the existing
  overall-score bar markup, and falls back to the spinner when `progress_pct` is
  absent.

`python tests/repro_issue_97.py` now reports 4/4 PASS (it reported 4/4 FAIL in
Week 8), which is the clearest signal so far that the whole path is wired.

**Next steps:**
Finish plan step 5 (verification): write the unit tests asserting progress
advances during `process_review`, run `make check` and `make test-unit` and
compare them against the pre-change baseline, then open the draft PR, ask for
peer review in Slack, and fill in the PR template.

**Blockers:**
The mentor question from Week 8 (coarse milestones vs. finer progress) is still
unanswered, so I'm shipping the five fixed milestones I planned and calling that
out explicitly in the PR description for the reviewer to push back on.

Two environment notes, neither blocking: this checkout had no `.venv`, so I had
to run `make setup`'s install step before I could run any checks; and `node` is
not installed on this machine, so I verified the frontend change by reading the
rendered JSX path and its type-checking rather than by running `npm test`.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/814

**Branch:** `fix/97-review-progress-indicator`

**What you built:**
Review progress is now reported end to end instead of being dropped at every
layer. `process_review` persists a `progress_pct` value on the new `reviews`
column at five pipeline milestones (10/35/60/85/100), `GET /reviews/{id}/status`
returns that live column instead of a hardcoded `0`, and `ReviewPage` renders a
percentage-driven progress bar during polling — clamped to 0–100, snapped to 100
on completion, and falling back to the old spinner when the field is absent.

**Tests added or updated:**
`tests/unit/test_review_service.py` — added a `TestReviewProgress` class (8
tests) covering: `process_review` committing the exact milestone sequence
10 → 35 → 60 → 85 → 100 in order; progress never decreasing and staying inside
0–100; the review ending at `status="complete"` with `progress_pct=100`; at least
three distinct intermediate values being observable mid-run (the direct
regression guard for #97, where every poll returned `0`); a review failed by
safety checks keeping its partial progress instead of jumping to 100;
`create_review` starting a new review at `progress_pct=0`; and `_set_progress`
clamping out-of-range values (150 → 100, −20 → 0) and committing so polls can
observe the value.

`tests/repro_issue_97.py` — the Week 8 reproduction script now reports 4/4 PASS
instead of 4/4 FAIL (unchanged file, used as a before/after check).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Both boxes reflect the "no new failures" standard for a codebase with documented
pre-existing failures. Measured on `9e32d4c` (the commit before my changes) and
again on the branch tip:

| Command | Before | After |
| --- | --- | --- |
| `ruff check .` (`make lint`) | 182 errors | 182 errors |
| `black --check .` | 53 files would reformat | 53 files would reformat (none of them mine) |
| `mypy api/ core/ ingestion/ rag/ agent/ safety/` | 5 errors in 4 files | 5 errors in 4 files |
| `pytest tests/unit -m unit` (`make test-unit`) | 53 failed, 375 passed | 53 failed, **383 passed** |

Same failures before and after; the only delta is my 8 new passing tests. The
pre-existing failures are missing type stubs (`jose`, `passlib`, `rank_bm25`,
`PyPDF2`), a numpy stub that needs Python ≥3.12, and 53 unit tests that already
failed on `main` — including 13 in `test_review_service.py::TestReviewService`
that mis-mock the async session (`AsyncMock` result objects make
`result.scalars()` a coroutine). I left those alone: they're unrelated to #97 and
fixing them would balloon the diff.

**Draft PR feedback received from:** none (no peer or mentor feedback received at
the time of submission)

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in. As of the end of Week 10, PR #814 on `ascherj/pathreview`
(https://github.com/ascherj/pathreview/pull/814) is still open and unmerged with
zero review comments, zero inline comments, and no requested reviewers. GitHub
reports its merge state as `blocked`, and no CI checks have run against the head
commit at all — the workflows in `.github/workflows/ci.yml` appear not to be
triggered for fork pull requests on this repo, so I don't even have an automated
signal to react to. Nobody from my cohort picked up my Slack request for a draft
review either.

**How you responded:**
No changes were warranted, since there was nothing to respond to. Rather than
let the PR sit completely idle, I re-verified it against the same baseline I
recorded in Week 9 (`ruff check .` still 182 errors vs. 182 before my changes,
`pytest tests/unit -m unit` still 53 failed / 383 passed vs. 53 failed / 375
passed before), so if a maintainer picks it up the "introduces no new failures"
claim in the PR description is still true. If feedback arrives after the module
closes, the two things I'd expect and would act on first are the ones I flagged
myself in the "Notes for Reviewers" section: whether five coarse milestones are
acceptable or they want finer per-source progress, and whether one DB commit per
milestone is acceptable write load or they'd rather cache progress in Redis.

---

### Reflection

**What was harder than you expected?**
The reproduction breaking my own issue framing was the hardest moment, and it
happened in Week 8, not during implementation. In Week 7 I wrote in this journal
that "the backend already emits `progress_pct`, so no API or database changes are
required — this is primarily wiring an existing value through to the UI." That
was wrong, and I only found out because I made myself write `tests/repro_issue_97.py`
instead of trusting my read of the code. The endpoint in `api/routes/reviews.py`
really did return a field called `progress_pct` — but via
`getattr(review, "progress_pct", 0)` against a `Review` model that had no such
column, so the fallback silently resolved to `0` on every single poll. I had
scanned that line in Week 7 and pattern-matched "the field is there, good" without
asking where the value came from. If I'd gone straight to implementation I would
have shipped a progress bar frozen at 0% that snapped to complete, which is
arguably a worse user experience than the spinner it replaced, and I'd have had no
idea until someone ran it. The thing that fooled me wasn't complicated code; it
was a defensive default that made broken code look finished.

**What did you learn about working in a large codebase?**
That "don't make it worse" is a completely different bar than "make it pass," and
that you have to measure it deliberately. When I finally ran the checks, this
repo had 53 failing unit tests, 182 ruff errors, and 5 mypy errors before I
touched anything — including 13 failures in `tests/unit/test_review_service.py`,
the exact file I needed to edit, caused by tests building result objects with
`AsyncMock` so that `result.scalars()` returns a coroutine. On my own projects
green means good and red means I broke something; here red was the starting
state, so I had to check out `9e32d4c` (the commit before my work), record every
number, then re-run the same commands on my branch and diff them. That discipline
paid off twice: my ruff count went 182 → 183 and my mypy count 20 → 21, and both
deltas were mine — an `N806` from naming a patched class `MockReview` and a
`no-untyped-def` from `_set_progress`'s unannotated `db` parameter. Without a
baseline both would have been invisible in the noise. I also learned to read the
tooling itself rather than trust its name: `make check` runs `black .`, which
*rewrites* 53 pre-existing files, so running the documented command as-is would
have buried my ~180-line fix inside a thousand-line reformatting diff. I ran
`black --check` instead and left the other files alone. Resisting drive-by
cleanup was genuinely uncomfortable — those 13 broken tests are three lines from
working — but they're unrelated to #97 and fixing them would have made my diff
much harder to review.

**How did AI tools help — and where did they fall short?**
The biggest win was tracing the data path end to end. I could ask for every place
`progress_pct` appears across Python, TypeScript, and the Alembic migrations and
get the full five-layer picture — model, service, endpoint, TS type, component —
in one pass instead of grepping a repo I'd never seen before. It was also good at
matching conventions: my migration `003_add_progress_pct_to_reviews.py` follows
the shape of `002_add_error_message_to_reviews.py` because I asked for the
existing pattern rather than writing one from scratch, and the same for the
Google-style docstrings CONTRIBUTING.md requires. Where it fell short was
judgment about *this specific* repo's state. The generated test code was correct
and passed, but it introduced that `N806` lint error — plausible, idiomatic
Python that happened to violate a rule this project enables. Nothing flagged
that; I only caught it by diffing ruff output against the baseline. It also
couldn't make the call that mattered most: once the reproduction proved the
backend was broken, deciding to emit five coarse milestones instead of
instrumenting `_run_ingestion_pipeline` per source was a scope judgment about how
much of someone else's pipeline a first-time contributor should touch, and that
came down to me. The pattern I'd summarize is: AI was excellent at "what does this
code do and what does this project's convention look like," and useless at "what
should I not do here."

**What would you do differently if you started over?**
I'd reproduce before I write the problem summary, not after. My Week 7 entry
committed me publicly to a frontend-only framing that Week 8 demolished, and I
spent the first part of Week 9 rewriting my mental model rather than building. A
thirty-minute check — actually reading where `getattr`'s default came from —
would have caught it. I'd also set up the environment in Week 7 instead of Week
9: this checkout had no `.venv`, so I couldn't run a single check until I'd sat
through the full `pip install -e ".[dev]"`, and `node` still isn't installed on
this machine, which is the direct reason PR #814 has no screenshot of the
progress bar actually moving. For a UI issue, "trust me, the JSX is right" is a
weak thing to hand a reviewer, and that was avoidable with an hour of setup three
weeks earlier. On issue selection I'd stand by taking a Tier 3 — but I'd stop
reasoning from labels. I justified it in Week 7 by saying the hard backend part
was already done; it wasn't, and the tier was accurate while my justification was
not.

**What are you most proud of from this module?**
The reproduction script. `tests/repro_issue_97.py` is stdlib-only and statically
inspects all five files on the progress path, so it runs without Postgres, Redis,
or npm — which mattered enormously, since I never got the full stack running
locally. It reported 4/4 FAIL in Week 8 and 4/4 PASS in Week 9, and that flip is
the single clearest piece of evidence in my PR that the whole path is wired, not
just the layer I happened to be looking at. I'm prouder of it than of the fix
because it's what caught my own wrong assumption. Writing a check that could
prove me wrong, before I'd invested in being right, is the habit I actually want
to keep from this module — the progress bar itself is maybe 180 lines and I could
write it again in an afternoon.
