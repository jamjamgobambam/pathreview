## Solution plan

**Issue:** (https://github.com/ascherj/pathreview/issues/130)
docker-compose.yml doesn't set memory limits for the LLM proxy service, causing OOM kills on 8GB machines #130

### Understand
The root cause is that the local Docker compose setup does not define memory constraints for the LLM proxy service, so the proxy container can consume too much RAM and be killed by the host OS on machines with limited memory. The expected behavior is that the proxy container should start with a conservative memory cap so it remains stable on 8GB systems, while the existing db, redis, and vector-db services continue to run normally.

### Map
Files and modules involved:
- docker-compose.yml: add or update the LLM proxy service and set memory limits for it.
- Optional related configuration files if the proxy service needs a specific image, environment variables, or startup command.
- Any local development docs, if the compose setup is documented and should reflect the new resource limits.

### Plan
1. Review the existing compose services and confirm how the LLM proxy is expected to run in the local stack.
2. Add the LLM proxy service to docker-compose.yml with explicit memory limits that are safe for 8GB machines.
3. Validate the compose configuration and confirm the stack still starts correctly with the new resource constraints.
4. Test the updated setup locally to ensure the proxy does not crash due to memory pressure.

### Inputs & outputs
Inputs:
- The current docker-compose.yml configuration.
- The issue description and journal notes describing the OOM problem.
- Local development expectations for the LLM proxy service.

Outputs:
- A compose configuration that includes memory limits for the LLM proxy service.
- A more stable local development environment that reduces the risk of OOM kills.

### Risks & unknowns
- The exact proxy image or startup command may need to be confirmed before editing the compose file.
- A memory limit that is too low could cause the proxy to fail under heavier workloads.
- The fix should preserve existing behavior for the other supporting services while only tightening resource usage for the proxy.

### Edge cases
- Systems with limited available RAM should still be able to start the stack without the proxy being killed.
- The proxy should handle memory pressure gracefully rather than crashing unexpectedly.
- Existing services should continue working unchanged when the new limits are introduced.