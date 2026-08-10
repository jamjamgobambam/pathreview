# Reviewer Guide: Dependency Vulnerability Scan (Issue #128)

Thanks for reviewing! This adds a `security-scan` CI job that runs `pip-audit` (backend) and `npm audit` (frontend) and fails the build on real findings.

## 1. Get the branch

```bash
git fetch origin
git checkout fix/128-add-a-dependency-vulnerability-scan-to-the-ci-pipeline
```

## 2. Files to look at

- `.github/workflows/ci.yml` — the new `security-scan` job
- `pyproject.toml` — added `pip-audit` as a dev dependency
- `frontend/package.json` — added an `audit` script
- `Makefile` — added `make audit-backend` and `make audit-frontend`

## 3. Run it yourself

```bash
pip install -e ".[dev]"
make audit-backend
```

```bash
cd frontend
npm ci
cd ..
make audit-frontend
```

**Both commands are expected to FAIL right now.** That's not a bug — there are real, currently-unfixed vulnerabilities in some dependencies (e.g. `aiohttp`, `cryptography` on the backend; a few npm packages on the frontend). The scan finding them and failing is the feature working correctly.

## 4. What to check in the CI job itself

Open `.github/workflows/ci.yml` and look for the `security-scan` job. Check:

- [ ] **Ignore list** — two backend vulnerabilities (`PYSEC-2026-311`, `PYSEC-2026-1325`) are explicitly ignored via `--ignore-vuln`. The Makefile has a comment above `audit-backend` explaining why (no fix available upstream). Does that reasoning make sense to you?
- [ ] **Severity threshold** — frontend uses `npm audit --audit-level=high`, so only high/critical findings fail the build (moderate/low are logged but don't block). Backend's `pip-audit` fails on anything _not_ in the ignore list. Reasonable split?
- [ ] **PR comment step** — on every PR, a bot comment should post both scans' results (truncated if huge). Job continues past a failing scan just long enough to post this comment, then fails at the end.
- [ ] **Failure gating** — the last step in the job checks both scans' exit codes and fails the job if either found something. Make sure this logic makes sense: `.github/workflows/ci.yml`, step named "Fail if vulnerabilities were found".

## 5. Things I'm not 100% sure about — feedback welcome

- Is failing on **any** unignored backend finding too strict, or is that the right call?
- Is the ignore-list justification for `chromadb`/`ecdsa` (no upstream fix + not exploitable in how we use it) convincing, or should it be handled differently?
- Anything about the PR-comment format that's confusing or too noisy?

## 6. One thing you can't fully test locally

The PR-comment step only runs on a real `pull_request` GitHub Actions event — it can't be tested from your machine. Once this branch is pushed and a PR is opened, check the Actions tab and confirm a comment actually shows up.

## 7. Unrelated-looking files you'll also see in this branch

Not part of the vulnerability scan itself, but bundled in — these fix `make run`, which was broken before this branch:

- **`scripts/run_dev.py`** (new file) — used by the Makefile's `run` target to start the backend (`uvicorn`) and frontend (`npm run dev`) together as one command, and shut both down cleanly on Ctrl+C. Replaces an old inline bash background-job one-liner.
- **`api/routes/health.py`** — two small fixes: wraps the raw `"SELECT 1"` string in SQLAlchemy's `text()` (required as of SQLAlchemy 2.x, which rejects bare strings), and builds the Redis client with `redis.Redis.from_url(settings.redis_url)` instead of `settings.redis_host`/`settings.redis_port`, which don't exist on the `Settings` class.
