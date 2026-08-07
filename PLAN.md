## Solution plan

**Issue:** [Implement a caching layer for repeated identical portfolio queries](https://github.com/ascherj/pathreview/issues/32)

### Understand

`core/services/review_service.py::process_review()` currently runs the ingestion,
agent-orchestration, RAG-generation, and safety-check stages for every review. It
does not look for a previous result before calling
`_run_rag_retrieval_generation()`, so two profiles containing the same portfolio
content cause the expensive generation path to run twice.

The existing `agent/memory/context_manager.py` cache only memoizes tool calls in
one in-memory agent session. It does not persist complete review results or share
them with later requests. Redis is already included in the Python dependencies,
Docker Compose services, application settings, and example environment file, but
the review service does not use it.

Expected behavior:

- Identical portfolio content submitted by the same user reuses the previously
  generated review.
- Cache entries are isolated by user so one user can never receive another
  user's cached feedback.
- A change to the resume or other ingested portfolio content produces a different
  content hash and therefore a cache miss.
- A Redis connection, read, deserialization, or write failure is logged and the
  normal RAG path continues without failing the review.

Actual behavior:

- Every review unconditionally invokes the RAG-generation function, including
  repeated submissions with identical content.

### Map

Files and modules involved:

- `core/services/review_service.py`
  - Integrate cache lookup and storage into `process_review()`.
  - Preserve the current status updates, safety checks, and failure handling.
- `core/services/review_cache.py` (new)
  - Build deterministic, user-scoped content keys.
  - Read, validate, serialize, and store review results in Redis.
  - Treat Redis failures as cache misses instead of application failures.
- `core/config.py`
  - Add configurable cache TTL and optional cache-key version settings.
- `.env.example`
  - Document the review-cache settings and defaults.
- `tests/unit/test_review_cache.py` (new)
  - Test hashing, user isolation, serialization, TTL usage, and Redis failures.
- `tests/unit/test_review_service.py`
  - Keep the reproduction test and add hit, miss, invalidation, and fallback
    coverage around `process_review()`.
- `tests/integration/` (if needed)
  - Verify a real Redis round trip using the existing Docker service.

No frontend changes should be required because the review API response and review
status lifecycle will remain the same.

### Plan

1. Define the cache contract and deterministic key.
   - Canonically serialize the normalized ingestion results using sorted JSON.
   - Hash the serialized content with SHA-256.
   - Include the user ID and a cache schema/version prefix in the Redis key.
   - Exclude profile and review IDs so separate records with identical content
     for the same user can share a result.

2. Add an asynchronous Redis-backed review cache.
   - Use the existing `REDIS_URL` setting and `redis.asyncio` client.
   - Store the complete validated RAG output as JSON with a configurable TTL.
   - Return `None` for cache misses, malformed values, and Redis errors.
   - Emit structured logs for cache hits, misses, writes, and failures without
     logging resume text or other private portfolio content.

3. Integrate caching into `process_review()`.
   - Run ingestion first so the key represents the current source content.
   - Check the user-scoped content key before agent orchestration and RAG
     generation.
   - On a hit, reuse the cached RAG output and continue through safety validation
     and normal review persistence.
   - On a miss, run the existing agent and RAG stages, validate the output, then
     cache only a successful result.
   - If any cache operation fails, log the failure and continue through the
     uncached path.

4. Add automated coverage for the cache contract.
   - Confirm identical content for one user invokes RAG only once.
   - Confirm identical content submitted by different users does not share cache
     entries.
   - Confirm changed resume content creates a miss and invokes RAG again.
   - Confirm changed GitHub or portfolio ingestion data also creates a miss.
   - Confirm Redis read/write failures and malformed cached JSON fall back to
     normal generation.
   - Confirm failed or safety-rejected generation output is not cached.

5. Validate and document the completed behavior.
   - Run unit tests, Redis integration tests, Ruff, Black, and Mypy.
   - Manually submit identical content twice and confirm the second request logs
     a cache hit and returns equivalent feedback.
   - Change the resume content and confirm the next request logs a miss.
   - Document the TTL setting and local Redis requirement in `.env.example` or
     the relevant setup documentation.

### Inputs & outputs

Inputs used to derive a cache key:

- Authenticated user ID.
- Canonically serialized ingestion results, including resume text, GitHub data,
  and portfolio data.
- A cache schema/version prefix so incompatible result or prompt changes can
  invalidate older entries.

Cached value:

- The JSON-serializable RAG output containing feedback sections and the overall
  score.

Outputs and observable behavior:

- A cache miss produces and stores a normal review through the existing RAG path.
- A cache hit produces a new `Review` record using the cached feedback without
  another RAG call.
- Changed portfolio content produces a different hash and a fresh review.
- Redis failures produce a normal uncached review rather than an API failure.
- The frontend and API response schemas remain unchanged.

### Risks & unknowns

- The final cache TTL is not specified. It should be configurable; a one-day
  default is a reasonable starting point but should be confirmed with the issue
  owner or mentor.
- Two identical requests arriving concurrently could both miss and run RAG
  before either stores a value. A Redis lock or single-flight mechanism may be
  useful, but it may be deferred if issue #32 only requires reuse after the first
  review completes.
- Cache keys must never contain raw resume or portfolio text. Only a cryptographic
  hash and the owning user ID should appear in Redis keys or logs.
- Prompt, model, output-schema, or safety-policy changes can make old results
  stale even if portfolio content is unchanged. A version component is needed in
  the key, and the invalidation policy must be documented.
- Cached JSON must be validated before use so corrupt or outdated entries do not
  cause review processing to fail.
- The current ingestion functions contain placeholder source data. Tests should
  verify the cache against ingestion output rather than assume future GitHub and
  portfolio fetchers remain unchanged.

### Edge cases

- Empty optional portfolio URL with otherwise identical content.
- Whitespace or ordering differences in equivalent serialized ingestion data.
- Same content submitted under different profile and review IDs.
- Same content submitted by different users.
- Resume content changes while the filename stays the same.
- Resume filename changes while the content stays the same.
- GitHub or portfolio source content changes without changing its URL or username.
- Unicode and large resume text.
- Redis unavailable, timed out, or returning malformed JSON.
- Cached data missing required feedback fields.
- RAG generation or safety validation fails; no unsuccessful output should be
  cached.
- Concurrent identical submissions before the first cache write completes.
