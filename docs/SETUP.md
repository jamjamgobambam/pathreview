# Development Environment Setup

## Prerequisites

| Requirement | Minimum | Check command |
|---|---|---|
| Git | 2.39 | `git --version` |
| Python | 3.11 | `python --version` |
| Node.js | 18 | `node --version` |
| npm | 9 | `npm --version` |
| Docker | 24 | `docker --version` |
| Docker Compose | 2.20 | `docker compose version` |
| RAM | 8 GB | — |
| Free disk | 20 GB | — |

### Platform-Specific Notes

**macOS (Apple Silicon / M1-M3):**
Ensure Rosetta 2 is installed: `softwareupdate --install-rosetta`. Docker Desktop should be set to use the Apple Silicon build. The `make setup` command handles `ARCHFLAGS` automatically.

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
git remote add upstream https://github.com/jamjamgobambam/pathreview.git

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
make setup

# 5. Start the application
make run
```

Open http://localhost:5173 in your browser. The API is at http://localhost:8000 (Swagger docs at /docs).

`make setup` seeds the database with three test accounts you can use immediately:

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

**Python version too old:**
- Use `pyenv` to install Python 3.11+: `pyenv install 3.11 && pyenv local 3.11`

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
- Run: `.venv/Scripts/pip install asyncpg` (Windows) or `.venv/bin/pip install asyncpg` (Mac/Linux).
