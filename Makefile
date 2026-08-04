.PHONY: setup run test-unit test-integration test-all lint format typecheck check audit migrate seed reset-db eval clean

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

# ---- Security ----

# Advisories with no patched release available upstream yet — reviewed and
# accepted so the gate is intentional, not silently green. Revisit when a fix
# ships (tracking: docs/reproduction-128.md).
#   PYSEC-2026-311  chromadb  — no patched release
#   PYSEC-2026-1325 ecdsa     — no patched release (Minerva side-channel)
PIP_AUDIT_IGNORE := --ignore-vuln PYSEC-2026-311 --ignore-vuln PYSEC-2026-1325

audit: ## Scan Python + frontend deps for known vulnerabilities (mirrors CI)
	@echo "--- Python dependencies (pip-audit) ---"
	$(VENV_BIN)/pip-audit $(PIP_AUDIT_IGNORE)
	@echo "--- Frontend production dependencies (fails on high+) ---"
	cd frontend && npm audit --omit=dev --audit-level=high
	@echo "--- Frontend dev-tooling advisories (informational, non-blocking) ---"
	cd frontend && npm audit || true

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
