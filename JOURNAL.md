# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/54

**Issue title:** Add a plan validation step that checks tool prerequisites before executing the plan

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The agent orchestrator (`agent/orchestrator.py`) builds a flat, linear execution plan
and runs each analysis tool in a fixed order without ever checking whether a tool's
prerequisites actually ran and produced usable output. As a result, dependent tools
receive empty or hardcoded inputs — for example `market_analyzer` is always handed
`{"detected_skills": {}}`, so it never sees the skills that `skill_extractor` produced,
and `skill_extractor` assumes GitHub repo metadata that may never have been fetched.
A successful fix introduces an explicit tool dependency graph (a DAG) in a new
`agent/tools/tool_dependencies.py` and a validation step in the orchestrator that,
before execution, confirms each tool's upstream dependencies were satisfied — failing
fast (or skipping with a clear, logged reason) instead of silently running tools on
missing data. This makes the agent's plan correct-by-construction and its failures
diagnosable, which is the core of reliable multi-tool agent orchestration.

**Branch name:** feat/54-plan-dag-validation

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### Selection notes — "Is this right for me?" reasoning

- **Tier acknowledgement:** This is a **Tier 3** issue (labels: `tier-3`, `agent`,
  `enhancement`, `devops`). I chose Tier 3 on purpose because my goal for this module
  is to practice real AI-engineer *agent architecture* work — planning, dependency
  resolution, and plan validation — rather than a one-line bug fix.
- **Scope fit:** The change is tightly bounded to the `agent/` subsystem. It is one
  new module (`tool_dependencies.py`) plus a validation hook in `orchestrator.py`.
  The five tools are small (~100–160 lines each) and already expose clear
  input/output contracts via the `ToolResult` dataclass, so the dependency edges are
  discoverable from the code (e.g. `market_analyzer` consumes `detected_skills`,
  `skill_extractor` consumes `repo_metadata`). The 8–12h effort estimate fits the
  Weeks 8–9 window.
- **Why not a lower tier:** The Tier-1/2 agent items are smaller reliability tweaks
  (e.g. exponential backoff). This issue is the most representative of agent-design
  work and gives me a concrete DAG/planning artifact to talk about in the Week 10
  reflection.
- **Risk noted:** It is a popular issue (a few cohort members have also commented to
  claim it). Cohort issues are graded per-student on our own forks and are not
  required to be merged upstream, so working in parallel is acceptable; I will still
  record it on the ledger for visibility.

**Setup verification (Week 7):**
- `.env` created from `.env.example` (`LLM_PROVIDER=mock`, no API key needed).
- `docker compose up -d` — Postgres (5433) and Redis (6379) healthy.
- `make setup` completed: `.venv` (Python 3.11), dependencies installed, Alembic
  migrations applied, database seeded (test users `user1..3@example.com`), frontend
  deps installed.
- `make run` — frontend confirmed loading at http://localhost:5173, API at :8000.
