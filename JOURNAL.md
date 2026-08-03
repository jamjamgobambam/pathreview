## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/130

**Issue title:** `docker-compose.yml` doesn't set memory limits for the LLM proxy service, causing OOM kills on 8GB machines

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The development stack needs a bounded memory allocation for its LLM proxy so workloads related to model cannot exhaust the RAM on host. In the current docker-compose.yml, the database, Redis, and vector database have memory caps, but no memory-limited LLM proxy service is defined. A successful fix would add an appropriate limit for the proxy on the minimum 8 GB development machine while preserving enough memory for the OS and other containers. This would contain excessive proxy memory use instead of allowing it to trigger system-wide OOM kills.

**Branch name:** fix/130-llm-proxy-oom-memory-limit

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Scope Reasoning**:

**Working assumption:** In this issue, "LLM proxy" means an intended local OpenAI-compatible gateway container in the development Docker Compose stack, such as LiteLLM. It does not mean the hosted OpenRouter API or Vite's frontend `/api` proxy.

### Part 1 - Understanding the Issue

[x] I can explain the problem and expected behavior in my own words.

The intended development gateway can grow beyond the safe memory budget on an 8 GB machine because its container has no enforced ceiling. The fix should constrain that container so excessive LLM traffic cannot starve PostgreSQL, Redis, Chroma, the host operating system, or other applications.

[x] I located and read the referenced file and supporting setup documentation.

The issue is labeled `devops`, `docs`, and `tier-3`, and it names `docker-compose.yml` as the relevant file. I read that file in full and confirmed that it currently defines `db` (512M), `redis` (256M), and `vector-db` (1G); I also confirmed in `docs/SETUP.md` that 8 GB is the minimum supported RAM and that the OOM guidance recommends allocating at least 4 GB to Docker Desktop.

[x] I can describe the intended before-and-after under the working assumption.

Before the fix, the intended local gateway can use host memory without a Compose-enforced maximum. After the fix, its Compose service should have an explicit limit that fits within the documented 8 GB minimum and leaves headroom for the existing 1.75 GB of service limits, Docker overhead, and the host; exceeding the limit should be contained to the gateway instead of causing system-wide memory pressure.

### Part 2 - Tier Fit

[x] I confirmed that the tracker classifies this issue as Tier 3.

[x] I understand why the issue can require Tier 3 infrastructure reasoning.

The final edit may be small, but choosing a safe limit requires understanding the full development memory budget and how the gateway interacts with the other containers. My scope is limited to the proxy's resource limit, its validation, and any directly related setup documentation; designing a new model-serving architecture is outside this issue.

### Part 3 - Codebase Readiness

[x] I found and read the Compose service and resource-limit sections relevant to the change.

The three existing services all use `deploy.resources.limits.memory`, which establishes the repository's current convention. The checked-in file does not contain the assumed gateway stanza, so I will not silently invent its image, ports, routing, or credentials; the narrow fix applies once the intended service definition or prerequisite branch is identified.

[x] I can write a rough plan for the scoped fix.

I will identify the intended gateway service, add an explicit memory limit using the existing Compose convention, validate the normalized Compose configuration, and verify that Docker reports the expected nonzero runtime limit. I will also update the OOM/setup guidance if the chosen budget changes what developers must allocate to Docker.

[x] I found and read a relevant test file for this configuration.

No existing test parses or validates `docker-compose.yml`, and CI has no Compose resource-limit check. I reviewed the repository's pytest conventions; the fix needs a new configuration-focused test or validation step that asserts the gateway has a valid, nonzero memory limit and that the Compose file normalizes successfully.

### Part 4 - Scope and Time

[x] I checked both issue activity and the cohort ledger's Claims count.

The public issue currently has no comments, linked branch, or pull request. I confirm that the issue was added to the cohort ledger.

[x] The scoped work is realistic for the Week 8-9 timeline.

The issue estimates 2-4 hours, which is reasonable for selecting a memory budget, applying it to an identified Compose service, adding focused validation, and updating related documentation. Even if the work expands into designing and integrating an entirely new gateway, the estimated effort is still reasonable.

[x] The issue has no formally listed blocker or dependency.

GitHub lists no relationship, dependency, linked branch, or pull request. The missing gateway stanza is a scope condition rather than permission to invent a new service: I need to locate the intended definition or confirm the prerequisite with the maintainer before editing.

### Verdict

Under the stated assumption, the issue is understandable and the implementation boundary is clear: enforce and validate a safe memory limit on the intended local LLM gateway without designing a new LLM architecture. I also need to establish the new Compose-validation test because no relevant test currently exists.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/shishkebab/pathreview/commit/d815b303b2f0929f718e8b94291cdf709b71eadd

**Reproduction summary:**
On an isolated 8 GB development virtual machine, start the LiteLLM proxy with both `mem_limit` and `deploy.resources.limits.memory` disabled, verify with `docker inspect` that `HostConfig.Memory=0`, and monitor it with `docker stats` while a controlled process allocates 640 MiB inside the proxy container. The issue is successfully reproduced when the proxy exceeds the intended 512 MiB budget without an enforced ceiling, demonstrating that its memory growth can compete with PostgreSQL, Redis, Chroma, and the host; the same workload can then be repeated with a 512 MiB limit to verify containment.

**PLAN.md link:** https://github.com/shishkebab/pathreview/blob/fix/130-llm-proxy-oom-memory-limit/PLAN.md

**Blockers or open questions:**
The remaining open questions are whether the maintainer considers introducing LiteLLM part of issue #130, whether 512 MiB provides enough headroom under representative proxy traffic, and whether the regression check should be implemented as a pytest configuration test or a Compose validation step in CI.

## Week 9 — Solution building & PR submission

**Selected issue:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

### Check-in 1 (mid-week)

**Current progress:**
I reproduced Issue #146 and confirmed that the four related tests failed because the shared US phone pattern could not match a number beginning with `(` or separators containing spaces. I updated the `phone_us` pattern to recognize parenthesized area codes and the existing dashed, dotted, spaced, and compact formats while preserving accurate match boundaries. I also strengthened the regression tests to check complete redaction, exact detection values and offsets, multiple numbers, embedded identifiers, and unbalanced parentheses. The eight focused phone tests now pass.

**Next steps:**
Move the Issue #146 changes onto a clean branch based on `main`, rerun the focused checks there, create the implementation commit, and prepare the draft pull request. The PR should remain limited to the US phone pattern, its regression tests, and the required course documentation.

**Blockers:**
There is no blocker in the Issue #146 implementation. The current branch still contains the five earlier Issue #130 commits, so it must not be used directly for the new pull request. Repository-wide validation also has unrelated baseline failures: the PII scrubber module has one existing `street_address` false-positive failure, while the broader unit and quality checks report additional pre-existing failures and network-dependent tokenizer setup errors. These results are separate from the eight passing Issue #146 tests.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]

**Tests added or updated:**
[Which test files did you touch? What do they cover?]

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]
