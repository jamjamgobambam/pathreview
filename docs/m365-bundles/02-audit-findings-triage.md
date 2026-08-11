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
## FILE: frontend/package.json
----
{
  "name": "pathreview-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:coverage": "vitest --coverage"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "lucide-react": "^0.294.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vitest": "^1.0.0",
    "@testing-library/react": "^14.1.0",
    "@testing-library/jest-dom": "^6.1.0",
    "jsdom": "^23.0.0",
    "jest-axe": "^8.0.0",
    "@types/jest-axe": "^3.5.7",
    "@types/jest": "^29.5.0"
  }
}


----
## FILE: pyproject.toml
----
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pathreview"
version = "0.1.0"
description = "AI-powered portfolio review assistant"
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"

dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.25.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.13.0",
    "psycopg2-binary>=2.9.9",
    "asyncpg>=0.29.0",
    "greenlet>=3.0.0",
    "pydantic[email]>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-multipart>=0.0.6",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "bcrypt>=4.0.1,<5.0.0",
    "openai>=1.10.0",
    "chromadb>=0.4.22",
    "redis>=5.0.0",
    "httpx>=0.26.0",
    "pypdf>=3.17.0",
    "tiktoken>=0.5.2",
    "tenacity>=8.2.0",
    "structlog>=24.1.0",
    "rank-bm25>=0.2.2",
    "numpy>=1.26.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.23.0",
    "pytest-benchmark>=4.0.0",
    "pytest-httpserver>=1.0.8",
    "hypothesis>=6.92.0",
    "ruff>=0.2.0",
    "black>=24.1.0",
    "mypy>=1.8.0",
    "pre-commit>=3.6.0",
    "mutmut>=2.4.4",
    "types-redis>=4.6.0",
]

