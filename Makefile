.PHONY: setup run test-unit test-integration test-all lint format typecheck check migrate seed reset-db eval clean

ifeq ($(OS),Windows_NT)
  SHELL := cmd.exe
else
  SHELL := /bin/bash
endif

# Detect Windows (Git Bash) vs Unix
ifeq ($(OS),Windows_NT)
  VENV_BIN := $(CURDIR)/.venv/Scripts
  ACTIVATE := "$(VENV_BIN)/activate"
  PYTHON_BIN := "$(VENV_BIN)/python.exe"
else
  VENV_BIN := $(CURDIR)/.venv/bin
  ACTIVATE := "$(VENV_BIN)/activate"
  PYTHON_BIN := "$(VENV_BIN)/python"
endif

PYTHON := $(PYTHON_BIN)
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
ifeq ($(OS),Windows_NT)
  ALEMBIC := $(VENV_BIN)/alembic.exe
else
  ALEMBIC := $(VENV_BIN)/alembic
endif
PRE_COMMIT := $(PYTHON) -m pre_commit
RUFF := $(PYTHON) -m ruff
BLACK := $(PYTHON) -m black
MYPY := $(PYTHON) -m mypy

# ---- Setup ----

setup: ## First-time setup: venv, deps, migrations, seed data
	python -m venv .venv || python3 -m venv .venv
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e ".[dev]"
	$(PRE_COMMIT) install
	$(ALEMBIC) upgrade head
	$(PYTHON) scripts/seed_db.py
	cd frontend && npm install
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
	$(RUFF) check .

format: ## Run black formatter
	$(BLACK) .

typecheck: ## Run mypy type checker
	$(MYPY) api/ core/ ingestion/ rag/ agent/ safety/

check: lint format typecheck ## Run lint + format + typecheck

# ---- Database ----

migrate: ## Run pending database migrations
	$(ALEMBIC) upgrade head

seed: ## Re-seed the database with sample data
	$(PYTHON) scripts/seed_db.py

reset-db: ## Drop and recreate the development database
	docker compose exec db psql -U pathreview -d postgres -c "DROP DATABASE IF EXISTS pathreview_dev;"
	docker compose exec db psql -U pathreview -d postgres -c "CREATE DATABASE pathreview_dev;"
	$(ALEMBIC) upgrade head
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
