# ADR-003: Agent Orchestration Approach

## Status
Accepted

## Context
The portfolio analysis requires coordinating multiple tools (GitHub API, skill extraction, README scoring, market comparison, tech detection). We considered two approaches: a reactive agent that decides the next tool at each step, and a plan-execute agent that builds a full plan before executing.

## Decision
Use a plan-execute approach. The orchestrator inspects the available profile data, builds an ordered execution plan, and runs tools sequentially with retry and timeout policies. If a tool fails, the orchestrator can replan with the remaining tools.

## Consequences
- More predictable execution order and timing
- Easier to debug (the plan is inspectable)
- Less adaptive than a reactive agent — won't discover new tool needs mid-execution
- Replanning on failure adds complexity
