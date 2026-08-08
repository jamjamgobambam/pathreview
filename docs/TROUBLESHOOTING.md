# Troubleshooting Guide

The five most common setup failures, with cause, symptoms, and resolution.

## 1. Docker memory limit

**Cause:** Docker Desktop defaults to 2 GB of RAM, but the stack requires ~4 GB.

**Symptom:** Containers crash with exit code 137 (OOMKilled) during `docker compose up` or `make test-integration`.

**Fix:** Increase Docker's allocated memory:
- **Docker Desktop:** Settings → Resources → Advanced → Memory → set to at least 4 GB (8 GB recommended)
- **Orchestration:** After changing settings, restart Docker and run `docker compose up -d` again

## 2. Port conflicts

**Cause:** A local service (PostgreSQL, Redis, or another dev server) already occupies port 5432, 6379, or 8000.

**Symptom:** `docker compose up` fails with `port is already allocated`.

**Fix:**

| Port | Service | Resolution |
|------|---------|------------|
| 5432 | PostgreSQL | Stop local PostgreSQL, or change `docker-compose.yml` host port |
| 6379 | Redis | Stop local Redis, or change host port in `docker-compose.yml` |
| 8000 | API | Kill the process on :8000, or change `--port` in the `Makefile`/Dockerfile |

Check port usage:
- macOS/Linux: `lsof -i :PORT`
- Windows (Git Bash): `netstat -ano | findstr :PORT`

## 3. Missing `.env` variables

**Cause:** The `.env` file was not created from the template.

**Symptom:** The app starts but features fail with `KeyError` or `ValidationError` at runtime, or the app crashes immediately with a configuration error.

**Fix:**
```bash
cp .env.example .env
```
Then edit `.env` to set `OPENAI_API_KEY` (or use `LLM_PROVIDER=mock` for development).

## 4. Outdated Node.js version

**Cause:** The system Node.js is older than 18, or a version manager (nvm/nodenv) is active with an old default.

**Symptom:** `cd frontend && npm install` fails with engine-version errors, or `npm run dev` crashes immediately.

**Fix:**
```bash
# Check current version
node --version   # must be >= 18

# Using nvm (recommended)
nvm install 18
nvm use 18

# Using fnm
fnm install 18
fnm use 18
```

## 5. Mismatched Python version

**Cause:** Python 3.11+ is required, but the system default is an older version (or `python` points to Python 2).

**Symptom:** `make setup` fails with syntax errors or `pip install` fails to find compatible wheels.

**Fix:**
```bash
# Check current version
python --version   # must be >= 3.11

# Using pyenv (recommended)
pyenv install 3.11
pyenv local 3.11

# Verify
python --version   # should show Python 3.11.x
```

If both Python 3.11 and an older version are installed, the Makefile uses `.venv/bin/python` after `make setup` creates the virtualenv with whatever `python` resolves to. Ensure `python` points to 3.11 before running `make setup`.
