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
