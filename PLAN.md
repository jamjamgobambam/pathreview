## Solution plan

**Issue:** Add an integration test that runs the full RAG pipeline against a mock LLM —
https://github.com/ascherj/pathreview/issues/38

### Understand
The RAG pipeline is built from independently-tested stages: `HybridRetriever`
(`rag/retriever/hybrid.py`, blending `VectorStore` + `KeywordSearcher` results),
`ReviewGenerator` (`rag/generator/review_generator.py`, calls an LLM to produce feedback
text per section), and `parse_review_output` (`rag/generator/output_parser.py`, turns raw
LLM text into `FeedbackSection` objects). Each has unit tests in isolation
(`tests/unit/test_keyword_search.py`, `tests/unit/test_output_parser.py`, etc.), but
nothing runs them chained together. A repo-wide search confirms `HybridRetriever`,
`ReviewGenerator`, and `parse_review_output` are each referenced only inside their own
defining file — no orchestration point exists (`core/services/review_service.py`'s
`_run_rag_retrieval_generation` is a stub that returns hardcoded data and never calls
any of these classes). Root cause: a shape/contract mismatch at a seam between stages —
e.g. the dict keys `HybridRetriever.retrieve()` returns (`text`, `metadata`, `score`)
no longer matching what `ReviewGenerator._format_context()` expects — could pass every
unit test while silently breaking the real end-to-end flow, because nothing asserts the
seams line up. Expected behavior: a `tests/integration/` test drives a representative
query through retrieval → generation → parsing against a deterministic mock and asserts
a well-formed review comes out. Actual behavior: `tests/integration/` contains only
`__init__.py` — confirmed by running
`.venv/Scripts/python.exe -m pytest tests/integration -v -m integration`, which reports
`no tests ran in 4.22s` (0 items collected).

**Divergence from the issue text:** the issue says "retrieval → reranking → generation →
parsing," but there is no reranking stage anywhere in `rag/` (no `rag/reranker/`
directory, zero matches for `rerank` repo-wide). The test will cover the pipeline that
actually exists — retrieval → generation → parsing — and this gap is called out rather
than silently ignored.

### Map
- `rag/retriever/hybrid.py` — `HybridRetriever.__init__(vector_store, keyword_searcher,
  vector_weight=0.7, keyword_weight=0.3)`, `.retrieve(query, profile_id, query_embedding,
  max_chunks=10, min_score=0.3) -> list[dict]`. Blends vector + BM25 scores, filters by
  `min_score`, returns top `max_chunks`.
- `rag/retriever/vector_store.py` — `VectorStore(persist_dir)`, backed by a real Chroma
  `PersistentClient`; `.get_collection(name)`, `.add_chunks(...)`, `.query(...)`.
- `rag/retriever/keyword_search.py` — `KeywordSearcher`, in-memory BM25, `.index(chunks)`,
  `.search(query, top_k)`.
- `rag/generator/review_generator.py` — `ReviewConfig` dataclass (`api_key`, `base_url`,
  `model`, `temperature`, `max_tokens`); `ReviewGenerator.__init__` builds
  `self.client = openai.OpenAI(api_key=..., base_url=...)` directly (line 34, no
  injectable client param); `.generate_full_review(profile_data, retrieved_chunks) ->
  list[FeedbackSection]` loops 5 fixed section names, calls `.generate_section(...)` per
  section, catches exceptions per-section, adds citations, consolidates.
- `rag/generator/output_parser.py` — `FeedbackSection` dataclass (`section_name`,
  `content`, `confidence`, `suggestions`); `parse_review_output(raw) -> list[FeedbackSection]`
  tries JSON-in-fence, then raw JSON, then falls back to one plaintext section.
- `ingestion/embeddings/provider.py` — `MockEmbeddingProvider.embed(texts) ->
  list[list[float]]`, deterministic (SHA-256 hash → seeded RNG → normalized 1536-dim
  vector); this is the existing "mock" building block for embeddings, reused to produce
  query/document embeddings in the test.
- New file: `tests/integration/test_rag_pipeline.py` (target of the issue). `tests/conftest.py`
  currently only holds `sample_resume_text`/`sample_readme_text` fixtures — new
  fixtures for this test will live either in the new file or a new
  `tests/integration/conftest.py`.

### Plan
1. Add fixtures that stand up a `VectorStore` against a pytest `tmp_path` (Chroma
   `PersistentClient` supports a plain local directory — no Docker/network needed) and
   seed it with 2-3 known profile chunks, embedded via `MockEmbeddingProvider`, plus a
   matching `KeywordSearcher.index(...)` call over the same chunks.
