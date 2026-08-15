# Solution Plan for Issue #47

## Solution plan

**Issue:** [Agent state isn't persisted across API restarts, causing in-progress reviews to be lost](https://github.com/ascherj/pathreview/issues/47)

### Understand

**Root cause:** The `ContextManager` class stores tool execution results in memory only (`self.results` dictionary). When the Orchestrator is re-initialized after an API restart, this in-memory cache is lost, even though `SessionStore` persists some session state to Redis.

**Expected behavior:** Long-running reviews (5+ repositories) should preserve cached tool results across server restarts, allowing them to resume without re-executing the same expensive operations.

**Actual behavior:** On API restart, the ContextManager cache is empty, causing tool re-execution and loss of progress during long-running reviews.

### Map

**Files involved:**
1. `agent/memory/context_manager.py` - Stores results in memory only
2. `agent/memory/session_store.py` - Persists session state to Redis (not cache)
3. `agent/orchestrator.py` - Creates and uses ContextManager, initializes new instance on each run
4. `core/services/review_service.py` - Calls agent orchestration (placeholder currently)

**Key functions:**
- `ContextManager.__init__()` - Initializes empty results dict
- `ContextManager.store_tool_result()` - Caches result in memory
- `ContextManager.get_tool_result()` - Retrieves from memory cache
- `Orchestrator.__init__()` - Creates new ContextManager instance
- `Orchestrator.run()` - Loads session state from Redis but not cached results
- `SessionStore.get()` / `SessionStore.set()` - Redis persistence layer

### Plan

**High-level approach:** Extend SessionStore to persist and restore ContextManager cache alongside session state, ensuring cached tool results survive server restarts.

**Concrete sub-tasks:**

1. **Extend ContextManager to serialize/deserialize cached results**
   - Add method `to_dict()` that returns results in JSON-serializable format
   - Add method `from_dict(data)` that restores results from dict
   - Handle edge cases: non-serializable result objects

2. **Extend SessionStore to manage context cache**
   - Add separate Redis key prefix for context cache: `cache:<profile_id>`
   - Implement `set_cache()` method to persist ContextManager results
   - Implement `get_cache()` method to restore ContextManager results
   - Use same TTL as session data (1 hour default)

3. **Update Orchestrator to load and persist context cache**
   - In `__init__()`: Add optional parameter to initialize from saved cache
   - In `run()`: After loading session state, also load cached results into ContextManager
   - In `run()`: After execution completes, persist context cache via SessionStore

4. **Add integration test demonstrating persistence across restarts**
   - Create test that simulates: run → restart → resume
   - Verify cache hit rate (tool not re-executed)
   - Ensure session integrity during restart

5. **Update review_service.py to use new persistence**
   - Pass session store to Orchestrator
   - Verify profile_id consistency between session and cache keys

### Inputs & outputs

**Inputs:**
- Profile ID (string) - used as session/cache key
- Tool execution results (dict) - cached in memory
- Redis client instance - for persistence

**Outputs:**
- ContextManager cache persisted to Redis with TTL
- Restored ContextManager on Orchestrator restart
- Cache keys follow pattern: `cache:<profile_id>`
- Session data and cache data aligned (same profile_id)

### Risks & unknowns

**Risks:**
1. **Serialization of complex results** - Tool results might contain non-JSON-serializable objects (custom classes, file handles). Need to handle gracefully with fallback or conversion.
2. **Cache key collision** - If profile IDs aren't unique across users, cache could leak between profiles. Must verify SessionStore uses `profile_id` that includes user context.
3. **Stale cache after deployment** - Redis keys might persist beyond expected TTL if Redis is not cleared. Could be mitigated with version prefix in cache keys.
4. **Redis unavailability** - If Redis is down, cache persistence fails silently in SessionStore. Need to log errors and ensure graceful degradation.

**Unknowns:**
- What exactly do tool results contain? Are they JSON-serializable by default?
- How are profile IDs constructed? Do they include user ID?
- What's the expected maximum size of cached results for 5+ repo review?
- Is there existing serialization pattern in the codebase (e.g., in models)?

**Investigation paths:**
- Check `agent/tools/*.py` to see what `execute()` methods return
- Look at `agent/tools/base.py` for ToolResult schema
- Check how profile_id is passed in review_service.py
- Verify SessionStore key format includes user context

### Edge cases

**What the fix should handle gracefully:**

1. **Non-serializable result objects**
   - If tool result contains objects that can't be JSON-encoded, try to convert to dict or string representation
   - Log warning but don't fail - graceful degradation

2. **Partial cache on restart**
   - If Redis has stale cache from previous profile, overwrite with new session
   - If some tools succeeded but Redis persistence failed, resume with partial cache

3. **Cache key collisions across users**
   - Ensure profile_id in cache key cannot accidentally match another user's profile
   - Consider adding user_id or session_id to cache key prefix

4. **Very long-running reviews**
   - Cache expires after TTL (1 hour default) - but review might take longer
   - Could extend TTL for active reviews, or implement LRU eviction

5. **Multiple concurrent reviews on same profile**
   - If user starts review, restarts API, starts another review before first completes
   - Need to distinguish cache between concurrent runs (use review_id not just profile_id)

6. **Redis connection failures**
   - If SessionStore.set_cache() fails, cache persistence fails silently
   - Should log error but allow review to continue with in-memory cache only
   - Document that reviews aren't truly persistent without working Redis

**Edge case mitigation:**
- Use `review_id` as cache key (more specific than profile_id)
- Add try-except with logging around cache operations
- Document Redis requirement for production persistence
- Add tests for partial/stale cache scenarios

---

## Implementation notes (Week 9)

What actually shipped, and where it differed from the plan above.

**Answered from the Week 8 open questions:**
- Tool results are `ToolResult` dataclasses (`agent/tools/base.py`) — JSON-safe
  via `dataclasses.asdict`, so no custom encoder was needed.
- Kept `profile_id` as the cache key rather than switching to `review_id`.
  `SessionStore` already keys session state by `profile_id`, and the orchestrator
  only receives `profile_id`; reusing it keeps the cache aligned with the
  existing session and avoids a wider signature change. Noted as a follow-up if
  concurrent reviews on one profile ever need isolation.

**What changed from the plan:**
- Added checkpointing after *every* tool, not just at the end of `run()`. The
  issue is about reviews interrupted partway through, so persisting only on
  completion wouldn't have saved partial progress. A small `_checkpoint` helper
  writes session state + cache after each tool.
- Serialization tags each entry (`__kind__`) so `from_dict` can rebuild a real
  `ToolResult` on restore and cache hits keep the same `.data` interface.

**Files touched:**
- `agent/memory/context_manager.py` — `to_dict` / `from_dict` + helpers
- `agent/memory/session_store.py` — `get_cache` / `set_cache`
- `agent/orchestrator.py` — restore on start, `_checkpoint` after each tool
- `tests/unit/test_agent_state_persistence.py` — serialization, store, and
  end-to-end restart tests (10 tests, using an in-memory `FakeRedis`)
