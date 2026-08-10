.PHONY: setup run test-unit test-integration test-all lint format typecheck check migrate seed reset-db eval clean

SHELL := /bin/bash

# Detect Windows (Git Bash) vs Unix
ifeq ($(OS),Windows_NT)
  VENV_BIN := .venv/Scripts
  PYTHON := $(VENV_BIN)/python.exe
  PIP := $(VENV_BIN)/pip.exe
  PYTEST := $(VENV_BIN)/pytest.exe
  PRE_COMMIT := $(VENV_BIN)/pre-commit.exe
  ALEMBIC := $(VENV_BIN)/alembic.exe
  NPM := npm.cmd
  CREATE_ENV := if not exist .env copy .env.example .env
  CREATE_VENV := if not exist "$(PYTHON)" (where py >nul 2>nul && py -3 -m venv .venv || python -m venv .venv)
else
  VENV_BIN := .venv/bin
  PYTHON := $(VENV_BIN)/python
  PIP := $(VENV_BIN)/pip
  PYTEST := $(VENV_BIN)/pytest
  PRE_COMMIT := $(VENV_BIN)/pre-commit
  ALEMBIC := $(VENV_BIN)/alembic
  NPM := npm
  CREATE_ENV := test -f .env || cp .env.example .env
  CREATE_VENV := test -x "$(PYTHON)" || (python3 -m venv .venv || python -m venv .venv)
endif

# ---- Setup ----

setup: ## First-time setup: venv, deps, migrations, seed data
	$(CREATE_ENV)
	$(CREATE_VENV)
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
	$(PIP) install -e ".[dev]"
	docker compose up -d --wait
	$(PRE_COMMIT) install
	$(ALEMBIC) upgrade head
	$(PYTHON) scripts/seed_db.py
	cd frontend && $(NPM) install
	@echo ""
	@echo "Setup complete. Run 'make run' to start the application."

# ---- Run ----

run: ## Start backend + frontend dev servers
	$(PYTHON) scripts/run_dev.py

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

# ---- Security ----

# Ignored findings (no fix available upstream, tracked in issue #128):
#   PYSEC-2026-311 / CVE-2026-45829 (chromadb): RCE via trust_remote_code on model-load;
#     this project never sets trust_remote_code, so it isn't reachable here.
#   PYSEC-2026-1325 / CVE-2024-23342 (ecdsa): Minerva timing side-channel; upstream has
#     stated side-channel attacks are out of scope for python-ecdsa, no fix planned.
audit-backend: ## Run pip-audit against Python dependencies
	$(VENV_BIN)/pip-audit --desc \
		--ignore-vuln PYSEC-2026-311 \
		--ignore-vuln PYSEC-2026-1325

audit-frontend: ## Run npm audit against frontend dependencies (fails on high/critical)
	cd frontend && $(NPM) run audit

# ---- Database ----

migrate: ## Run pending database migrations
	$(ALEMBIC) upgrade head

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
