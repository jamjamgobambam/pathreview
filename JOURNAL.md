# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/130

**Issue title:** `docker-compose.yml` doesn't set memory limits for the LLM proxy service, causing OOM kills on 8GB machines

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Why I picked this issue:**
This is a Tier 3 issue, which is the highest tier, but I still felt comfortable picking it because I had just spent a bunch of time getting my local environment running with `docker compose up`. While debugging that setup I was already reading through `docker-compose.yml` line by line and noticed the `db`, `redis`, and `vector-db` services all have `deploy.resources.limits.memory` set. So going into this issue I already understood the pattern I'd need to follow. It's also a nicely scoped, single file change (just `docker-compose.yml`), so I don't need to touch the RAG pipeline or agent code yet, which I'm still getting familiar with. That made it feel like a good first issue even though it's labeled Tier 3.

**Problem summary:**
Right now `docker-compose.yml` sets memory limits for `db` (512M), `redis` (256M), and `vector-db` (1G), but there's no matching limit, or even a service block, for the LLM proxy container that's supposed to be used in local dev. Because that container has no cap, it can eat up all the RAM on a machine, and since the project says 8GB is the minimum spec, that's a real problem. Once memory runs out, the OS starts killing off other containers or processes to free up space, so instead of just the LLM proxy struggling, other parts of the dev stack can go down too. A good fix would add a memory limit for the LLM proxy service that follows the same pattern as the other three services, sized so it still works on an 8GB machine. This only touches `docker-compose.yml` in the repo root.

**Branch name:** fix/130-docker-compose-memory-limits

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
