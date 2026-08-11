----
## FILE: JOURNAL.md
----
# PathReview — Module 3 Journal

Running record of progress across Weeks 7–10.

---

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/128

**Issue title:** Add a dependency vulnerability scan to the CI pipeline

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**

PathReview currently runs lint, typecheck, unit, integration, and frontend tests in GitHub Actions, but nothing checks whether installed Python or JavaScript dependencies contain known security vulnerabilities. That means a dependency with a published CVE could ship without CI noticing. The fix adds automated scanning to `.github/workflows/ci.yml`: `pip audit` for Python dependencies (after installing the project with dev extras) and `npm audit` for the frontend (after `npm ci`), failing the build when high-severity findings are detected. This is DevOps/CI work rather than application logic, but it directly improves the project's security posture and gives contributors faster feedback on risky dependency updates.

**Branch name:** `chore/128-add-dependency-vulnerability-scans`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Issue claim comment:** https://github.com/ascherj/pathreview/issues/128#issuecomment-5034547950

**Cohort ledger entry:** Yie Sheng Chen · `speculaas` · #128 · [cohort spreadsheet](https://docs.google.com/spreadsheets/d/1oclK-70-klhGofiaw6krk8-zV_wZiumsR-Xnd_l5ZR8/edit?gid=1079392097#gid=1079392097)

### "Is this right for me?" checklist reasoning

| Question | Assessment |
|---|---|
| **Is it actually open?** | Yes — listed in the open issue export and issue tracker with no linked merged PR. |
| **Is the scope clear?** | Yes — add `pip audit` and `npm audit` to CI, fail on high-severity findings, primary file is `ci.yml`. |
| **Is it the right size?** | Tier 3, estimated 3–5 hours. Larger than Tier 1, but bounded to one workflow file plus policy decisions. |
| **Is the maintainer active?** | Yes — upstream repo has recent merges and active issue activity. |
| **Does it match my skill level?** | Chosen deliberately to learn CI/GitHub Actions YAML. I accept the Tier 3 scope because my primary goal is DevOps/CI experience, not the fastest Tier 1 PR. |

