# Development Environment Setup

## Prerequisites

| Requirement | Minimum | Check command |
|---|---|---|
| Git | 2.39 | `git --version` |
| Python | 3.11 | `python3 --version` (must be ≥3.11 — macOS system Python is often 3.9) |
| Node.js | 18 | `node --version` |
| npm | 9 | `npm --version` |
| Docker | 24 | `docker --version` |
| Docker Compose | 2.20 | `docker compose version` |
| [uv](https://docs.astral.sh/uv/) (recommended) | latest | `uv --version` |
| RAM | 8 GB | — |
| Free disk | 20 GB | — |

Install uv if you don't have it: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Platform-Specific Notes

**macOS (Apple Silicon / M1-M3):**
Ensure Rosetta 2 is installed: `softwareupdate --install-rosetta`. Docker Desktop should be set to use the Apple Silicon build. The `make setup` command handles `ARCHFLAGS` automatically.

**Prefer the [uv setup path](#alternative-setup-with-uv) on macOS.** Apple’s default `/usr/bin/python3` is often **3.9.x**. `make setup` falls back to that interpreter, creates a 3.9 venv, and then fails because this project requires `>=3.11`. `uv` installs a modern Python and creates the venv for you.

**Windows:**
Use **Git Bash** (included with [Git for Windows](https://git-scm.com/download/win)) to run all commands in this guide. PowerShell and Command Prompt will not work for most commands.

`make` is not installed by default on Windows. Install it via winget, then add it to your Git Bash PATH:

```bash
winget install GnuWin32.Make
echo 'export PATH="$PATH:/c/Program Files (x86)/GnuWin32/bin"' >> ~/.bashrc
source ~/.bashrc
```

Docker Desktop must use the WSL 2 backend (Settings → General → "Use the WSL 2 based engine"). If you prefer a fully Linux-native environment, WSL 2 with Ubuntu 22.04 also works — run all commands inside the WSL terminal in that case.

**Linux:**
Install Docker Engine and the Docker Compose plugin (not the standalone `docker-compose` binary).

## Setup Steps

```bash
# 1. Clone your fork
git clone https://github.com/<your-username>/pathreview.git
cd pathreview
git remote add upstream https://github.com/ascherj/pathreview.git

# 2. Configure environment
cp .env.example .env
# Edit .env and set your OPENROUTER_API_KEY (required for AI features)
# All other defaults work for local development

# 3. Start backing services (PostgreSQL + Redis)
#    ⚠️  Docker must be running before the next step — make setup runs database migrations
docker compose up -d
# Wait ~15 seconds, then verify all services are healthy:
docker compose ps

# 4. Run first-time setup
#    Prefer "Alternative: setup with uv" below if `python3 --version` is < 3.11
make setup

# 5. Start the application
make run
```

### Alternative: setup with uv

Use this when system Python is too old (common on macOS) or you already manage projects with `uv`. This replaces step 4 (`make setup`) only — still do steps 1–3 first (clone, `.env`, `docker compose up -d`).

```bash
# Remove a failed/partial venv if one exists (e.g. after make setup with Python 3.9)
rm -rf .venv

# Create a venv with Python ≥3.11 (uv downloads it if needed)
# Note: `uv venv` does not install pip — use `uv pip` for packages
uv venv --python 3.12

# Install the project + dev extras into .venv
uv pip install -e ".[dev]"

# Same post-install steps make setup runs
.venv/bin/pre-commit install
.venv/bin/alembic upgrade head
.venv/bin/python scripts/seed_db.py
cd frontend && npm install && cd ..
```

Then start the app as usual:

```bash
make run
```

`make run`, `make test-unit`, and other Make targets only need `.venv/bin/*` — they work the same whether the venv was created by `make setup` or `uv`.

Open http://localhost:5173 in your browser. The API is at http://localhost:8000 (Swagger docs at /docs).

Setup seeds the database with three test accounts you can use immediately:

| Email | Password |
|---|---|
| user1@example.com | password1 |
| user2@example.com | password2 |
| user3@example.com | password3 |

To reset back to a clean seed state at any time: `make reset-db`

## Troubleshooting

**Docker services won't start:**
- Check Docker is running: `docker info`
- Check port conflicts:
  - macOS/Linux: `lsof -i :5432` / `lsof -i :6379`
  - Windows (Git Bash): `netstat -ano | findstr :5432`
- If ports are in use, stop the conflicting service or change ports in `docker-compose.yml`

**Windows: "password authentication failed" when running migrations:**
PostgreSQL is mapped to port **5433** on Windows (not 5432) to avoid conflicts with any native PostgreSQL installation. If you see auth errors, make sure your `.env` uses the correct connection string:
```
DATABASE_URL=postgresql+asyncpg://pathreview:pathreview@localhost:5433/pathreview_dev
```
If you have PostgreSQL installed natively on Windows (e.g. from a previous project), it will occupy port 5432 and intercept connections meant for Docker. The `docker-compose.yml` already maps around this — just ensure your `.env` was copied from `.env.example` after cloning.

**"Out of memory" during setup:**
- Close other applications to free RAM
- In Docker Desktop: Settings → Resources → set Memory to at least 4 GB

**`make setup` fails on Apple Silicon:**
- Try: `ARCHFLAGS="-arch arm64" make setup`

**Missing `.env` variables:**
- Ensure you copied `.env.example` to `.env`: `cp .env.example .env`

**Node version too old:**
- Use `nvm` to install Node 18+: `nvm install 18 && nvm use 18`

**Python version too old / `Package 'pathreview' requires a different Python: 3.9.x not in '>=3.11'`:**
- `make setup` used system Python 3.9. Do **not** re-run `make setup` (it will recreate the 3.9 venv). Follow [Alternative: setup with uv](#alternative-setup-with-uv) instead.
- Or use `pyenv`: `pyenv install 3.12 && pyenv local 3.12`, delete `.venv`, then `make setup`.

**`No module named pip` after `uv venv`:**
- Expected. `uv venv` does not ship pip. Install deps with `uv pip install -e ".[dev]"`, not `.venv/bin/pip`.

**Windows: `make` not found after installing GnuWin32:**
- The GnuWin32 bin directory may not be on your PATH. Add it manually in Git Bash:
  ```bash
  echo 'export PATH="$PATH:/c/Program Files (x86)/GnuWin32/bin"' >> ~/.bashrc
  source ~/.bashrc
  make --version   # should print GNU Make x.x
  ```

**Windows: `make setup` fails with "No such file or directory: .venv/bin/pip":**
- This should not occur with the current Makefile, which auto-detects Windows and uses `.venv/Scripts/`. If you see this, ensure you have the latest `Makefile` from the repo.

**`alembic upgrade head` fails with "password authentication failed" (macOS/Linux):**
- Docker is not running, or the database container hasn't finished initializing. Run `docker compose up -d`, wait 15 seconds, and try again.
- Check that your `DATABASE_URL` in `.env` uses the `postgresql+asyncpg://` scheme, not plain `postgresql://`.

**`alembic upgrade head` fails with "No module named asyncpg":**
- Re-run the project install: `uv pip install -e ".[dev]"` (or `.venv/bin/pip install asyncpg` if your venv was created with standard `pip`).
