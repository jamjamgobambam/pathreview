# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/130

**Issue title:** `docker-compose.yml` doesn't set memory limits for the LLM proxy service, causing OOM kills on 8GB machines

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The dev `docker-compose.yml` already caps memory for `db` (512M), `redis` (256M), and `vector-db` (1G) under `deploy.resources.limits`, but there's no equivalent limit — or even a defined service block — for the LLM proxy container used in local development. Without a cap, that container can consume all available RAM on the 8GB machines the project targets as a minimum spec, and the OS ends up killing other containers (or the whole compose stack) to recover memory. A successful fix adds a memory limit for the LLM proxy service consistent with the pattern already used for the other three services, sized appropriately for an 8GB minimum-spec machine. This affects `docker-compose.yml` in the repo root.

**Branch name:** fix/130-docker-compose-memory-limits

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