2. Write a fake OpenAI client (a small class or `unittest.mock.MagicMock` shaped to
   match) whose `chat.completions.create(...)` returns a canned response object with
   `.choices[0].message.content` set to a JSON-fenced string that
   `parse_review_output` will route through its first (JSON-in-fence) branch, and
   monkeypatch `rag.generator.review_generator.openai.OpenAI` so `ReviewGenerator.__init__`
   picks it up.
3. Instantiate `HybridRetriever(vector_store, keyword_searcher)`, call `.retrieve(query,
   profile_id, query_embedding=MockEmbeddingProvider().embed([query])[0])`, then feed the
   resulting chunks into `ReviewGenerator(ReviewConfig(...)).generate_full_review(profile_data,
   chunks)`.
4. Assert on the full path: `.retrieve()` returns non-empty chunks with the expected dict
   shape (`id`, `text`, `metadata`, `score`); `generate_full_review()` returns exactly 5
   `FeedbackSection`s (one per fixed section name), each with non-empty `content` and a
   `confidence` in `[0, 1]`; confirm citations get appended to `content` when chunks exist
   (`Sources:` substring present).
5. Mark the test class `@pytest.mark.integration` (per `pyproject.toml`'s registered
   markers) and confirm `pytest tests/integration -v -m integration` now collects >0
   items and passes with no Docker/network/live API key required, so `make
   test-integration` picks it up in CI.

### Inputs & outputs
**Input:** a `profile_id`, a query string representative of a real review request (e.g.
"How strong are this candidate's backend skills?"), and a small fixed corpus of
profile-like text chunks (resume/README snippets) embedded via `MockEmbeddingProvider`.
**Output:** a `list[FeedbackSection]` of length 5, with deterministic `content` and
`confidence` values (deterministic because both the embeddings and the fake chat
response are canned/seeded, not live).

**Risks & unknowns:**
- `ReviewGenerator.__init__` (`rag/generator/review_generator.py:34`) constructs
  `openai.OpenAI` directly inside `__init__` rather than accepting an injected client —
  the monkeypatch must target `rag.generator.review_generator.openai.OpenAI` (the name
  as imported in that module), not `openai.OpenAI` globally, or the patch will silently
  no-op and the test will attempt a real network call.
- `VectorStore` (`rag/retriever/vector_store.py`) is backed by a real Chroma
  `PersistentClient` — pointing it at a pytest `tmp_path` avoids needing the Docker
  Chroma container, but Chroma's on-disk schema/version could change between the
  installed `chromadb` version and what's pinned, so the test should confirm this
  actually collects without Docker before assuming it's a good CI fit.
- `parse_review_output` (`rag/generator/output_parser.py`) has three fallback branches
  (JSON-fenced, raw JSON, plaintext) — the canned fake-LLM response's exact string
  format determines which branch runs; the test must pin the response format
  deliberately (JSON-in-fence) so it isn't accidentally testing the plaintext fallback
  instead of the intended structured path.
- `HybridRetriever._get_all_chunks()` (`rag/retriever/hybrid.py:106`) re-fetches all
  chunks from the vector store's collection to build the keyword index's chunk-lookup —
  the seeded chunks must be added through `VectorStore.add_chunks(...)` (not only
  `KeywordSearcher.index(...)`) or this lookup will silently return an empty chunk map
  for keyword-only hits.

### Edge cases
- **Empty/low-similarity corpus:** if `HybridRetriever.retrieve()`'s `min_score=0.3`
  filter excludes every candidate (e.g. a query unrelated to the seeded corpus), the
  retrieval step returns zero chunks; the test should assert `generate_full_review()`
  still returns exactly 5 sections (via `ReviewGenerator`'s existing per-section
  try/except in `generate_full_review`, `rag/generator/review_generator.py:126`) rather
  than raising, confirming the pipeline degrades gracefully with no context.
- **Malformed/unparseable LLM output for one section:** if the fake client's response
  content isn't valid JSON-in-fence for one call (simulate by having the fake return a
  broken payload for a single section), confirm the existing per-section
  `except Exception` path (`review_generator.py:126-135`) still yields a placeholder
  `FeedbackSection(content=f"Error generating {section_name}", confidence=0.0)` instead
  of failing the whole `generate_full_review()` call.

You'll update this file as your understanding evolves in Week 9. It's a living document,
not a contract.
