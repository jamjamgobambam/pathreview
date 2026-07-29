# Journal

## 2026-07-23 — Environment setup

Verified local dev environment is working end-to-end:

- `.env` configured from `.env.example` (using `LLM_PROVIDER=mock`, no API key needed)
- Frontend deps installed (`cd frontend && npm install`)
- Docker Desktop installed and running
- `docker compose up -d` brings up `db`, `redis`, and `vector-db`, all healthy
  - Fixed `vector-db` crash by bumping `chromadb/chroma:0.4.22` → `0.5.0` in `docker-compose.yml` (0.4.22's bundled numpy used `np.float_`, removed in NumPy 2.0)
