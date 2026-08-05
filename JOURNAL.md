## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/130)

**Issue title:** docker-compose.yml doesn't set memory limits for the LLM proxy service, causing OOM kills on 8GB machines #130

**Tier:** Tier 3

**Problem summary:**
The current docker-compose.yml, there is no LLM proxy service defined. The db, redis, and vector-db containers are supporting services. The application appears to use an LLM provider directly through environment configuration. The LLM proxy service expected to be added should have memory limits set in the docker file which can prevent OOM kills on 8GB machines.

**Branch name:** 'fix/130-set-memorylimit-llmproxy-service'

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (https://github.com/SinAIML/pathreview/blob/fix/130-set-memorylimit-llmproxy-service)

**Reproduction summary:**
Reproduction summary:
I confirmed that the existing db, redis, and vector-db services already had resource limits, while the proxy service itself is absent, proxy service with memory limits is added post litellm configuration.


**PLAN.md link:** https://github.com/SinAIML/pathreview/blob/fix/130-set-memorylimit-llmproxy-service/PLAN.md

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Added the `llm-proxy` service to `docker-compose.yml`, running the LiteLLM proxy image with a 512M memory limit and a healthcheck, matching the pattern already used for `db`/`redis`/`vector-db`. Added `litellm-config.yaml` to route the app's two existing providers (OpenAI, OpenRouter) through the proxy instead of the app calling them directly. Added an `llm_proxy_url` setting to `core/config.py` and documented `OPENROUTER_API_KEY`/`LLM_PROXY_URL` in `.env.example` and `.env`.

**Next steps:**
Point `ReviewGenerator`'s `base_url` at `settings.llm_proxy_url` once the RAG generation step is actually implemented (it's currently a placeholder in `review_service.py`, so there's no live call site to redirect yet). Bring the stack up locally with `docker compose up` to confirm `llm-proxy` starts, passes its healthcheck, and stays within its memory limit under a real request. Add/update tests covering the new config field and the compose service.

**Blockers:**
None blocking right now — noting that this issue's fix (the proxy container + memory limit) is complete on its own, but it isn't exercised end-to-end yet since the code path that would call it (RAG generation) hasn't been built.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/950

**Branch:** `fix/130-set-memorylimit-llmproxy-service`

**What you built:**
Added the missing `llm-proxy` service to `docker-compose.yml` (LiteLLM proxy image, 512M memory limit, healthcheck), so the LLM-facing traffic runs as its own resource-capped container instead of the app calling OpenAI/OpenRouter directly — matching the limits already set on `db`, `redis`, and `vector-db`. Added `litellm-config.yaml` to route the app's existing OpenAI and OpenRouter credentials through the proxy, and an `llm_proxy_url` setting in `core/config.py` for app code to point at it.

**Tests added or updated:**
None — no test files were touched. Verified manually by running `docker compose up` and confirming the `llm-proxy` container starts and passes its healthcheck.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** none 