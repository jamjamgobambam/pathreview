# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/128

**Issue title:** Add a dependency vulnerability scan to the CI pipeline

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
Right now the CI pipeline lints, type-checks, and runs tests, but nothing ever
checks whether the project's third-party dependencies contain *known* security
vulnerabilities. That means a Python package or npm module with a published CVE
can be merged into `main` without anyone noticing. The fix is to add a new job
to `.github/workflows/ci.yml` that runs `pip audit` against the Python
dependencies and `npm audit` against the frontend's `package-lock.json`, and
fails the build when a high-severity (or worse) advisory is found. A successful
fix means every pull request is automatically gated on a clean dependency scan,
so vulnerable packages are caught before merge instead of in production. This
touches only the CI configuration and, optionally, an allow-list/threshold
config — it does not change application code.

**Branch name:** feat/128-dependency-vulnerability-scan

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### "Is this issue right for me?" — checklist reasoning

- **Do I understand what's being asked?** Yes. The ask is concrete: add a CI
  step that runs `pip audit` + `npm audit` and fails on high-severity findings.
  There is no ambiguity about the desired end state.
- **Is the scope bounded?** Yes. The issue names exactly one file to change
  (`.github/workflows/ci.yml`). The change is additive — a new job — so it is
  unlikely to break existing lint/typecheck/test jobs.
- **Do I have (or can I get) the skills?** Yes. It requires reading a GitHub
  Actions workflow and adding a job that invokes two well-documented CLI tools.
  No changes to the Python/React application logic are required.
- **Can I verify the fix?** Yes. Running `pip audit` and `npm audit` locally
  reproduces what CI will do. In fact, `npm audit` on the freshly installed
  frontend already reports 11 advisories (1 critical, 4 high), so I have a
  real, observable signal to build the gating logic against.
- **Scope risks I'm watching:** (1) `npm audit` finding pre-existing high-sev
  issues means the new job would fail the build on day one — I'll need to
  decide between fixing/upgrading those deps, adding a documented allow-list,
  or scoping the failure threshold, and confirm the intended behavior with the
  issue author. (2) `pip audit` needs the dependency set resolved in CI, so I'll
  mirror how the existing jobs install deps (`pip install -e ".[dev]"`).
  This is why the issue is rated Tier 3 / 3–5 hours rather than a trivial one.
- **Note on tier:** This is a Tier 3 issue (higher difficulty than the Tier 1
  recommended for a first contribution). I chose it deliberately because the
  blast radius is small (CI-only, no app code) even though the devops surface
  is more advanced.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/BengalPirate/pathreview/commit/74908f8

**Reproduction summary:**
I ran the exact scans the missing CI job would run, directly against the current
checkout. `pip-audit` on the installed Python environment exits non-zero with
**39 vulnerable packages / 188 advisories** (e.g. `tornado`, `urllib3`,
`transformers`, `pillow`, `cryptography`), and `npm audit --audit-level=high` in
`frontend/` exits non-zero with **11 vulnerabilities (1 critical, 4 high)** —
including `ws` and `react-router`. Meanwhile `.github/workflows/ci.yml` has only
`lint`, `typecheck`, `test-unit`, `test-integration`, and `frontend` jobs, none
of which inspect dependencies. This proves the gap: a package with a published
CVE passes CI today.

**Reproduction steps:**
1. `cd frontend && npm audit --audit-level=high` → exit 1 (1 critical, 4 high).
2. `pip install pip-audit && pip-audit` from the repo root → exit 1
   (39 packages, 188 advisories).
3. Inspect `.github/workflows/ci.yml` → confirm no `pip-audit` / `npm audit`
   step exists in any job.

**PLAN.md link:** https://github.com/BengalPirate/pathreview/blob/feat/128-dependency-vulnerability-scan/PLAN.md

**Walkthrough video (recommended):** _(optional — to record via Loom)_

**Blockers or open questions:**
The main open question is the day-one baseline: the repo already carries
pre-existing high/critical advisories, so a strict scan would fail the build
immediately. I need to confirm with the issue author whether to upgrade the
fixable packages, use a documented allow-list of existing advisory IDs, or set a
severity threshold. My default plan is an allow-list for existing advisories
that still gates strictly on *newly introduced* high/critical ones.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the full fix. From PLAN.md: (1) added the npm scan and (2) the Python
scan, both wired into a new `dependency-scan` CI job; (3) resolved the day-one
baseline question by committing a generated baseline snapshot
(`.github/audit-baseline.json`) so the gate blocks only *newly introduced*
advisories rather than red-walling on pre-existing ones; (4) the job runs on the
same `pull_request`/`push` triggers as the rest of the pipeline. The gating logic
lives in a testable `scripts/dependency_audit.py` with 21 passing unit tests.

**Next steps:**
Finish the docs note (done, in `docs/CONTRIBUTING.md`), self-review against
CONTRIBUTING, open a draft PR for peer feedback, then finalize.

**Blockers:**
None. Resolved the open baseline question with the baseline-snapshot approach
(an auto-generated allow-list of pre-existing advisories) instead of hand-listing
188 advisory IDs.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/637

**Branch:** `feat/128-dependency-vulnerability-scan`

**What you built:**
A CI `dependency-scan` job that runs `pip-audit` (Python) and `npm audit`
(frontend) and fails the build when a vulnerability advisory appears that is not
already recorded in a committed baseline (`.github/audit-baseline.json`). The
gating logic lives in `scripts/dependency_audit.py`: it parses each scanner's
JSON, gates npm findings at `high`/`critical` (Python advisories are gated
regardless, since pip-audit reports no severity), and diffs against the baseline
so only *newly introduced* advisories break the build.