[tool.setuptools.packages.find]
include = ["api*", "core*", "ingestion*", "rag*", "agent*", "safety*"]
exclude = ["frontend*", "alembic*", "tests*", "scripts*"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM", "TCH"]

[tool.ruff.lint.per-file-ignores]
"core/models/*.py" = ["E501"]
"scripts/*.py" = ["E501"]
"alembic/versions/*.py" = ["E501"]

[tool.black]
target-version = ["py311"]
line-length = 100

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
check_untyped_defs = true
exclude = ["alembic/versions/"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "unit: Unit tests (fast, no external dependencies)",
    "integration: Integration tests (require Docker services)",
    "benchmark: Performance benchmarks",
    "security: Security and red-team tests",
]


----
## FILE: Makefile
----
.PHONY: setup run test-unit test-integration test-all lint format typecheck check migrate seed reset-db eval clean

SHELL := /bin/bash

# Detect Windows (Git Bash) vs Unix
ifeq ($(OS),Windows_NT)
  VENV_BIN := .venv/Scripts
else
  VENV_BIN := .venv/bin
endif

PYTHON := $(VENV_BIN)/python
PIP := $(VENV_BIN)/pip
PYTEST := $(VENV_BIN)/pytest

# ---- Setup ----

setup: ## First-time setup: venv, deps, migrations, seed data
	python -m venv .venv || python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
	$(PIP) install -e ".[dev]"
	$(VENV_BIN)/pre-commit install
	$(VENV_BIN)/alembic upgrade head
	$(PYTHON) scripts/seed_db.py
	cd frontend && npm install
	@echo ""
	@echo "Setup complete. Run 'make run' to start the application."

# ---- Run ----

run: ## Start backend + frontend dev servers
	@trap 'kill %1 %2 2>/dev/null' EXIT; \
	source $(VENV_BIN)/activate && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 & \
	cd frontend && npm run dev & \
	wait

# ---- Tests ----

test-unit: ## Run unit tests only (~30 seconds)
	$(PYTEST) tests/unit -v -m unit

test-integration: ## Run integration tests only
	$(PYTEST) tests/integration -v -m integration

test-all: ## Run full test suite
	$(PYTEST) tests/ -v

# ---- Code Quality ----

lint: ## Run ruff linter
	$(VENV_BIN)/ruff check .

format: ## Run black formatter
	$(VENV_BIN)/black .

typecheck: ## Run mypy type checker
	$(VENV_BIN)/mypy api/ core/ ingestion/ rag/ agent/ safety/

check: lint format typecheck ## Run lint + format + typecheck

# ---- Database ----

migrate: ## Run pending database migrations
	$(VENV_BIN)/alembic upgrade head

seed: ## Re-seed the database with sample data
	$(PYTHON) scripts/seed_db.py

reset-db: ## Drop and recreate the development database
	docker compose exec db psql -U pathreview -d postgres -c "DROP DATABASE IF EXISTS pathreview_dev;"
	docker compose exec db psql -U pathreview -d postgres -c "CREATE DATABASE pathreview_dev;"
	$(VENV_BIN)/alembic upgrade head
	$(PYTHON) scripts/seed_db.py

# ---- Evaluation ----

eval: ## Run the RAG evaluation suite
	$(PYTHON) scripts/run_evals.py

# ---- Cleanup ----

clean: ## Remove build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage dist build *.egg-info

# ---- Help ----

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help


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
## FILE: _audit_scratch/npm-audit-fix-dry-run.txt
----
npm warn Unknown env config "devdir". This will stop working in the next major version of npm. See `npm help npmrc` for supported config options.
change ws 8.20.0 => 8.21.1
change react-router-dom 6.30.3 => 6.30.4
change react-router 6.30.3 => 6.30.4
change postcss 8.5.8 => 8.5.25
change picomatch 2.3.1 => 2.3.2
change node-releases 2.0.36 => 2.0.51
change nanoid 3.3.11 => 3.3.17
change hasown 2.0.2 => 2.0.4
change form-data 4.0.5 => 4.0.6
change electron-to-chromium 1.5.321 => 1.5.399
change caniuse-lite 1.0.30001780 => 1.0.30001806
change browserslist 4.28.1 => 4.28.7
change baseline-browser-mapping 2.10.10 => 2.11.12
change @remix-run/router 1.23.2 => 1.23.3
change @babel/types 7.29.0 => 7.29.8
change @babel/traverse 7.29.0 => 7.29.8
change @babel/template 7.28.6 => 7.29.7
change @babel/parser 7.29.2 => 7.29.8
change @babel/helpers 7.29.2 => 7.29.7
change @babel/helper-validator-option 7.27.1 => 7.29.7
change @babel/helper-validator-identifier 7.28.5 => 7.29.7
change @babel/helper-string-parser 7.27.1 => 7.29.7
change @babel/helper-module-transforms 7.28.6 => 7.29.7
change @babel/helper-module-imports 7.28.6 => 7.29.7
change @babel/helper-globals 7.28.0 => 7.29.7
change @babel/helper-compilation-targets 7.28.6 => 7.29.7
change @babel/generator 7.29.1 => 7.29.8
change @babel/core 7.29.0 => 7.29.7
change @babel/compat-data 7.29.0 => 7.29.7
change @babel/code-frame 7.29.0 => 7.29.7

changed 30 packages, and audited 324 packages in 8s

84 packages are looking for funding
  run `npm fund` for details

# npm audit report

@babel/core  <=7.29.0
@babel/core: Arbitrary File Read via sourceMappingURL Comment - https://github.com/advisories/GHSA-4x5r-pxfx-6jf8
fix available via `npm audit fix`


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


picomatch  <=2.3.1
Severity: high
Picomatch: Method Injection in POSIX Character Classes causes incorrect Glob Matching - https://github.com/advisories/GHSA-3v7f-55p6-f55p
Picomatch has a ReDoS vulnerability via extglob quantifiers - https://github.com/advisories/GHSA-c2c7-rcm5-vvqj
fix available via `npm audit fix`


postcss  <=8.5.22
Severity: high
PostCSS has XSS via Unescaped </style> in its CSS Stringify Output - https://github.com/advisories/GHSA-qx2v-qp2m-jg93
PostCSS: Arbitrary file read and information disclosure via attacker-controlled sourceMappingURL in CSS comments - https://github.com/advisories/GHSA-6g55-p6wh-862q
PostCSS: Path Traversal in Previous Source Map Auto-Loading (sourceMappingURL) leads to Arbitrary .map File Disclosure - https://github.com/advisories/GHSA-r28c-9q8g-f849
PostCSS: incomplete fix of GHSA-6g55-p6wh-862q — attacker-controlled sourceMappingURL reads arbitrary .map files when `from` is unset - https://github.com/advisories/GHSA-fxqj-rqcc-2cmp
fix available via `npm audit fix`


react-router  6.0.0 - 7.17.0
Severity: moderate
React Router's same-origin redirect with path starting // causes open redirect via protocol-relative URL reinterpretation - https://github.com/advisories/GHSA-2j2x-hqr9-3h42
React Router: Open redirect via backslash in <Link> and useNavigate (CVE-2025-68470 bypass) - https://github.com/advisories/GHSA-wrjc-x8rr-h8h6
React Router: Arbitrary Constructor Injection via deserializeErrors() in React Router SSR Hydration - https://github.com/advisories/GHSA-337j-9hxr-rhxg
fix available via `npm audit fix`

  react-router-dom  6.6.3-pre.0 - 6.30.4
  Depends on vulnerable versions of react-router
  




ws  8.0.0 - 8.20.1
Severity: high
ws: Uninitialized memory disclosure - https://github.com/advisories/GHSA-58qx-3vcg-4xpx
ws: Memory exhaustion DoS from tiny fragments and data chunks - https://github.com/advisories/GHSA-96hv-2xvq-fx4p
fix available via `npm audit fix`


11 vulnerabilities (1 low, 4 moderate, 5 high, 1 critical)

To address issues that do not require attention, run:
  npm audit fix

To address all issues (including breaking changes), run:
  npm audit fix --force
npm warn allow-scripts 2 packages have install scripts not yet covered by allowScripts:
npm warn allow-scripts   esbuild@0.21.5 (postinstall: node install.js)
npm warn allow-scripts   fsevents@2.3.3 (install: (install scripts present))
npm warn allow-scripts
npm warn allow-scripts Run `npm approve-scripts --allow-scripts-pending` to review, or `npm approve-scripts <pkg>` to allow.


----
## FILE: _audit_scratch/npm-audit-after-fix.txt
----
npm warn Unknown env config "devdir". This will stop working in the next major version of npm. See `npm help npmrc` for supported config options.
# npm audit report

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

react-router  6.0.0 - 7.17.0
Severity: moderate
React Router: Open redirect via backslash in <Link> and useNavigate (CVE-2025-68470 bypass) - https://github.com/advisories/GHSA-wrjc-x8rr-h8h6
React Router: Arbitrary Constructor Injection via deserializeErrors() in React Router SSR Hydration - https://github.com/advisories/GHSA-337j-9hxr-rhxg
fix available via `npm audit fix`
node_modules/react-router
  react-router-dom  6.0.0-alpha.0 - 7.17.0
  Depends on vulnerable versions of react-router
  node_modules/react-router-dom




6 vulnerabilities (4 moderate, 1 high, 1 critical)

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


----
## FILE: _audit_scratch/pip-audit-help-flags.txt
----
8:                 [-o FILE] [--ignore-vuln ID] [--disable-pip]
11:audit the Python environment for dependencies with known vulnerabilities
32:  -s SERVICE, --vulnerability-service SERVICE
33:                        the vulnerability service to audit dependencies
41:  -S, --strict          fail the entire audit if dependency collection fails
44:                        include a description for each vulnerability; `auto`
49:                        includes alias IDs for each vulnerability; `auto`
65:                        vulnerabilities (default: False)
86:  --ignore-vuln ID      ignore a specific vulnerability by its vulnerability
ERROR: unknown command "audit"


