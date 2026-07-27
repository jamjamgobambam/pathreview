## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/pull/249

**Issue title:** Add an end-to-end agent test using a fully stubbed tool suite

**Tier:** [ ] Tier 1  [ ] Tier 2  [*] Tier 3

**Problem summary:**
Currently there is no test that completely undergoes the full agent process from planning, execution, and synthesizing without reinstalling live dependencies. This issue description basically wants us to add an integration test that is able to test the agent using a "stub implementation" of the tools while also utilizing a mock LLM.

Currently no file exists within tests/integration/ that allows for testing the agents. The description specifically calls for the existence of the file "test_agent_orchestrator.py."

A successful fix will be able to test the full agent life cycle without needing the live dependencies and only needing stub implementations.

**Branch name:** test/59-Add-an-end-to-end-agent-test

**Setup confirmation:** [*] App runs locally at localhost:5173

**Cohort ledger:** [*] Issue added to cohort ledger