**Tests added or updated:**
`tests/unit/test_dependency_audit.py` — 21 unit tests covering pip-audit and npm
audit parsing, the severity threshold, baseline diffing, the end-to-end
evaluation (pass when baseline covers everything; fail on a new Python or new
high/critical npm advisory; ignore new moderate npm advisories), baseline
load/build round-tripping, and the human-readable report.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> Note on pre-existing failures: this checkout has failures unrelated to my
> issue. Measured with my changes stashed vs. applied, the numbers are identical
> except for my additions: `ruff` 161 errors → 161 (my files are clean),
> `mypy` 5 errors → 5 (my files are outside the mypy scope), and `pytest
> tests/unit` 375 passed / 53 failed → 396 passed / 53 failed (the 53 failures
> are unchanged; the +21 are my new passing tests). My changes introduce **no
> new failures** — "passes" here means "no new failures," per the Week 9
> pre-existing-failure guidance. The new `dependency-scan` job itself is green
> (`python scripts/dependency_audit.py` exits 0 against the committed baseline).

**Draft PR feedback received from:** none (peer review waived by CodePath for this cohort)

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback came in. CodePath confirmed that reviewer
feedback is not a feature for the Summer 2026 cohort, and no comments or reviews
were posted on PR #637 (https://github.com/ascherj/pathreview/pull/637) by the
end of the week. The PR remains open and unreviewed.

**How you responded:**
No changes were warranted since no feedback arrived. Rather than let the branch
go stale, I re-ran the full gate one more time to confirm the PR is still in a
mergeable state: `python scripts/dependency_audit.py` exits 0 against the
committed baseline, and my 21 unit tests still pass. If a maintainer does pick
this up later, the two most likely review questions — "why a committed baseline
instead of just failing on everything?" and "why are Python advisories gated
regardless of severity?" — are already answered in the PR description and the
Week 9 journal entry.

---

### Reflection

**What was harder than you expected?**
The hardest part wasn't the CI config — it was deciding what "correct" even
meant given a repo that was already red. A naive `pip-audit` / `npm audit` gate
fails on day one because the checkout ships with 188 Python advisories and 11
npm advisories (1 critical, 4 high) that predate my change. So the real work was
designing a gate that blocks *newly introduced* vulnerabilities without
red-walling every unrelated PR. Landing on a committed baseline snapshot
(`.github/audit-baseline.json`) and diffing against it took more design thought
than the actual YAML. The second surprise was how much noise a large,
partially-broken codebase throws at you: the checkout had 161 pre-existing
`ruff` errors, 5 `mypy` errors, and 53 failing unit tests before I touched
anything, so I had to carefully measure "with my changes stashed vs. applied"
just to *prove* I introduced zero new failures. Separating my signal from the
existing noise was harder and slower than writing the feature.

**What did you learn about working in a large codebase?**
Contributing to someone else's production code is mostly archaeology and
restraint, not coding. On my own projects I'd have just upgraded the vulnerable
packages — but here that would balloon the blast radius far past the issue's
CI-only scope and risk breaking app code I don't understand. I learned to work
*with* the existing state (baseline the known advisories) rather than try to fix
the whole world in one PR. I also learned to mirror existing conventions instead
of inventing my own: I wired the new `dependency-scan` job into the same
`pull_request`/`push` triggers and dependency-install pattern (`pip install -e
".[dev]"`) the other jobs already used, so a maintainer reads it as "one more of
the same" rather than a foreign addition. And I learned that in a big repo,
"passes" means "introduces no new failures," not "everything is green" — a
distinction that doesn't exist when you own 100% of the code.

**How did AI tools help — and where did they fall short?**
AI was most useful as a fast reference for the mechanical, well-documented parts:
the exact shape of `pip-audit` and `npm audit` JSON output, GitHub Actions job
syntax, and scaffolding the unit tests for `scripts/dependency_audit.py`. It let
me move quickly through the parts of the problem that were "known-answer."
Where it fell short was the actual judgment calls — deciding that a committed
baseline was the right pattern (vs. a hand-maintained allow-list of 188 advisory
IDs, or a severity threshold), and figuring out that the pre-existing 53 test
failures were unrelated to my change. Those required reading *this specific
repo's* state and history and making a defensible engineering trade-off, which
AI couldn't do for me because it didn't have the ground truth of what was
already broken. AI accelerated the typing; the deciding was still mine.

**What would you do differently if you started over?**
I'd resolve the day-one baseline question earlier instead of carrying it as an
open blocker into Week 9. I flagged it correctly in Week 8, but I spent time
building against uncertainty before committing to the baseline-snapshot
approach; deciding that up front would have made the implementation more direct.
I'd also record the short Loom walkthrough I left as optional — for a CI change
where the whole value is in the *reasoning* about scope and baselines, a
two-minute narration would communicate the design intent far better than the
diff alone. On issue selection, I'd make the same choice again: a Tier 3 issue
with a small blast radius (CI-only, no app code) was a good bet.

**What are you most proud of from this module?**
That I turned a scope trap into a clean design decision. The easy version of this
issue — "add `pip-audit` to CI" — would have produced a job that fails every PR
on advisories nobody in this cohort introduced, and it would have been useless.
Recognizing that the *interesting* problem was gating on the delta, and then
building it as a testable, isolated `scripts/dependency_audit.py` with 21 unit
tests rather than a pile of untestable shell in a YAML file, is the thing I'd
point to. It's the difference between "made CI run a command" and "designed a
gate the project can actually live with."
