# Reflection — Issue #40: offline eval runner

**Issue:** [ascherj/pathreview#40](https://github.com/ascherj/pathreview/issues/40)
**Pull request:** [ascherj/pathreview#658](https://github.com/ascherj/pathreview/pull/658)
**Branch:** `feat/40-offline-eval-runner`
**Written:** 2026-08-02

Supporting documents: [reproduction](../reproductions/issue-40-offline-eval-runner.md) · [plan](../../PLAN.md) · [journal](../../JOURNAL.md)

---

## Why I picked this issue

I chose #40 because its surface matched what I am strongest at — Python, RAG pipelines, retrieval, JSON contracts, pytest — and because as a Tier 3 it was clearly not a one-file fix. The issue named two files (`scripts/run_evals.py`, `rag/evaluator/eval_suite.py`) but the work obviously spanned `rag/retriever/`, `rag/generator/`, `rag/evaluator/`, `ingestion/chunking/`, `ingestion/embeddings/` and `scripts/`. I wanted an issue where the difficulty was *integration and determinism* rather than volume of code, because that is the kind of problem where reading a codebase carefully actually pays off.

I also picked it because it had a hard, checkable success condition. `.github/workflows/eval.yml` already ran `python scripts/run_evals.py` with `LLM_PROVIDER: mock`, no `services:` block, on Python 3.11, and read `eval_results.json` from the repo root. That is a contract I could verify against rather than a matter of taste.

## What the issue appeared to require

The issue body reads: *"The current eval suite runs inline during API requests. Add a standalone eval runner (`scripts/run_evals.py`) that tests the full RAG pipeline against a curated set of benchmark portfolios and outputs a JSON report of quality scores."*

That describes a **refactor**: take evaluation that currently runs in the request path, lift it out, point it at fixtures instead of live requests. I expected to spend my time on fixture design and on the JSON schema, and to reuse the wiring that `process_review()` already had.

That framing was wrong, and finding out *how* wrong was the most valuable part of the work.

## What reproduction actually revealed

I ran the thing before I changed anything, which turned out to matter more than usual.

**The runner was a stub that reported success.** `LLM_PROVIDER=mock python scripts/run_evals.py` printed `Evaluation complete. Results written to eval_results.json` and exited **0** — while `ls eval_results.json` returned "No such file or directory" and `git status --porcelain` was empty. The success message was unconditional text at [`scripts/run_evals.py:12`](https://github.com/ascherj/pathreview/blob/main/scripts/run_evals.py#L12); the body of `main()` was a four-line TODO comment.

That is worse than a no-op, and the second-order effect is the part I would not have predicted: `eval.yml` reads the report inside a `try` whose `catch (e) {}` is **empty**. So the missing file threw, was swallowed, and every PR touching `rag/**` got a green check next to a comment saying "Eval results not found." A passing evaluation and an evaluation that never ran were indistinguishable in CI. The bug was not "the script is unfinished" — it was "CI reports success for a job that does nothing."

**The issue's premise did not match the code.** `grep -rn "EvalSuite" --include="*.py" .` matched only its own definition. It does not run inline during API requests; it does not run *anywhere*. `process_review()` delegates to `_run_ingestion_pipeline`, `_run_agent_orchestration`, `_run_rag_retrieval_generation` and `_run_safety_checks`, all of which return hardcoded literals — there is a fixed `"overall_score": 0.81` sitting in `core/services/review_service.py`. So there was no existing wiring to lift out.

**Three load-bearing defects, none visible from the issue text.** I wrote two throwaway probe scripts that wired the real `ingestion/` and `rag/` components together by hand, and they surfaced:

1. `VectorStore.add_chunks` raised `AttributeError: 'Chunk' object has no attribute 'id'` on every real chunk.
2. `ReviewGenerator.__init__` builds `openai.OpenAI(...)` eagerly, so it raises `OpenAIError: Missing credentials` at *construction* — the generation stage could not be exercised offline at all.
3. `LLM_PROVIDER` was inert. `Settings.llm_provider` was declared and both workflows set it, but **no module read `settings.llm_provider`**, and `get_embedding_provider()` had zero production callers. The switch CI depended on to stay offline did nothing.

The probes also found two silent-degradation behaviours that shaped the runner. `HybridRetriever.retrieve` computes `all_chunks = self._get_all_chunks(collection_name)` and then never uses it — the caller must have called `KeywordSearcher.index(...)` themselves. If they have not, or if the indexed chunk dicts lack an `"id"` key, `retrieve` still succeeds and the BM25 half silently contributes 0.0 to every score. I confirmed this: the un-indexed case and the id-less case returned *identical* results. And on a single-document corpus BM25 returned `-0.824`; since `HybridRetriever` normalises by `keyword_scores_max`, a negative maximum inverts the ranking and the `min_score=0.3` filter can then discard everything.

## Why the missing composition seam changed the solution

Every RAG stage in PathReview exists as a competent, isolated unit — `StrategySelector`, `MockEmbeddingProvider`, `VectorStore`, `KeywordSearcher`, `HybridRetriever`, `ReviewGenerator`, `EvalSuite`. Each was written against an assumed caller that would assemble them. The only two places that assembly was ever meant to happen were `process_review()` and `scripts/run_evals.py`, and **both were stubs**.

That single fact explains everything I found. The seams between the stages had never been exercised, so nothing forced them to agree. `VectorStore.add_chunks` could disagree with the `Chunk` dataclass indefinitely because it had zero callers. `LLM_PROVIDER` could be inert because nothing needed to choose a provider. `HybridRetriever` could depend on the caller having built the keyword index because there was no caller to get it wrong.

So the task stopped being "write a script" and became: **introduce the composition seam, supply the deterministic generation provider the pipeline lacked, repair the one broken seam blocking composition, and make `LLM_PROVIDER=mock` mean something.** `scripts/run_evals.py` ended up 127 lines of argument parsing and printing — the smallest part of the work. The real deliverable is `rag/evaluator/benchmark_runner.py`.

This also told me where to put it. I put the runner under `rag/` rather than `scripts/` because `pyproject.toml`'s `[tool.setuptools.packages.find]` excludes `scripts*` from the installed distribution — library code there would resolve only as a CWD namespace package and would not be reliably importable by tests or by an installed copy.

## Architectural decisions

**Benchmark loading.** Fixtures are JSON files in `tests/fixtures/sample_profiles/` — a path chosen because the original TODO already named it, even though the directory did not exist. Files load in **sorted filename order** so report ordering is stable across machines. Validation **fails loudly and names the file**: a missing directory, an empty directory, malformed JSON, a blank `portfolio_id`, a whitespace-only document, an empty query string, a duplicate `source_id`. Silently skipping a bad fixture would shrink the benchmark set and move the aggregate with no explanation in the report — and the whole point of this work was to stop CI reporting numbers that mean nothing.

I also enforce a **minimum of 4 chunks per portfolio**, directly because of the `-0.824` BM25 measurement. That is a constant with a reason behind it, and the reason is in the code comment.

I deliberately shipped **no golden or expected scores**. Nothing in the repository establishes what a good score is. Inventing thresholds would have created a gate that looked authoritative and was made up.

**Deterministic generation.** This is where I got it wrong first, and the failure was instructive.

`FaithfulnessChecker` scores the fraction of feedback sentences sharing ≥2 non-stopword tokens with the concatenated context. So a mock returning canned text scores ~0.0 on every benchmark, and a mock copying chunks verbatim scores ~1.0 on every benchmark. Both are constants; a constant detects nothing. I knew that going in and wrote it into the plan's risk section.

My first implementation pooled salient terms across *all* retrieved chunks and composed three grounded sentences plus one ungrounded recommendation per section. Then I ran it on the real benchmark set and got faithfulness of **exactly 0.8000 on all four portfolios**. I had walked straight into the failure I had documented. Pooling meant any portfolio with a handful of chunks could always fill three sentences, so the ratio saturated.

The fix was to ground each sentence in **one** chunk rather than in a pooled list. A thin chunk now yields a thin sentence that the checker scores as unsupported. Faithfulness now separates the deliberately sparse portfolio (0.60) from the dense ones (0.80). One further detail that only shows up when you read `FaithfulnessChecker._is_supported`: it compares raw whitespace tokens, so a term carrying attached punctuation — `"python,"` lifted from `"Python, FastAPI"` — would never match the context it came from. I only quote tokens that are already alphanumeric.

I also chose **not** to mirror `ReviewGenerator._add_citations`, which appends a `Sources: ...` line. Those source ids come from chunk *metadata*, not chunk *text*, so the fragment would depress faithfulness for reasons unrelated to review quality.

**Retrieval.** The runner drives the real `VectorStore`, `KeywordSearcher` and `HybridRetriever` — substituting deterministic implementations only at the two model boundaries. It always builds the keyword index and always sets `"id"` on each chunk dict, because the probes showed omitting either silently zeroes the BM25 half. Retrieval is capped at `settings.max_chunks_per_query` so the generator and the scorer see the same context: `ReviewGenerator._format_context` truncates to 10 chunks while `EvalSuite` scores everything it is handed, so an uncapped retrieval would score context the generator never saw.

The vector store is an embedded Chroma client on a `tempfile.TemporaryDirectory()`. That is two guarantees in one: a run cannot inherit a stale collection from a previous run, and it leaves no `.chromadb/` in the working tree.

**Evaluation.** `EvalSuite.run` takes a *single* query, but a "portfolio" implies several. I resolved that by scoring **per query** and aggregating per portfolio, then across the set — rather than changing `EvalSuite`. Only relevance and faithfulness are computed, matching what the code implements; actionability appears exactly once in the codebase, in the comment I deleted.

**Reporting.** `eval_results.json` is inlined *verbatim* into a PR comment by `eval.yml`, so it must stay small and legible — the four-portfolio report is 4,814 bytes. Field names mirror `EvalResult`'s so the report and the dataclass cannot drift. Keys are sorted, scores are rounded before aggregation, and there is **no timestamp, hostname, git SHA or duration** — those change every run and would destroy the byte-level reproducibility the report exists to demonstrate. `retrieval_empty` is carried per query so a retrieval failure is distinguishable from genuinely bad relevance; both otherwise score 0.0.

## Why live APIs and external services were excluded

Not a preference — a constraint read off `eval.yml`. It starts no `services:`, so there is no Postgres, no Redis, no Chroma container. It sets `LLM_PROVIDER: mock`. It runs on Python 3.11 with `pip install -e ".[dev]"` and nothing else.

That also ruled out `IngestionPipeline`, which would have been the obvious thing to reuse: its `_check_skip` calls `self.db_session.query(...)`, so the ingestion orchestrator requires a database session the eval job cannot provide. The runner calls `StrategySelector.chunk(...)` directly and bypasses the pipeline rather than refactoring it.

Beyond CI, determinism is the point. A benchmark whose numbers move because a hosted model felt different today cannot function as a regression signal. `MockEmbeddingProvider` seeds `np.random.RandomState` from a SHA-256 of the text; `RelevanceScorer` and `FaithfulnessChecker` are pure lexical overlap; the mock generator is a pure function of its chunks. Every source of variance is removed on purpose.

## How I handled the `VectorStore.add_chunks` mismatch

This was the one change to existing behaviour, so I was careful about it.

`add_chunks` read `chunk.id`, `chunk.source_id`, `chunk.chunk_index` and `chunk.section` as **attributes**. `Chunk` is a two-field dataclass — `text` and `metadata` — and the chunkers put `source_id`/`chunk_index` inside `metadata`. I verified the shape directly rather than assuming: `Chunk` fields are `dict_keys(['text', 'metadata'])`, and `hasattr(chunk, 'id')` is `False`.

Three things made me comfortable including it:

1. **It is on the critical path.** `HybridRetriever` reads through `VectorStore`. Without the fix, `add_chunks` raises and the retriever has nothing to read. The runner is not implementable without it.
2. **It has zero callers**, so nothing can regress. That is also exactly why the defect survived.
3. **The id format is not invented.** `BatchEmbeddingProcessor._store_embedding` already derives `f"{source_id}_chunk_{chunk_index}"` from `chunk.metadata` — correctly — but writes to a raw Chroma collection instead of through `VectorStore`, so `HybridRetriever` could never see anything it wrote. Adopting that same convention makes the two indexing paths converge instead of diverge.

I kept the diff to 19 lines inside that one method. When the repo's pre-commit hook reformatted the whole file with `black`, I reverted the reformatting — burying a load-bearing three-line fix in an 80-line whitespace diff is how a reviewer misses it. `tests/unit/test_vector_store.py` covers it with real `Chunk` objects shaped the way the chunkers emit them, including the id convention, the metadata fallbacks and the empty-input case.

## Which tests gave me the most confidence

Not the ones with the most assertions.

**`test_repeated_runs_produce_identical_json` and `test_written_report_is_byte_identical_across_runs`.** The issue's core promise is reproducibility. Comparing two full serialised runs byte-for-byte is the only assertion that tests that promise directly, and it would catch a stray timestamp, an unsorted key, or a float tail digit that no schema assertion would.

**`test_run_constructs_no_live_model_client`.** It patches `openai.OpenAI` and asserts it is never called across an entire benchmark run. Since `ReviewGenerator` fails at *construction*, this is the assertion that proves offline operation rather than asserting it in a docstring.

**`test_empty_retrieval_is_flagged_not_silently_zero`.** It drives the runner with `min_score=1.1` so nothing is retrievable, then asserts `retrieved_count == 0` and `retrieval_empty is True` alongside the 0.0 scores. This is the test that encodes the lesson from the original bug: a zero that means "broken" must be distinguishable from a zero that means "bad."

**`test_thin_chunks_lower_faithfulness_than_dense_chunks`.** This is the guard against the mistake I actually made. It fails if the mock ever goes back to producing a constant.

**`test_run_leaves_no_vector_store_residue`.** Cheap, and it catches an entire class of "works on my machine, poisons the next run" problems.

The 40 fixture-validation cases matter too, but individually — the ones above are the ones that would have caught a real regression.

## What was harder than expected, and what failed

**The `LLM_PROVIDER` chain was longer than it looked.** "Honour `LLM_PROVIDER`" sounds like reading one setting. It meant writing a whole generation provider, a factory, and a `Protocol` so both implementations could be held interchangeably without importing `openai` on the mock path.

**Byte-comparing two runs does not prove determinism.** This is the thing I am most glad I caught. I had three byte-identical runs and considered determinism done. Then I actually read `HybridRetriever.retrieve` again and noticed it builds its result list by iterating `set(vector_map.keys()) | set(keyword_map.keys())` — and **Python randomises string hashing per process**. A probe over five `PYTHONHASHSEED` values on a 12-chunk corpus with duplicated text returned the same chunks in five different orders. My benchmark set does not trip it (no exact ties, never reaches the `max_chunks` cap), so my "proof" was luck. I added two guards in the runner — re-sort on `(-score, id)`, and reject a portfolio containing two chunks with identical text, since identical text gives an identical mock embedding *and* an identical BM25 score. I left `hybrid.py` alone: shared production code, out of scope, and worth raising separately.

**Fixture authoring was constrained by the chunkers in a non-obvious way.** `SemanticChunker` targets ~500 tokens, so a realistic one-page resume produces exactly **one** chunk — well under the 4-chunk floor BM25 needs. `StructuralChunker` splits markdown on headings, so a README with five headings produces five chunks. The benchmark documents are shaped the way they are because of that: mostly markdown with several headings, which is what gets each portfolio to 6–10 chunks.

**The repository's own quality gates fail before my code runs.** `make check` exits at its first step with 182 pre-existing ruff errors and never reaches `black` or `mypy`. `make test-unit` has 53 pre-existing failures. `black .` would reformat 52 files. The repo's `.pre-commit-config.yaml` runs `mypy` over staged files and rejects the repository's own untyped test convention — `tests/unit/test_relevance_scorer.py` alone produces 21 `no-untyped-def` errors. I resisted fixing any of it. Instead I captured the exact baseline first, diffed the failure sets before and after, and reported that my change adds **zero** ruff errors, **zero** mypy errors and **zero** test failures. That measurement was worth the time it took: without it, "53 tests fail" would look like something I broke.

**CI has not actually run on the PR.** The workflow runs are `action_required` — GitHub gates first-time fork contributors behind maintainer approval. So I reproduced both jobs locally in a clean Python 3.11.14 virtualenv built the same way `eval.yml` builds one. The eval output was byte-identical to the Python 3.14 output. That is good evidence, but it is not the same as a green check, and I have said so rather than implying CI passed.

## How AI coding tools helped, and where I had to verify them

I used Claude Code throughout. The honest summary is that it was strongest at breadth and weakest at the things that only surface when you run the code.

**Where it clearly helped.** Mapping an unfamiliar codebase quickly — reading a dozen modules and reporting what actually calls what was much faster than doing it by hand, and it is what surfaced "`EvalSuite` has no runtime callers" early. Writing the volume of validation tests. Drafting docstrings in the repo's Google style consistently across new modules.

**Where its output was wrong and running the code caught it.** The first `MockReviewGenerator` design was plausible, well-documented, and produced a **constant** faithfulness score of 0.8 on every portfolio — the exact failure the plan had predicted in writing. No amount of reading the generator would have shown that; running it against the real benchmark set did, immediately.

**Where its confidence was misplaced.** Three byte-identical runs were treated as proof of determinism. They were not — `HybridRetriever` iterates a set, and hash randomisation makes that order process-dependent. Finding that required going back and re-reading the retriever, then writing a deliberately adversarial probe with duplicated text and five hash seeds. The lesson generalises: an AI tool will confirm the property you asked it to check, not the property you actually care about.

**Where small assertions were simply wrong.** A residue test asserted `tmp_path` was empty when the fixtures directory lived there. A sorted-keys test asserted a specific line index rather than checking the keys. Both failed on first run and were trivially fixed — but they are a reminder that a test suite that has never been run is a draft, not a verification.

My working rule by the end: use the tool to read broadly and to generate volume, then verify every behavioural claim by executing it, and treat any statement about determinism, ordering or "this cannot happen" as unverified until there is a probe that tries to break it.

## Feedback received

**None yet.** The draft PR was opened and then marked ready for review; at the time of writing there are **no review comments, no submitted reviews, and no maintainer comments** on [PR #658](https://github.com/ascherj/pathreview/pull/658), and no new comments on issue #40 beyond the several students who claimed it. I have not adopted or rejected any feedback, because none exists. I would rather record that plainly than manufacture a review cycle.

In its place I ran a structured self-review against runner determinism, benchmark validation, report schema, temporary vector-store cleanup, mock provider isolation, error handling, CI compatibility, test coverage and documentation accuracy. It produced two real defects, both fixed and both with tests: the hash-randomisation ordering issue described above, and a CLI error-handling gap where an unrecognised `LLM_PROVIDER` surfaced as a raw traceback from inside the provider factory instead of an actionable message and exit 1.

The PR raises five open decisions explicitly rather than deciding them silently — whether actionability is in scope, whether the runner should ever exit non-zero on low scores, whether `eval_results.json` should be committed or ignored, whether the benchmark and report schemas are acceptable, and whether `get_review_generator("openai")` should take its model from a new setting rather than a module constant. Those are the maintainer's calls, not mine.

## Known limitations

**Mock embeddings carry no semantic signal, and this is the honest ceiling on what the report measures.** `MockEmbeddingProvider` seeds a RNG from a SHA-256 of the text, so vectors for related texts are near-orthogonal. Measured cosine similarity against the query `"Python FastAPI REST APIs"`: the paraphrase *"Built REST APIs using Python and FastAPI"* scored **+0.054**; a second paraphrase **+0.022**; unrelated React/TypeScript text **+0.000**. Under `LLM_PROVIDER=mock`, vector ranking is effectively random and BM25 carries all the real retrieval signal — while `HybridRetriever` weights vector at 0.7 and keyword at 0.3.

So this report is a **regression-and-determinism signal, not a semantic-quality measurement**. I put that in the PR in those words. A number labelled "review quality" that is mostly noise is worse than no number, because someone will eventually treat it as authoritative. The same runner with `LLM_PROVIDER=openai` produces genuinely semantic scores — at the cost of determinism and offline operation, which is the whole reason CI uses mock.

**Related: absolute relevance values are low (0.04–0.27) and must not be read as percentages of goodness.** `RelevanceScorer` averages query-token overlap across *every* retrieved chunk, and with near-random vector ranking the retriever returns most of the corpus, so the average is diluted by construction. The values are useful *relatively* — the deliberately off-domain query on the frontend portfolio scores 0.0, the sparse portfolio scores lowest overall — and comparably across runs, which is what a regression signal needs.

**Faithfulness is scored over at most the first 10 sentences** of the concatenated feedback, because `FaithfulnessChecker._extract_claims` truncates to 10 claims. With five sections, later sections do not influence the score.

**The runner does not exercise the parsers, the agent layer or the safety layer** — only chunking → embedding → retrieval → generation → scoring. Whether "the full RAG pipeline" was meant to include those is one of the open questions in the PR.

**`HybridRetriever`'s set-iteration ordering is worked around, not fixed.** My guards make *the benchmark* reproducible. The underlying behaviour still affects any other caller, including the request path whenever it gets wired up.

## What I would design differently

**I would run the pipeline end-to-end on day one, before writing the plan.** I wrote a careful plan and then discovered the seams by probing. The probes were the highest-value hour of the whole issue — `AttributeError: 'Chunk' object has no attribute 'id'` reframed the entire task. Doing that first would have made the plan better, not just earlier.

**I would treat "is this metric a constant?" as a first-class test before shipping the mock**, not as something noticed by eyeballing a results table. The saturation was predictable from reading `FaithfulnessChecker` — I predicted it in writing and then built it anyway. A test asserting the metric varies across two synthetic corpora would have failed immediately.

**I would write the adversarial determinism probe before claiming determinism**, rather than after three clean runs. "Same output twice" and "no source of variance" are different claims, and I conflated them.

**I would give the report a `notes` field** carrying the mock-embedding caveat *inside* `eval_results.json`. Right now that limitation lives in the PR description; since `eval.yml` pastes the raw JSON into a PR comment, someone reading a comment six months from now sees the numbers with none of the caveats. The report should carry its own health warning.

**I would reconsider making the report's `overall_score` prominent at all.** It is `(relevance + faithfulness) / 2`, where one term is diluted by design and the other is a property of the mock generator. Reporting the two components without averaging them into a single headline number would be more honest, though it would mean diverging from `EvalResult`'s shape.

## What this demonstrates about working in an unfamiliar codebase

Mostly: **trust the code over the description of the code, and check before you build.**

The issue's first sentence was factually wrong about the repository, and a large fraction of the value I added came from establishing that carefully — with `grep` output and a stack trace — rather than either quietly ignoring the issue text or implementing a refactor of wiring that did not exist. Reconciling the two, in the reproduction document and again in the PR, is what made the scope defensible.

It also demonstrates knowing what *not* to touch. `core/services/review_service.py` is stubbed and visibly wrong, and the discrepancy actively invited "while I'm here, fix `process_review` too." It is untouched. So are the API layer, `ingestion/pipeline.py`, the Docker config, and 182 pre-existing lint errors. The one change I made outside my own new files is 19 lines, in a method with zero callers, on the critical path, aligned to a convention already in the codebase — and the PR argues for it explicitly rather than sneaking it in.

And it demonstrates measuring before changing. Capturing the exact `make check` / `make test-unit` baseline before writing any code turned "53 tests fail" from an accusation into a documented pre-existing condition with a diffable failure set.

## How I would explain this in an interview

> PathReview had a RAG pipeline where every stage worked and nothing was connected. The eval runner was a stub that printed "results written" and exited 0 without writing a file — and because the CI job swallowed the resulting read error in an empty `catch`, every PR got a green check next to "Eval results not found." A passing evaluation looked exactly like an evaluation that never ran.
>
> The issue asked me to move inline evaluation into a standalone runner. When I reproduced it, that turned out to describe a refactor of wiring that had never existed: the eval suite had zero runtime callers, and the request path returned hardcoded scores. There was no composition seam for the pipeline anywhere in the codebase.
>
> That explained the defects I found by wiring the stages together by hand. The vector store's indexing method read chunk identity as attributes, but chunks are a two-field dataclass with that data in a metadata dict — so it raised `AttributeError` on every real chunk. It had zero callers, which is exactly why nobody had noticed. Generation built its OpenAI client in the constructor, so it couldn't run offline at all. And `LLM_PROVIDER=mock`, which both CI workflows set to stay offline, was read by no module in the codebase.
>
> So I built the missing seam — a runner that drives the real chunker, vector store, BM25 index, hybrid retriever and scorer, substituting deterministic implementations only at the two model boundaries — plus the offline generator that didn't exist, a provider factory that finally reads `LLM_PROVIDER`, four benchmark portfolios, and a JSON report. Ninety tests. It runs with no database, no Redis, no Docker and no network.
>
> Two things I'd want to be judged on. First, I caught a determinism bug that byte-comparing runs had missed: the hybrid retriever assembles results by iterating a Python set, and string hashing is randomised per process, so equally-scored chunks come back in different orders. Three identical runs had been luck. I proved it with a probe across five hash seeds and fixed it in my code without touching shared production code.
>
> Second, I documented what the numbers *don't* mean. The mock embeddings are SHA-256-seeded, so a paraphrase of the query scores 0.054 cosine similarity against 0.000 for unrelated text — vector ranking is essentially random and BM25 carries all the signal. So I said in the PR that this is a regression-and-determinism signal, not a measurement of review quality. A number labelled "quality" that's mostly noise is worse than no number, because someone will eventually trust it.
