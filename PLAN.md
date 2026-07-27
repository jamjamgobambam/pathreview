## Solution plan

**Issue:** [issue title and link]

### Understand

What is the root cause of this issue? What behavior is expected vs. actual?

- The root cause is that there is no service configuration for the "LLM proxy" in `docker-compose.yml`. This file is basically a list of containers Docker should start. Right now there are only three entries, and each one has a memory cap set under it. The "LLM proxy" is missing from this list, so there is no container for a memory limit to attach to in the first place. After looking into this more, I understand this is not a simple "add a memory line" fix. A full service block is needed first, including things like image, ports, and volumes, before a memory limit can even be applied.
- Expected behavior: If the "LLM proxy" service existed, it should have a memory limit set just like the other three services. That way, low end machines would not run out of memory and crash other parts of the app.
- Actual behavior: There is no "LLM proxy" service in the file at all right now, so there is nothing being capped for it.

### Map

Which files, functions, or modules are involved?
List the specific files you expect to touch.

- `docker-compose.yml` is the only file this issue touches. This is where the existing services each define `deploy.resources.limits.memory`, and it is also where the missing "LLM proxy" service would need to be added.

### Plan

What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Confirm scope with a maintainer or in an issue comment, since the "LLM proxy" service does not exist yet and I want to make sure adding it is actually the right call.
2. Add the service block to `docker-compose.yml`. This means a new service (for example `llm-proxy`) with an image, a healthcheck similar to the other services, and a `deploy.resources.limits.memory` entry sized to fit an 8GB machine. The other three services already reserve 512M + 256M + 1G = 1.75G, so I need to pick a value that leaves enough headroom for the rest of the app.
3. Size the memory limit appropriately. I will research or estimate a reasonable cap for whatever proxy image is chosen, and try to pick a number that fits the same logic used for the other services instead of just guessing.
4. Verify locally by running `docker compose up -d`, confirming the new service starts, and checking `docker inspect <container> --format '{{.HostConfig.Memory}}'` (or `docker stats`) to confirm the limit is actually being enforced, the same way I would check `db`, `redis`, or `vector-db`.
5. Update `JOURNAL.md` and the PR description to note that no proxy service existed before this change. This way reviewers understand I added a whole new service, not just a small config line, and that it is not scope creep.

### Inputs & outputs

What does your fix take as input? What should it produce or change?

- Input: the current `docker-compose.yml`, using the existing `db`, `redis`, and `vector-db` blocks as the pattern to follow.
- Input: a decision from step 1 of the plan on whether a new "LLM proxy" service block should actually be added, or whether this ends up being more of a scope or documentation clarification instead.
- Input: if a service is added, a chosen proxy image or tag needs to be picked, since none is referenced anywhere in the repo right now, along with a memory value sized for the 8GB minimum spec.
- Output: `docker-compose.yml` is the only file that changes. A new `llm-proxy` (or similarly named) service block would be added, with an image, ports if needed, a healthcheck, and a `deploy.resources.limits.memory` entry, following the same structure already used for the other three services.

### Risks & unknowns

What could go wrong? What are you still unsure about?

Unknowns:

- There is no confirmed identity for the "LLM proxy." Nothing in the repo, including the code, `docker-compose.yml`, `.env.example`, `docs/SETUP.md`, or `docs/ARCHITECTURE.md`, names a specific proxy tool. Without that, any service block I add is really a guess at an image that might not match what was actually intended.
- Even if I pick a proxy image, I do not have real local usage data for it, so any memory number I choose is an estimate rather than something measured. It could end up wrong in either direction: too tight and the proxy gets OOM killed itself, too loose and it does not actually protect the other services on an 8GB machine.

Risks:

- Adding a made up service that does not match reality could get flagged in review as scope creep, or as solving a problem that does not exist, which would waste the review cycle.
- If the memory limit is set too low for whatever image ends up being used, it could cause the new container to crash loop, which just trades one reliability problem for another.
- The total memory already reserved across all capped services is 1.75G. Adding a new proxy limit on top of that needs to stay comfortably under 8GB once the OS, other apps, and the dev servers are accounted for. If I pick a number without checking that total, I could end up recreating the same kind of problem this issue is trying to fix.

### Edge cases

What inputs or states should your fix handle gracefully?

- A machine with less than 8GB of total RAM. The fix should still let the stack start, even if it is a bit slower, so the memory limit should not be set so high that it assumes more headroom than the stated minimum spec actually provides.
- The proxy container briefly going over the limit during startup, such as while downloading a model or warming up a cache. If that happens and it gets OOM killed right away, `docker compose up` should still show a clear failure instead of just hanging, so it is worth checking that the container has a sane restart or health setup like the other three services do.
- A developer who is not actually using the LLM proxy locally, since today the app talks to OpenRouter directly. If a proxy service gets added to compose, it should not break `docker compose up` for developers who are not routing through it. It should be additive, not a new hard requirement.
- Existing developers who already have containers or volumes running. Since this only changes `docker-compose.yml`, running `docker compose up -d` again should cleanly add the new service without disrupting the already running `db`, `redis`, or `vector-db` containers or their volumes.
- The case where the issue turns out not to match reality at all. If the conclusion ends up being "no proxy exists, so there is nothing to add a limit to," the fix can gracefully mean documenting that finding instead of forcing a compose change just to have something to show. A well justified "no code change" should count as a valid outcome here.