**Scope reasoning:** I considered Tier 1 alternatives (#37 snapshot tests, #159 structlog/caplog) for lower risk, but selected #128 because it is the most direct path to editing GitHub Actions workflows, configuring audit tools, and iterating through the CI feedback loop. Main risks: existing dependencies may already have advisories, Python and npm audit tools differ in severity filtering, and policy choices (blocking threshold, job structure) need investigation before the PR is merge-ready.

**Supporting reference:** See `docs/issue-128-context.md` for Mermaid diagrams, CI design notes, and implementation roadmap from issue-selection discussions.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/speculaas/pathreview/commit/474ab43e5c8060948355504d054e8bee3aac25e5

**Reproduction summary:**
Issue #128 is a missing CI security gate rather than a runtime app bug. I reproduced it by inspecting `.github/workflows/ci.yml` on `main`: the workflow has lint, typecheck, unit, integration, and frontend jobs only — no `pip audit`, `npm audit`, or any vulnerability-scan step. Search for those terms returns no matches, which matches the issue’s claim that Python and JavaScript dependencies are not automatically audited. Full notes are in `docs/reproduction-128.md` on that commit.

**PLAN.md link:** https://github.com/speculaas/pathreview/blob/chore/128-add-dependency-vulnerability-scans/PLAN.md

**Walkthrough video (recommended):** *(optional — not recorded yet; not graded)*

**Blockers or open questions:**
- Will existing dependencies already fail `pip audit` / `npm audit --audit-level=high` on first enablement?
- Should Python use plain `pip audit` (any finding fails) or a pinned tool with severity filtering to mirror npm’s high/critical policy?
- Is documenting local `make audit` / SETUP commands in-scope for the PR, or should the first PR touch only `ci.yml`?

---

## Week 9 — Implementation and PR

*(To be filled in next week.)*

---

## Week 10 — Iteration and reflection

*(To be filled in next week.)*


----
## FILE: PLAN.md
----
# Solution plan

**Issue:** [Add a dependency vulnerability scan to the CI pipeline](https://github.com/ascherj/pathreview/issues/128) (#128 · Tier 3 · `bug` · `devops`)

---

### Understand

**Root cause:** PathReview’s GitHub Actions workflow never invokes a dependency vulnerability scanner. Contributors and maintainers only learn about known CVEs in Python or JavaScript packages through ad-hoc local checks or after something is already in production.

**Expected:** On pull requests and pushes to `main`, CI runs:

- `pip audit` against installed Python dependencies (project + dev extras)
- `npm audit` against the frontend lockfile install
- Build **fails** when findings meet the agreed high-severity policy

**Actual (upstream `main`):** `.github/workflows/ci.yml` defines `lint`, `typecheck`, `test-unit`, `test-integration`, and `frontend` only. There are no audit jobs or steps. Reproduction notes: [`docs/reproduction-128.md`](docs/reproduction-128.md).

This is a **missing security gate**, not a broken application code path.

---

### Map

| File / area | Role |
|---|---|
| `.github/workflows/ci.yml` | **Primary** — add Python and frontend audit jobs (or steps) |
| `pyproject.toml` | Defines runtime + `[project.optional-dependencies] dev` that `pip audit` will see after `pip install -e ".[dev]"` |
| `frontend/package-lock.json` | Lockfile consumed by `npm ci` before `npm audit` |
| `frontend/package.json` | Frontend dependency set |
| `Makefile` | Optional: add `make audit` for local parity with CI |
| `docs/SETUP.md` / `docs/CONTRIBUTING.md` | Optional: document local audit commands |
| `docs/reproduction-128.md` | Reproduction record (Week 8) |
| `JOURNAL.md` | Module 3 progress |

**Functions / modules:** N/A for application Python/TS — the “module” under change is the GitHub Actions job graph.

Draft audit jobs already exist on this branch from Week 7 (`dependency-audit-python`, `dependency-audit-frontend`). Week 9 should treat them as a starting point and harden policy.

---

### Plan

Concrete sub-tasks for Week 9 implementation / PR:

1. **Rebase / sync with upstream `main`** and reconfirm the gap still exists; keep reproduction docs accurate.
2. **Finalize CI design in `.github/workflows/ci.yml`:**
   - Keep (or adjust) separate `dependency-audit-python` and `dependency-audit-frontend` jobs so failures are easy to diagnose.
   - Python: upgrade pip → `pip install -e ".[dev]"` → `pip audit`.
   - Frontend: `npm ci` → `npm audit --audit-level=high` (treats high **and** critical as blocking in npm’s semantics).
3. **Resolve severity / policy unknowns** by running audits locally and/or observing GitHub Actions on this branch:
   - If existing dependencies already fail the gate, document findings and choose a maintainer-acceptable approach (upgrade deps, narrow scope, or temporary documented exception — **not** silent `continue-on-error: true`).
   - Note: built-in `pip audit` does not mirror npm’s `--audit-level=high`; decide whether “any finding fails” is acceptable or whether a pinned `pip-audit` CLI with richer flags is needed.
4. **Add contributor-facing local parity** (small, optional-but-valuable): document commands in SETUP/CONTRIBUTING and/or a `make audit` target that wraps the same commands.
5. **Validate and open PR:** confirm new jobs appear in Actions; confirm existing lint/test jobs are unchanged; fill PR template; link #128; run whatever local checks remain in scope (`make audit` / documented commands). Do **not** expand into fixing unrelated baseline `make check` / `make test-unit` debt (182 lint / 53 unit failures) unless they block *this* PR.

---

### Inputs & outputs

**Inputs**

- Repository checkout on CI (or local clone)
- Python 3.11 environment + install of `.[dev]` from `pyproject.toml`
- Node 18 + `frontend/package-lock.json` via `npm ci`
- Advisory databases used by `pip audit` / `npm audit` (network on the runner)

**Outputs / changes**

- New CI jobs (or steps) that exit non-zero when the severity policy is violated
- Clear job names/logs so a failing PR shows *which* ecosystem failed
- Optional: documented local commands so contributors can reproduce CI before pushing
- No change to application runtime behavior at `localhost:5173`

---

### Risks & unknowns

| Risk / unknown | Why it matters | Investigation path |
|---|---|---|
| **Pre-existing advisories** | First time the gate runs, CI may fail on current deps and block all PRs | Run `pip audit` and `npm audit --audit-level=high` locally; inspect Actions logs on this branch |
| **`pip audit` severity filtering** | npm can filter with `--audit-level=high`; pip’s built-in audit is coarser | Check `pip audit --help` on CI Python; consider pinning `pip-audit` package if needed |
| **Tool / pip version on runners** | `pip audit` needs a sufficiently new pip | Explicit `pip install --upgrade pip` step (already drafted) |
| **Scope creep into Makefile / docs** | Issue names only `ci.yml`; extras need maintainer buy-in | Keep docs/`make audit` as a follow-up commit; drop if PR feedback rejects |
| **False sense of security** | Audits miss some vulns; lockfile vs unlocked installs differ | Document that this is a gate, not a full security program |
| **Unrelated baseline test/lint red** | Local `make check` / `make test-unit` already noisy upstream | Out of scope for #128; do not block the security-gate PR on fixing #158/#159-style suite issues |

---

### Edge cases

1. **Clean tree:** no advisories → both audit jobs pass; PR CI green for the new gate.
2. **High/critical npm advisory only:** frontend audit fails; Python may still pass — jobs should be independent so logs show which ecosystem broke.
3. **Python advisory of any severity (if using plain `pip audit`):** job fails even if npm is clean — document this asymmetry in the PR / SETUP notes.
4. **Moderate/low npm findings:** with `--audit-level=high`, should **not** fail the build; still visible in logs if npm prints them.
5. **Transient advisory DB / network errors on the runner:** job may fail for infrastructure reasons — prefer clear error output; avoid hiding failures with `continue-on-error`.
6. **Lockfile drift:** `npm ci` fails before audit if `package-lock.json` is inconsistent — that failure is correct and separate from vulnerability findings.
7. **Dev-only Python packages:** auditing `.[dev]` may flag tooling CVEs that do not ship in production — decide whether that is desired (stricter) or whether a prod-only install is preferred; default to issue wording (project deps as installed in CI, matching other jobs’ `pip install -e ".[dev]"`).

---

## Living document

This plan will be updated in Week 9 as CI runs reveal real advisory counts and as PR review feedback arrives. Supporting diagrams: [`docs/issue-128-context.md`](docs/issue-128-context.md).


----
## FILE: docs/WEEK9_HANDOFF.md
----
# Week 9 verified facts (do not re-derive)

Date: 2026-08-03
Branch: chore/128-add-dependency-vulnerability-scans
Issue: https://github.com/ascherj/pathreview/issues/128

## Already done on branch
- Draft CI jobs `dependency-audit-python` / `dependency-audit-frontend` exist (commit 239ac1f).
- PLAN.md, reproduction doc, JOURNAL Weeks 7–8 done.
- Branch includes upstream/main (no unique upstream commits to rebase).
- No PR opened yet (`gh` token invalid — run `gh auth login`).

## Load-bearing findings (verified locally)
1. **`pip audit` is broken as drafted.** Even with pip 26.2, `pip audit` returns `ERROR: unknown command "audit"`. CI must install/run the `pip-audit` package (`pip install pip-audit` then `pip-audit`).
2. **Python audit currently fails:** `chromadb 1.5.9` → PYSEC-2026-311 / GHSA-f4j7-r4q5-qw2c (no fix versions listed); `ecdsa 0.19.2` → PYSEC-2026-1325 / GHSA-wj6h-64fc-37mp (no fix versions). Exit code 1.
3. **npm gate fails on current lockfile:** `npm audit --audit-level=high` exit 1 — 5 high + 1 critical among 11 total.
4. **After `npm audit fix` (no --force) in a temp tree:** drops to 6 vulns meta `{moderate:4, high:1, critical:1}` — **still fails `--audit-level=high`**. Remaining notable: esbuild/vite/vitest chain (moderate, needs Vite 8 / `--force`); react-router 6.30.4 still flagged (range includes through 7.17.0).
5. Unrelated baseline suite red is out of scope per PLAN.

## Recommended default strategy for Cursor orchestrator (pending M365 + user confirm)
- Fix Python job to use pinned `pip-audit`.
- Prefer documented `--ignore-vuln` for the two unfixed PyPI IDs OR ask maintainers — silent `continue-on-error: true` is not acceptable.
- Include safe `npm audit fix` lockfile refresh if it materially helps; clear remaining high/critical without a Vite major if possible; if not possible, decide with maintainers whether moderate-only residual + upgraded RR is enough or whether policy should stay red until Vite upgrade (follow-up).
- Add optional `make audit` + short SETUP note in a separate commit.
- Open **draft PR early**; fill JOURNAL Week 9 Check-in 1 now; Check-in 2 at submission.

## M365 offload
See `docs/m365-bundles/M365_PROMPTS.md`. Upload bundles; paste replies back for review.


----
## FILE: .github/PULL_REQUEST_TEMPLATE.md
----
## Summary
<!-- One paragraph describing what this PR does and why -->

## Issue
Closes #

## Changes
<!-- Bullet list of the specific changes made -->
-

## Testing
<!-- How did you verify your changes? -->
- [ ] Unit tests pass (`make test-unit`)
- [ ] Integration tests pass (`make test-integration`)
- [ ] Linter passes (`make lint`)
- [ ] Type checker passes (`make typecheck`)
- [ ] New/updated tests cover the changes

## Screenshots / Demo
<!-- If applicable, add screenshots or a link to a demo video -->

## Notes for Reviewers
<!-- Anything the reviewer should pay particular attention to -->


----
## FILE: .github/workflows/ci.yml
----
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install ruff black
      - name: Ruff lint
        run: ruff check .
      - name: Black format check
        run: black --check .

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - name: Mypy type check
        run: mypy api/ core/ ingestion/ rag/ agent/ safety/ --ignore-missing-imports

  test-unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - run: pip install -e ".[dev]"
      - name: Run unit tests
        run: pytest tests/unit -v --tb=short
        env:
          LLM_PROVIDER: mock

  test-integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: pathreview
          POSTGRES_PASSWORD: pathreview
          POSTGRES_DB: pathreview_test
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U pathreview"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - run: pip install -e ".[dev]"
      - name: Run integration tests
        run: pytest tests/integration -v --tb=short
        env:
          DATABASE_URL: postgresql://pathreview:pathreview@localhost:5432/pathreview_test
          REDIS_URL: redis://localhost:6379/0
          LLM_PROVIDER: mock

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "18"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: cd frontend && npm ci
      - name: Frontend lint and tests
        run: cd frontend && npm test -- --run

  dependency-audit-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - name: Upgrade pip for audit support
        run: pip install --upgrade pip
      - name: Install project dependencies
        run: pip install -e ".[dev]"
      - name: Audit Python dependencies
        run: pip audit

  dependency-audit-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "18"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - name: Install frontend dependencies
        run: cd frontend && npm ci
      - name: Audit JavaScript dependencies
        run: cd frontend && npm audit --audit-level=high


----
## FILE: docs/reproduction-128.md
----
# Reproduction notes — Issue #128

**Issue:** [Add a dependency vulnerability scan to the CI pipeline](https://github.com/ascherj/pathreview/issues/128)

**Issue type:** Feature / security gap (not a runtime application bug)

**Date reproduced:** 2026-07-28

---

## Expected vs actual

| | Behavior |
|---|---|
| **Expected** | CI runs `pip audit` (Python) and `npm audit` (JavaScript) and **fails the build on high-severity findings**. |
| **Actual (upstream `main`)** | `.github/workflows/ci.yml` runs lint, typecheck, unit tests, integration tests, and frontend tests only. There is **no** dependency vulnerability scan. |

---

## How this was reproduced

Because #128 is a missing CI gate (not a UI bug), reproduction is:

1. Inspect the workflow on `main` (the baseline the course fork tracks).
2. Confirm no audit jobs/steps exist.
3. Confirm the relevant file named by the issue is exactly `.github/workflows/ci.yml`.

### Commands used

```bash
# On branch main (or: git show main:.github/workflows/ci.yml)
git show main:.github/workflows/ci.yml | rg -n "audit|pip audit|npm audit|vulnerability" || true

# List job names on main
git show main:.github/workflows/ci.yml | rg -n "^  [a-z].*:$"
```

### Observed results

- Search for `audit`, `pip audit`, `npm audit`, and `vulnerability` in `main`'s `ci.yml` returns **no matches**.
- Jobs present on `main`: `lint`, `typecheck`, `test-unit`, `test-integration`, `frontend`.
- Issue body names **Relevant files:** `.github/workflows/ci.yml` and asks for `pip audit` + `npm audit` failing on high-severity findings — that behavior is absent on `main`.

### Evidence snippet (jobs on `main` only)

```yaml
# Jobs on main (abbreviated): lint, typecheck, test-unit,
# test-integration, frontend — then file ends.
# No dependency-audit-python / dependency-audit-frontend jobs.
```

---

## Local verification path (for Week 9)

On a machine with the project venv and Node installed, contributors can preview the same checks CI should run:

```bash
# Python (after make setup / pip install -e ".[dev]")
python -m pip install --upgrade pip
pip audit

# Frontend
cd frontend && npm ci && npm audit --audit-level=high
```

These commands are **not** required to prove the gap exists (the missing CI steps already prove it), but they are the intended local parity for refining severity policy in Week 9.

---

## Where the fix lives

| Area | Path |
|---|---|
| Primary change | `.github/workflows/ci.yml` |
| Optional docs | `docs/SETUP.md` or CONTRIBUTING (local audit commands) |
| Optional Make target | `Makefile` (`make audit`) — only if maintainers accept extra scope |

A draft of the audit jobs already exists on this working branch from Week 7 exploration. Week 8–9 work is to **finalize policy** (severity thresholds, pinning, pre-existing advisories) and land a clean PR — not to re-discover the gap.

---

## Conclusion

The issue is **reliably reproduced**: upstream CI has no automated Python/JS dependency vulnerability scanning. The gap is localized to `.github/workflows/ci.yml` and matches the issue description.
