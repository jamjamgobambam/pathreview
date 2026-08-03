# `test_rag_pipeline.py` — Explanation

## Why this test exists

Before this file, `retrieval`, `keyword_search`, `hybrid`, and `review_generator` /
`output_parser` each had unit tests in isolation, but nothing ran a query through
all of them wired together. A change to one module's return shape (e.g. a
renamed dict key) could break the pipeline without any test catching it. This
is Issue #38: one end-to-end test that proves the four stages actually connect.

**Note on "reranking":** there's no separate reranker module in `rag/`. Score
blending + re-sorting happens inline in `HybridRetriever.retrieve()`
(`rag/retriever/hybrid.py:78-94`), so that step *is* the reranking stage the
issue asks for.

## The four stages, in order

### 1. Retrieval — build a corpus and index it two ways

```python
embedder = MockEmbeddingProvider()
vector_store = VectorStore(persist_dir=str(tmp_path))
collection = vector_store.get_collection(f"profile_{PROFILE_ID}")
collection.upsert(ids=..., embeddings=embedder.embed([...]), documents=..., metadatas=...)

keyword_searcher = KeywordSearcher()
keyword_searcher.index(corpus)
```

- `corpus` (the `corpus` fixture) is built by splitting the shared
  `sample_resume_text` / `sample_readme_text` fixtures (`tests/conftest.py`)
  into naive line-level chunks via `_line_chunks()`, tagging each with a
  `source_id` of `"resume"` or `"readme"`. This gives the test real,
  human-readable text instead of synthetic strings.
- `MockEmbeddingProvider` (`ingestion/embeddings/provider.py:24`) turns each
  chunk's text into a deterministic 1536-dim vector via a SHA-256 hash seeding
  `numpy`'s RNG — same text always gets the same vector, but the vectors carry
  **no real semantic meaning**. This matters later (see the assertion note
  below).
- `VectorStore` (`rag/retriever/vector_store.py`) is a thin wrapper around a
  real ChromaDB `PersistentClient`, pointed at `tmp_path` (pytest's per-test
  temp dir) so nothing touches a shared/persistent DB.
- `KeywordSearcher` (`rag/retriever/keyword_search.py`) builds a BM25 index
  (`rank_bm25.BM25Okapi`) over the same chunks for sparse/lexical matching.

### 2. Reranking — `HybridRetriever.retrieve()`

```python
retriever = HybridRetriever(vector_store, keyword_searcher)
retrieved_chunks = retriever.retrieve(query, PROFILE_ID, query_embedding, max_chunks=5, min_score=0.0)
```

`HybridRetriever` (`rag/retriever/hybrid.py`) runs both searches, normalizes
each score set to 0-1 by dividing by its own max, then blends them
`0.7 * vector_score + 0.3 * keyword_score` per chunk id, and sorts descending.
That blend-and-sort step is the "reranking."

Assertions here check the wiring, not just the presence of results:
- `retrieved_chunks` is non-empty and already sorted by `score` descending.
- The top result's `source_id` is `"resume"` and its text contains `"python"`
  (case-insensitive) — this is deliberately anchored to the **BM25 signal**,
  because the query is `"What Python backend experience does this candidate
  have?"` and the resume chunk literally contains "Python". Since
  `MockEmbeddingProvider` embeddings are random noise, the vector score can't
  be relied on to surface the right chunk — only BM25 can. That's why the
  comment on line 98 exists: it documents *why* this assertion is safe despite
  using fake embeddings.

### 3. Generation — `ReviewGenerator.generate_full_review()`

```python
generator = ReviewGenerator(ReviewConfig(api_key="test", base_url="http://mock.invalid", model="mock-model"))
generator.client = _mock_llm_client(SECTION_PAYLOADS)
sections = generator.generate_full_review(profile_data, retrieved_chunks)
```

