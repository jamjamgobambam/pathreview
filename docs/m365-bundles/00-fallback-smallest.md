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
## FILE: _audit_scratch/npm-audit.txt
----
npm warn Unknown env config "devdir". This will stop working in the next major version of npm. See `npm help npmrc` for supported config options.
# npm audit report

@babel/core  <=7.29.0
@babel/core: Arbitrary File Read via sourceMappingURL Comment - https://github.com/advisories/GHSA-4x5r-pxfx-6jf8
fix available via `npm audit fix`
node_modules/@babel/core

esbuild  <=0.24.2
Severity: moderate
esbuild enables any website to send any requests to the development server and read the response - https://github.com/advisories/GHSA-67mh-4wv8-2f99
fix available via `npm audit fix --force`
Will install vite@8.2.0, which is a breaking change
node_modules/esbuild
  vite  <=6.4.2
  Depends on vulnerable versions of esbuild
  node_modules/vite
    vite-node  <=2.2.0-beta.2
    Depends on vulnerable versions of vite
    node_modules/vite-node
      vitest  <=3.2.5
      Depends on vulnerable versions of vite
      Depends on vulnerable versions of vite-node
      node_modules/vitest

form-data  4.0.0 - 4.0.5
Severity: high
form-data: CRLF injection in form-data via unescaped multipart field names and filenames - https://github.com/advisories/GHSA-hmw2-7cc7-3qxx
fix available via `npm audit fix`
node_modules/form-data

picomatch  <=2.3.1
Severity: high
Picomatch: Method Injection in POSIX Character Classes causes incorrect Glob Matching - https://github.com/advisories/GHSA-3v7f-55p6-f55p
Picomatch has a ReDoS vulnerability via extglob quantifiers - https://github.com/advisories/GHSA-c2c7-rcm5-vvqj
fix available via `npm audit fix`
node_modules/picomatch

postcss  <=8.5.22
Severity: high
PostCSS has XSS via Unescaped </style> in its CSS Stringify Output - https://github.com/advisories/GHSA-qx2v-qp2m-jg93
PostCSS: Arbitrary file read and information disclosure via attacker-controlled sourceMappingURL in CSS comments - https://github.com/advisories/GHSA-6g55-p6wh-862q
PostCSS: Path Traversal in Previous Source Map Auto-Loading (sourceMappingURL) leads to Arbitrary .map File Disclosure - https://github.com/advisories/GHSA-r28c-9q8g-f849
PostCSS: incomplete fix of GHSA-6g55-p6wh-862q — attacker-controlled sourceMappingURL reads arbitrary .map files when `from` is unset - https://github.com/advisories/GHSA-fxqj-rqcc-2cmp
fix available via `npm audit fix`
node_modules/postcss

react-router  6.0.0 - 7.17.0
Severity: moderate
React Router's same-origin redirect with path starting // causes open redirect via protocol-relative URL reinterpretation - https://github.com/advisories/GHSA-2j2x-hqr9-3h42
React Router: Open redirect via backslash in <Link> and useNavigate (CVE-2025-68470 bypass) - https://github.com/advisories/GHSA-wrjc-x8rr-h8h6
React Router: Arbitrary Constructor Injection via deserializeErrors() in React Router SSR Hydration - https://github.com/advisories/GHSA-337j-9hxr-rhxg
fix available via `npm audit fix`
node_modules/react-router
  react-router-dom  6.6.3-pre.0 - 6.30.4
  Depends on vulnerable versions of react-router
  node_modules/react-router-dom




ws  8.0.0 - 8.20.1
Severity: high
ws: Uninitialized memory disclosure - https://github.com/advisories/GHSA-58qx-3vcg-4xpx
ws: Memory exhaustion DoS from tiny fragments and data chunks - https://github.com/advisories/GHSA-96hv-2xvq-fx4p
fix available via `npm audit fix`
node_modules/ws

11 vulnerabilities (1 low, 4 moderate, 5 high, 1 critical)

To address issues that do not require attention, run:
  npm audit fix

To address all issues (including breaking changes), run:
  npm audit fix --force


----
## FILE: _audit_scratch/pip-audit-cli.txt
----
Found 2 known vulnerabilities in 2 packages
Name     Version ID              Fix Versions
-------- ------- --------------- ------------
chromadb 1.5.9   PYSEC-2026-311
ecdsa    0.19.2  PYSEC-2026-1325

Name       Skip Reason
---------- -------------------------------------------------------------------------
pathreview Dependency not found on PyPI and could not be audited: pathreview (0.1.0)
