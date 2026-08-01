## Solution plan

**Issue:** [Add an end-to-end agent test using a fully stubbed tool suite](https://github.com/ascherj/pathreview/issues/59)

### Understand

**Root cause:** `tests/integration/` contains only `__init__.py`. The `Orchestrator` class in `agent/orchestrator.py` — which builds an execution plan, dispatches all five analysis tools, aggregates their results, and persists state to Redis — has zero test coverage. Any regression in `_build_plan()`, `_execute_tool()`, the `ContextManager` cache, or the `SessionStore` handshake would go undetected.

**Expected:** `pytest tests/integration -v` collects and passes at least four tests covering the full Orchestrator lifecycle.

**Actual:** `pytest tests/integration -v` outputs `collected 0 items`.

---

### Map

Files to **create**:
- `tests/integration/test_agent_e2e.py` — the entire deliverable; no production code changes needed

Files to **read** (subject under test, not modified):
- `agent/orchestrator.py` — `run()`, `_build_plan()`, `_execute_tool()`, `_execute_with_timeout()`
- `agent/tools/base.py` — `BaseTool` / `ToolResult` (stub interface)
- `agent/memory/session_store.py` — `SessionStore.get()` / `.set()` (stub interface)
- `agent/memory/context_manager.py` — `ContextManager` (used internally; stubs bypass it)
- `agent/error_handling.py` — `retry_with_backoff(max_retries=2, backoff_factor=1.5)`

---

### Plan

**Step 1 — Stub infrastructure**

Mark the module with `pytestmark = pytest.mark.integration` so `make test-integration` (which runs `pytest -m integration`) actually collects these tests. Without the marker, CI shows green while covering nothing.

Define inside `test_agent_e2e.py`:

```python
class StubSessionStore:
    def __init__(self):
        self.data: dict = {}
    def get(self, session_id):
        return self.data.get(session_id)
    def set(self, session_id, data, ttl_seconds=3600):
        self.data[session_id] = data
```

Define five stub tools — each inherits `BaseTool`, sets `name` as a class attribute matching the key used in `_build_plan()`, and returns a hardcoded `ToolResult(success=True, data={"stub": True})` from `execute()`:

- `StubGithubTool` (name `"github_tool"`)
- `StubTechDetector` (name `"tech_detector"`)
- `StubReadmeScorer` (name `"readme_scorer"`)
- `StubSkillExtractor` (name `"skill_extractor"`)
- `StubMarketAnalyzer` (name `"market_analyzer"`)

**Step 2 — Fixtures**

```python
@pytest.fixture
def stub_store():
    return StubSessionStore()

@pytest.fixture
def all_stubs():
    return {
        "github_tool": StubGithubTool(),
        "tech_detector": StubTechDetector(),
        "readme_scorer": StubReadmeScorer(),
        "skill_extractor": StubSkillExtractor(),
        "market_analyzer": StubMarketAnalyzer(),
    }

@pytest.fixture
def orchestrator(all_stubs, stub_store):
    return Orchestrator(tools=all_stubs, session_store=stub_store)
```

**Step 3 — Happy-path test**

Profile data with all four trigger fields (`github_username` + project with `github_repo`, `files`, `readme_content`, `resume_text`) → all five tools appear in the plan.

Assert:
- `result["profile_id"] == profile_id`
- `result["tool_results"]` contains keys for all five tools
- Each value is `{"stub": True}` (the unwrapped `ToolResult.data`)
- `stub_store.data[profile_id] == result["tool_results"]` (the store persists `tool_results` only, not the top-level `profile_id` / `cached_results` keys)

**Step 4 — Partial-profile test**

Profile data with only `readme_content` and `resume_text` (no `github_username`, no `files`) → plan contains only `readme_scorer`, `skill_extractor`, `market_analyzer`.

Assert:
- `"github_tool"` and `"tech_detector"` are **not** in `result["tool_results"]`
- The three included tools are present and succeeded

**Step 5 — Tool-failure test**

Replace one stub's `execute()` to raise `RuntimeError("boom")` unconditionally, and track call count on the stub. Patch `agent.error_handling.time.sleep` to skip the backoff delay.

`retry_with_backoff(max_retries=2, ...)` will call `execute()` **twice** before giving up (attempt 1 → sleep → attempt 2 → raise), so assertions must reflect that:

- The failing tool's result is `{"error": "boom", "success": False}`
- `failing_stub.call_count == 2` (retry ran once, then gave up)
- All other tools still have successful results (orchestrator does not abort on one failure)

**Step 6 — Session-persistence test**

Two-part test to cover both directions of the `SessionStore` handshake:

*6a. Post-run write.* After `run()`, inspect `stub_store.data[profile_id]` directly. Assert the dict is non-empty and contains keys for every tool in the plan.

*6b. Pre-run hydration.* Pre-seed `stub_store.data[profile_id] = {"stale_key": "stale_value"}`, then call `run()`. Assert that `stale_key` survives in the post-run stored dict — this proves the orchestrator loads prior session state via `session_store.get(...)` and merges into it, rather than overwriting. Without this, a regression that drops the `session_store.get(profile_id) or {}` line would silently pass.

---

### Inputs & outputs

| Scenario | Input `profile_data` | Expected `tool_results` keys | Side effect on `stub_store` |
|---|---|---|---|
| Happy path | All four fields | All five tools | `data[profile_id]` = 5-key dict |
| Partial profile | `readme_content` + `resume_text` only | `readme_scorer`, `skill_extractor`, `market_analyzer` | `data[profile_id]` = 3-key dict |
| Tool failure | All four fields; one stub raises | All five keys; failing tool has `{"error": ..., "success": False}` | `data[profile_id]` includes the error entry |
| Session persistence | Any | Any | `stub_store.data[profile_id]` is a non-empty dict matching `tool_results` |

---

### Risks & unknowns

1. **`retry_with_backoff` sleeps and retries — 2 attempts, 1.0 s sleep between them.** With `max_retries=2, backoff_factor=1.5`, the wait is `1.5 ** (attempt - 1) = 1.5^0 = 1.0 s` (not 1.5 s), and any raising tool is called twice. Fix: `unittest.mock.patch("agent.error_handling.time.sleep")` in the failure test, and expect `call_count == 2`.

2. **`market_analyzer` is added if `plan` is non-empty** at the end of `_build_plan()`. This means the empty-profile edge case (`profile_data = {}`) produces an empty plan with no `market_analyzer`. Test the empty case to document this boundary.

3. **`_execute_with_timeout` does not enforce a real timeout.** It logs a warning when `elapsed > tool_timeout` but never raises `TimeoutError`. No timeout test is needed; this is an existing implementation gap, not in scope for this issue.

4. **CI log noise from the failure test.** `retry_with_backoff` logs at `warning` on each retry attempt and `error` on exhaustion, plus the orchestrator's outer `except` logs another `error`. Use `caplog` to assert those log records if we want observability coverage; otherwise expect noisy but green CI output for Step 5.

---

### Edge cases

| Case | How to handle |
|---|---|
| `profile_data = {}` | `_build_plan()` returns `[]`; `run()` returns `{"profile_id": ..., "tool_results": {}, "cached_results": {}}` — assert this shape |
| `session_store=None` | No `get`/`set` calls — `run()` still returns results; assert no `AttributeError` |
| Repeated `run()` with same input on same Orchestrator | Second call returns cached results via `ContextManager` (instance-level cache); each stub's `execute()` is called only once across both runs |
| Pre-existing session state for `profile_id` | Covered by Step 6b — prior keys must survive after `run()` merges new results |
