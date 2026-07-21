## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/130)

**Issue title:** docker-compose.yml doesn't set memory limits for the LLM proxy service, causing OOM kills on 8GB machines #130

**Tier:** Tier 3

**Problem summary:**
The current docker-compose.yml, there is no LLM proxy service defined. The db, redis, and vector-db containers are supporting services. The application appears to use an LLM provider directly through environment configuration. The LLM proxy service expected to be added should have memory limits set in the docker file which can prevent OOM kills on 8GB machines.

**Branch name:** 'fix/130-set-memorylimit-llmproxy-service'

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger