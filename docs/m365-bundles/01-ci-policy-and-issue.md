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


----
## FILE: docs/issue-128-context.md
----
# Issue #128 — Context and Diagram Reference

Running reference for **AI201 Module 3, Week 7** work on PathReview issue [#128](https://github.com/ascherj/pathreview/issues/128): *Add a dependency vulnerability scan to the CI pipeline*.

This document consolidates Mermaid diagrams and decision notes from issue-selection discussions (GPT/Copilot dialogues, lecture slides, and repo exploration) so you can recall context quickly while implementing the fix.

---

## Issue at a glance

| Field | Value |
|---|---|
| **Number** | #128 |
| **Title** | Add a dependency vulnerability scan to the CI pipeline |
| **Tier** | Tier 3 |
| **Labels** | `tier-3`, `bug`, `devops` |
| **Primary file** | `.github/workflows/ci.yml` |
| **Estimated effort** | 3–5 hours |
| **Proposed branch** | `chore/128-add-dependency-vulnerability-scans` |

### Problem (from issue tracker)

The project has no automated check for known security vulnerabilities in its Python or JavaScript dependencies. The fix should run `pip audit` and `npm audit` and **fail the build on high-severity findings**.

### Why this issue was chosen

Primary learning goal: **CI / DevOps** — edit GitHub Actions YAML directly, configure audit tools, handle exit codes, and iterate through the CI feedback loop.

Trade-offs acknowledged in selection discussions:

- **Pros:** clearest opportunity to learn GitHub Actions workflow structure; explicit scope in one file; real security gate.
- **Cons:** Tier 3 (no extra credit for harder issues); existing dependencies may already have advisories; audit tool behavior differs between Python and npm; policy decisions (severity thresholds, blocking vs. reporting) require investigation.

Alternative CI-learning issues considered: #37 (snapshot tests), #159 (structlog/caplog), #57 (mock GitHub API for integration tests), #129 (migration validation in CI).

---

## Module 3 placement

Week 7 is issue selection and setup. Weeks 8–10 cover reproduction/planning, implementation/PR, and iteration/reflection.

```mermaid
stateDiagram-v2
    [*] --> Week7IssueSelection
    Week7IssueSelection --> Week7_8ReproductionPlanning
    Week7_8ReproductionPlanning --> Week8_9BuildPR
    Week8_9BuildPR --> Week10IterationReflection
    Week10IterationReflection --> [*]
    Week7IssueSelection: Choose issue #128
    Week7IssueSelection: Fork repo and setup
    Week7IssueSelection: JOURNAL.md Week 7 section
    Week7_8ReproductionPlanning: Reproduce CI behavior locally
    Week7_8ReproductionPlanning: Write solution plan
    Week7_8ReproductionPlanning: Record walkthrough
    Week8_9BuildPR: Add pip audit and npm audit jobs
    Week8_9BuildPR: Configure severity policy
    Week8_9BuildPR: Submit PR by end of Week 9
    Week10IterationReflection: Respond to review feedback
    Week10IterationReflection: Document CI learnings
```

---

## Week 7 homework workflow

Deliverables for this week: fork, setup, claim issue, cohort ledger, branch, `JOURNAL.md`, submit branch URL.

```mermaid
flowchart TD
    A["Start Week 7: PathReview issue selection"] --> B["Fork PathReview repo"]
    B --> C["Clone your fork, not the original repo"]
    C --> D["Add upstream remote"]
    D --> E["docker compose up -d"]
    E --> F["make setup"]
    F --> G["make run"]
    G --> H{"App loads at localhost:5173?"}
    H -->|No| HFix["Fix setup — read docs/SETUP.md"]
    HFix --> E
    H -->|Yes| I["Comment on issue #128 to claim"]
    I --> J["Add issue to cohort ledger"]
    J --> K["Create branch chore/128-add-dependency-vulnerability-scans"]
    K --> L["Commit JOURNAL.md and context docs"]
    L --> M["Push branch to your fork"]
    M --> N["Submit branch URL ending in /tree/your-branch"]
```

---

## How #128 was selected (CI-oriented decision path)

Issue labels are **faceted** (tier, subsystem, work type overlap). Use a flowchart for decisions, not `gitGraph` — categories are not Git branches.

```mermaid
flowchart TD
    A["67 open issues"] --> B{"Primary learning goal?"}
    B -->|Application bug fix| C["Tier 1 implementation issues"]
    B -->|CI and DevOps| D{"Which CI skill?"}
    B -->|Documentation| E["Docs issues"]
    D -->|Automated regression gate| I37["#37 Snapshot-test prompt templates"]
    D -->|Pytest infrastructure| I159["#159 Capture structlog with caplog"]
    D -->|Edit GitHub Actions YAML| I128["#128 Dependency vulnerability scans"]
    D -->|Advanced service containers| I129["#129 Migration validation in CI"]
    I128 --> I128detail["Tier 3 · pip audit + npm audit · ci.yml"]
    classDef chosen fill:#d5f5e3,stroke:#1e8449,stroke-width:3px;
    classDef alt fill:#ebf5fb,stroke:#2874a6;
    class I128,I128detail chosen;
    class I37,I159,I129 alt;
```

### Issue landscape (quantitative overview)

Sankey diagrams show **volume** across classification dimensions. They are useful for “where are most issues?” but not for strict taxonomy (one issue can have multiple labels).

```mermaid
sankey-beta
    All issues,Tier 1,23
    All issues,Tier 2,23
    All issues,Tier 3,20
    All issues,Unclassified,1
    Tier 3,DevOps,11
    Tier 3,Bug,5
    Tier 3,Enhancement,11
```

---

## Local setup before touching CI

Step Zero from the Issue Selection lecture: confirm baseline before implementing.

```mermaid
flowchart TD
    A["Copy .env.example to .env"] --> B["Start Docker Desktop"]
    B --> C["docker compose up -d"]
    C --> D["docker compose ps"]
    D --> E{"PostgreSQL and Redis healthy?"}
    E -->|No| F["Fix Docker, ports, or environment"]
    F --> C
    E -->|Yes| G["make setup"]
    G --> H["make run"]
    H --> I{"localhost:5173 loads?"}
    I -->|Yes| J["Baseline established — safe to edit CI"]
    I -->|No| K["Inspect terminal output"]
```

### Make vs GitHub Actions (two layers)

PathReview uses **Make locally** and **explicit tool commands in GitHub Actions**. They are related but not identical.

```mermaid
flowchart LR
    subgraph Local["Local developer interface"]
        MakeRun["make run"]
        MakeCheck["make check"]
        MakeTest["make test-unit"]
    end
    subgraph Remote["GitHub Actions CI"]
        Lint["lint job: ruff, black"]
        Typecheck["typecheck job: mypy"]
        Unit["test-unit job: pytest"]
        Frontend["frontend job: npm test"]
    end
    MakeCheck -.->|"similar but not identical"| Lint
    MakeCheck -.-> Typecheck
    MakeTest -.-> Unit
    Issue128["Issue #128 adds"] --> AuditJobs["pip audit + npm audit jobs"]
    AuditJobs --> Remote
```

`make check` runs `black .` (modifies files); CI runs `black --check`. For #128, the change target is `.github/workflows/ci.yml`, not the Makefile — though a future `make audit` target could mirror CI locally if maintainers accept that scope.

---

## Current CI structure (before #128)

Existing jobs in `.github/workflows/ci.yml`:

```mermaid
flowchart TD
    Trigger["PR or push to main"] --> Lint["lint: ruff + black"]
    Trigger --> Typecheck["typecheck: mypy"]
    Trigger --> Unit["test-unit: pytest tests/unit"]
    Trigger --> Integration["test-integration: pytest + Postgres + Redis"]
    Trigger --> Frontend["frontend: npm ci + npm test"]
    Issue128Adds["#128 adds"] --> PythonAudit["Python dependency audit"]
    Issue128Adds --> NpmAudit["npm dependency audit"]
    PythonAudit --> Gate{"High-severity finding?"}
    NpmAudit --> Gate
    Gate -->|Yes| Fail["Fail CI"]
    Gate -->|No| Pass["Security gate passes"]
```

---

## Target CI design for #128

What the new pipeline should do conceptually:

```mermaid
flowchart TD
    A["Pull request or push"] --> B["Checkout repository"]
    B --> C["Backend audit job"]
    B --> D["Frontend audit job"]
    C --> C1["Set up Python"]
    C1 --> C2["Install locked dependencies"]
    C2 --> C3["Run pip audit"]
    C3 --> C4{"Blocking vulnerability found?"}
    D --> D1["Set up Node.js"]
    D1 --> D2["npm ci"]
    D2 --> D3["Run npm audit"]
    D3 --> D4{"High-severity finding?"}
    C4 -->|Yes| F["Fail CI"]
    C4 -->|No| P["Backend audit passes"]
    D4 -->|Yes| F
    D4 -->|No| Q["Frontend audit passes"]
    P --> R{"Both audit jobs pass?"}
    Q --> R
    R -->|Yes| S["Dependency security gate passes"]
    R -->|No| F
```

### Design questions to resolve (known unknowns)

1. Which Python audit tool and version will CI install (`pip audit` requires pip ≥ 22.2)?
2. Which dependency files does the auditor inspect (`pyproject.toml`, lockfile)?
3. Should audits be **separate jobs** or **steps in existing jobs**?
4. Does “high-severity” for npm include **critical**, or only `high`?
5. How will moderate/low findings be reported without blocking?
6. What if existing dependencies already have high-severity advisories?
7. Should contributors be able to reproduce audits locally (`make audit` or documented commands)?

---

## Implementation roadmap (`gitGraph`)

`gitGraph` is appropriate here because it models **real branch and commit history**, not issue taxonomy.

### Simple contribution path

```mermaid
gitGraph
    commit id: "Baseline: main passes CI"
    branch chore/128-dependency-audits
    checkout chore/128-dependency-audits
    commit id: "docs(ci): record current workflow"
    commit id: "ci: add Python dependency audit"
    commit id: "ci: add npm dependency audit"
    commit id: "ci: enforce high-severity threshold"
    commit id: "docs(ci): add local audit instructions"
    commit id: "chore(ci): run checks and finalize PR"
    checkout main
    merge chore/128-dependency-audits id: "PR #128 merged"
```

### Realistic CI-learning path (configure → push → diagnose → correct)

```mermaid
gitGraph
    commit id: "Baseline workflow"
    branch chore/128-dependency-audits
    checkout chore/128-dependency-audits
    commit id: "ci: add initial audit jobs"
    commit id: "ci: pin Python audit tooling"
    commit id: "ci: define npm severity threshold"
    commit id: "fix(ci): correct audit exit-code handling"
    commit id: "test(ci): verify policy behavior"
    commit id: "docs(ci): document local reproduction"
    commit id: "chore(ci): final validation — CI passes"
    checkout main
    merge chore/128-dependency-audits id: "Dependency security gate merged"
```

DevOps loop this encodes:

```text
configure → push → observe CI → diagnose → correct → rerun
```

---

## Engineering phases

| Phase | Actions |
|---|---|
| **1. Baseline** | `git checkout main && git pull upstream main`; run `make check && make test-unit`; inspect current GitHub Actions results |
| **2. Audit policy** | Decide severity thresholds, job structure, handling of pre-existing advisories |
| **3. Python scan** | Install deps → run `pip audit` → fail on agreed policy |
| **4. JavaScript scan** | `npm ci` → `npm audit` with agreed threshold |
| **5. Test outcomes** | Verify clean pass, high-severity fail, and unaffected lint/test jobs |
| **6. Document** | Local reproduction commands; update `JOURNAL.md` / solution plan |

---

## Lecture concepts still relevant

### Five questions before committing to an issue

```mermaid
flowchart TD
    A["Candidate GitHub issue"] --> B{"1. Is it actually open?"}
    B -->|No| Reject1["Skip or verify"]
    B -->|Yes| C{"2. Is the scope clear?"}
    C -->|No| Reject2["Skip vague issue"]
    C -->|Yes| D{"3. Is it the right size?"}
    D -->|Too large| Reject3["Avoid scope trap"]
    D -->|Manageable| E{"4. Is maintainer active?"}
    E -->|No activity| Reject4["Proceed cautiously"]
    E -->|Active| F{"5. Does it match your skill level?"}
    F -->|Double learning curve| Reject5["Consider easier tier"]
    F -->|Good fit| Pick["Good candidate — #128 for CI learning"]
```

For #128: open ✓, scope clear ✓, size is Tier 3 (larger than Tier 1) ⚠, maintainer active ✓, matches CI-learning goal ✓.

### Solution plan structure (for Week 7–8)

```mermaid
mindmap
  root((Solution Plan for #128))
    Problem summary
      No automated dependency scanning
      Python and JS deps unchecked
      High-severity vulns should block CI
    Reproduction steps
      Inspect ci.yml — no audit steps
      Run pip audit locally
      Run npm audit in frontend/
    Known unknowns
      Existing advisory count
      Severity threshold semantics
      Separate jobs vs steps
    Proposed approach
      Add audit jobs to ci.yml
      Pin audit tooling
      Document local commands
    Scope estimate
      1 primary file ci.yml
      Optional docs update
      3–5 hours per issue estimate
```

---

## Diagram type cheat sheet

| Diagram | Use for #128 | Avoid for |
|---|---|---|
| **Flowchart** | CI design, setup, issue selection | Git commit chronology |
| **gitGraph** | Branch/commit roadmap, PR lifecycle | Issue category taxonomy |
| **Sankey** | Issue volume by tier/label | Mutually exclusive classification |
| **Mind map** | Solution plan, known unknowns | Request sequence order |
| **stateDiagram** | Module 3 week progression | CI job internals |

---

## Quick command reference

```bash
# Local baseline
docker compose up -d
make setup
make run                    # → localhost:5173

# Pre-PR checks (contribution guide)
make check && make test-unit

# Explore audits locally (before CI integration)
pip install -e ".[dev]"
pip audit
cd frontend && npm ci && npm audit

# Issue data collection (issues live on GitHub, not in git clone)
gh issue view 128 -R jamjamgobambam/pathreview --comments
```

---

## Source discussions

- Issue selection and CI ranking: `docs/dialogue-dlg-m365-f46f6beb-6turns.json`
- Lecture workflows and PathReview architecture: prior Module 3 Lesson 7 dialogue
- Week 7 deliverables: course `projects.txt` and `docs/cursor_project_submission_requirements.md`
- Architecture diagrams in repo root `README.md`

---

*Last updated: Week 7, Module 3 — issue selection phase.*


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
## FILE: docs/CONTRIBUTING.md
----
# Contributing to PathReview

Thank you for contributing to PathReview! This guide explains our development workflow and standards.

## Getting Started

1. **Fork** the repository and clone your fork
2. **Set up** your development environment following [SETUP.md](SETUP.md)
3. **Browse issues** and find one that interests you
4. **Comment** on the issue to let others know you're working on it

## Branch Naming Convention

Create a branch from `main` using this format:

```
<type>/<issue-number>-<short-description>
```

Where `<issue-number>` is the GitHub issue number (the number shown under the issue title in the tracker — e.g., `#124`).

Examples:
- `fix/124-resume-parser-index-error`
- `feat/128-first-impression-prompt`
- `test/115-readme-scorer-unit-tests`
- `docs/110-update-setup-guide`

Types: `fix`, `feat`, `test`, `docs`, `refactor`, `perf`, `chore`

## Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/). Every commit message must follow this format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:** `fix`, `feat`, `test`, `docs`, `refactor`, `perf`, `chore`, `ci`

**Scopes:** `ingestion`, `rag`, `agent`, `safety`, `api`, `frontend`

**Examples:**
```
fix(ingestion): handle missing experience section in resume parser

Resume parser crashed with IndexError when a resume had no work experience
section. Added a bounds check before accessing sections['experience'][0].

Fixes #42
```

```
test(agent): add unit tests for readme_scorer tool
```

## Pull Request Process

1. **Ensure your code passes all checks:** `make check && make test-unit`
2. **Push your branch** and open a PR using the PR template
3. **Fill out the PR template completely** — incomplete PRs will be sent back
4. **Respond to review feedback** within 48 hours
5. **Squash fixup commits** before final merge if requested

## Code Style

- **Python:** Formatted with `black`, linted with `ruff`, type-checked with `mypy`
- **TypeScript/React:** Follows the existing component patterns in `frontend/src/`
- **Tests:** Every code change should include or update relevant tests
- **Docstrings:** All public functions and classes must have Google-style docstrings

## Running Checks Locally

```bash
make lint       # Ruff linter
make format     # Black formatter
make typecheck  # Mypy type checker
make check      # All three
make test-unit  # Unit tests
```

## Adding a New Parser

If your issue involves adding a new document parser to the ingestion pipeline:

1. Create a new file in `ingestion/parsers/` (e.g., `web_parser.py`)
2. Implement the `BaseParser` interface:
   ```python
   from ingestion.parsers.base import BaseParser, ParseResult

   class WebParser(BaseParser):
       def parse(self, content: str | bytes) -> ParseResult:
           ...
   ```
3. Register the parser in `ingestion/pipeline.py`
4. Add unit tests in `tests/unit/test_<parser_name>.py`
5. Add a sample fixture in `tests/fixtures/` if needed

## Adding a New Agent Tool

If your issue involves adding a new tool to the agent system:

1. Create a new file in `agent/tools/` (e.g., `dependency_audit_tool.py`)
2. Implement the `BaseTool` interface:
   ```python
   from agent.tools.base import BaseTool, ToolResult

   class DependencyAuditTool(BaseTool):
       name = "dependency_audit"
       description = "Checks for outdated dependencies in project repos"

       def execute(self, input_data: dict) -> ToolResult:
           ...
   ```
3. Register the tool in `agent/orchestrator.py`
4. Add unit tests in `tests/unit/test_<tool_name>.py`
5. Add mock responses in `tests/fixtures/` if the tool calls external APIs

## Questions?

Open a discussion or reach out in the course Discord channel.
