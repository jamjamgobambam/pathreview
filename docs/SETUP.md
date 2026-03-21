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
Use WSL 2 with Ubuntu 22.04. All commands should be run inside the WSL terminal. Docker Desktop must use the WSL 2 backend (Settings → General → "Use the WSL 2 based engine").

**Linux:**
Install Docker Engine and the Docker Compose plugin (not the standalone `docker-compose` binary).

## Setup Steps

```bash
# 1. Clone your fork
git clone https://github.com/<your-username>/pathreview.git
cd pathreview
git remote add upstream https://github.com/codepath-ai201/pathreview.git

# 2. Configure environment
cp .env.example .env
# Edit .env if needed — defaults work for local development

# 3. Start backing services
docker compose up -d
# Wait for all services to show "healthy":
docker compose ps

# 4. Run first-time setup
make setup

# 5. Start the application
make run
```

Open http://localhost:5173 in your browser. The API is at http://localhost:8000 (Swagger docs at /docs).

## Troubleshooting

**Docker services won't start:**
- Check Docker is running: `docker info`
- Check port conflicts: `lsof -i :5432` / `lsof -i :6379` / `lsof -i :8001`
- If ports are in use, stop the conflicting service or change ports in `docker-compose.yml`

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