`ReviewGenerator.__init__` (`rag/generator/review_generator.py:27`) normally
constructs a real `openai.OpenAI` client. The test lets that construction
happen (it's just building a client object, no network call), then
**swaps `generator.client`** for `_mock_llm_client(...)` — a `SimpleNamespace`
shaped like the openai client (`client.chat.completions.create`), backed by a
`unittest.mock.Mock(side_effect=responses)` that returns one canned response
per call, in order. This is what "no live network calls" means in practice:
the real OpenAI SDK objects are used for typing/shape, but nothing ever hits
the network.

`generate_full_review()` (`rag/generator/review_generator.py:93`) loops over
5 fixed section names — `skills_feedback`, `projects_feedback`,
`presentation_feedback`, `gaps_feedback`, `first_impression` — calling
`generate_section()` for each, which builds a prompt from a template + the
retrieved context chunks, calls `client.chat.completions.create(...)`, and
parses the response. `SECTION_PAYLOADS` supplies one canned LLM response per
section **in that exact order** — four JSON payloads and one plain-text
payload (mimicking a model that ignores the "respond as JSON" instruction for
`first_impression`).

### 4. Parsing — `output_parser.parse_review_output()`

Called internally by `generate_section()`, not directly by the test.
`parse_review_output()` (`rag/generator/output_parser.py:20`) tries, in order:
JSON inside a ` ```json ` fence, then raw JSON, then falls back to treating
the whole response as one plain-text section named `"general_feedback"`.

This is why the test's expected section names are:
```
["skills_feedback", "projects_feedback", "presentation_feedback", "gaps_feedback", "general_feedback"]
```
— the first four round-trip through JSON parsing and keep their key as the
section name, but the fifth payload (`first_impression`'s canned response) is
plain text, so the parser falls through to `general_feedback` regardless of
what the request template was named. The test asserts on the *parser's*
naming, not the *template's* naming — that's the real end-to-end behavior a
unit test on either module in isolation wouldn't catch.

## Final assertions

```python
assert generator.client.chat.completions.create.call_count == 5
for section in sections:
    assert section.content
    assert 0.0 <= section.confidence <= 1.0
    assert "Sources:" in section.content
```

- `call_count == 5` confirms all five sections actually triggered an LLM call
  (nothing short-circuited).
- Every section has non-empty content and a confidence in range — sanity
  checks on the parser's output contract.
- `"Sources:"` in every section's content confirms `_add_citations()`
  (`rag/generator/review_generator.py:162`) ran and appended the retrieved
  chunks' `source_id`s — proving retrieval output actually flowed through to
  the final generated text, closing the loop from stage 1 to stage 4.

## Pre-existing failures (unrelated to this change)

`tests/integration/test_rag_pipeline.py` itself is lint-clean (`ruff check`,
`black --check`) and passes on its own: `pytest tests/integration -v -m
integration` → 1 passed.

Running the full unit suite (`make test-unit` /
`pytest tests/unit -v -m unit`) shows **53 pre-existing failures** in modules
this change never touches:

- `test_batch_processor.py` (1)
- `test_bias_detector.py` (9)
- `test_faithfulness_checker.py` (4)
- `test_keyword_search.py` (1)
- `test_output_parser.py` (1)
- `test_pii_scrubber.py` (5)
- `test_prompt_defense.py` (1)
- `test_readme_parser.py` (2)
- `test_readme_scorer.py` (1)
- `test_relevance_scorer.py` (1)
- `test_resume_parser.py` (5)
- `test_review_service.py` (12)
- `test_security.py` (1)
- `test_skill_extractor.py` (5)
- `test_structural_chunker.py` (1)
- `test_tech_detector.py` (2)

These were observed before writing `test_rag_pipeline.py` and are unrelated
to this issue (#38): none of them import or exercise
`rag/retriever/hybrid.py`, `rag/retriever/vector_store.py`,
`rag/retriever/keyword_search.py`, or `rag/generator/review_generator.py` in
a way this test's changes could affect, and `test_keyword_search.py::
test_empty_index` / `test_output_parser.py::test_json_array_fallback` fail
for reasons internal to those modules, not from anything this new
integration test adds or imports. **This change does not introduce any new
failures and does not affect the pass/fail status of any of the above.**
