"""Offline benchmark runner for the retrieval, generation and scoring pipeline.

This module is the composition seam the RAG stages were written against but
never got: it drives chunking, embedding, indexing, hybrid retrieval, review
generation and scoring over a curated set of benchmark portfolios and returns a
serialisable report.

Everything here runs offline. Embeddings and generation are resolved through
``LLM_PROVIDER``, which selects deterministic mock implementations by default;
the vector store is an embedded ChromaDB client pointed at a temporary directory
that is deleted when the run finishes; keyword search is in-memory BM25. No
database, Redis, Chroma container or network call is involved, which is what lets
the GitHub Actions eval job run it with no ``services:`` block.

``IngestionPipeline`` is deliberately bypassed rather than reused: its
``_check_skip`` requires a database session, which the eval job has no way to
provide.
"""

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from core.config import settings
from ingestion.chunking.base import Chunk
from ingestion.chunking.strategy_selector import StrategySelector
from ingestion.embeddings.provider import get_embedding_provider
from rag.evaluator.eval_suite import EvalSuite
from rag.generator.provider import get_review_generator
from rag.retriever.hybrid import HybridRetriever
from rag.retriever.keyword_search import KeywordSearcher
from rag.retriever.vector_store import VectorStore

logger = structlog.get_logger()

# Bumped whenever the shape of eval_results.json changes, so consumers can tell
# an old report from a new one.
SCHEMA_VERSION = 1

GENERATED_BY = "scripts/run_evals.py"

DEFAULT_FIXTURES_DIR = Path("tests/fixtures/sample_profiles")
DEFAULT_OUTPUT_PATH = Path("eval_results.json")

# BM25 returns negative scores on a corpus of one or two documents, and
# HybridRetriever normalises by the maximum keyword score — a negative maximum
# inverts the ranking. Requiring a floor on corpus size keeps that out of the
# benchmark set.
MIN_CHUNKS_PER_PORTFOLIO = 4

# Scores are rounded before they are aggregated or serialised so that two runs
# produce byte-identical JSON regardless of floating point tail digits.
SCORE_PRECISION = 4


class BenchmarkFixtureError(ValueError):
    """Raised when a benchmark fixture is missing, malformed or unusable."""


@dataclass(frozen=True)
class BenchmarkDocument:
    """One source document belonging to a benchmark portfolio."""

    source_id: str
    source_type: str
    text: str


@dataclass(frozen=True)
class BenchmarkPortfolio:
    """One curated benchmark portfolio and the queries it should be scored on."""

    portfolio_id: str
    description: str
    profile: dict
    documents: list[BenchmarkDocument]
    queries: list[str]


@dataclass(frozen=True)
class QueryResult:
    """Scores for a single query against a single portfolio."""

    query: str
    retrieved_count: int
    generated_sections: int
    retrieval_empty: bool
    relevance_score: float
    faithfulness_score: float
    overall_score: float

    def to_dict(self) -> dict:
        """Serialise to the report's per-query shape.

        Returns:
            Report entry for this query
        """
        return {
            "query": self.query,
            "retrieved_count": self.retrieved_count,
            "generated_sections": self.generated_sections,
            "retrieval_empty": self.retrieval_empty,
            "relevance_score": self.relevance_score,
            "faithfulness_score": self.faithfulness_score,
            "overall_score": self.overall_score,
        }


@dataclass(frozen=True)
class PortfolioResult:
    """Aggregated scores across every query for one portfolio."""

    portfolio_id: str
    description: str
    chunk_count: int
    queries: list[QueryResult]
    relevance_score: float
    faithfulness_score: float
    overall_score: float

    def to_dict(self) -> dict:
        """Serialise to the report's per-portfolio shape.

        Returns:
            Report entry for this portfolio
        """
        return {
            "portfolio_id": self.portfolio_id,
            "description": self.description,
            "chunk_count": self.chunk_count,
            "query_count": len(self.queries),
            "queries": [query.to_dict() for query in self.queries],
            "relevance_score": self.relevance_score,
            "faithfulness_score": self.faithfulness_score,
            "overall_score": self.overall_score,
        }


@dataclass(frozen=True)
class BenchmarkReport:
    """The full benchmark report written to eval_results.json."""

    llm_provider: str
    portfolios: list[PortfolioResult]
    relevance_score: float
    faithfulness_score: float
    overall_score: float
    schema_version: int = SCHEMA_VERSION
    generated_by: str = GENERATED_BY

    @property
    def query_count(self) -> int:
        """Total number of scored queries across every portfolio."""
        return sum(len(portfolio.queries) for portfolio in self.portfolios)

    def to_dict(self) -> dict:
        """Serialise the whole report.

        No timestamp, host, path or duration is included: those change on every
        run and would destroy the byte-level reproducibility the report exists to
        demonstrate.

        Returns:
            JSON-serialisable report
        """
        return {
            "schema_version": self.schema_version,
            "generated_by": self.generated_by,
            "llm_provider": self.llm_provider,
            "portfolio_count": len(self.portfolios),
            "query_count": self.query_count,
            "aggregate": {
                "relevance_score": self.relevance_score,
                "faithfulness_score": self.faithfulness_score,
                "overall_score": self.overall_score,
            },
            "portfolios": [portfolio.to_dict() for portfolio in self.portfolios],
        }


def _round(value: float) -> float:
    """Round a score to the report's fixed precision.

    Args:
        value: Raw score

    Returns:
        Score rounded to SCORE_PRECISION decimal places
    """
    return round(float(value), SCORE_PRECISION)


def _mean(values: list[float]) -> float:
    """Average a list of scores, treating an empty list as zero.

    Args:
        values: Scores to average

    Returns:
        Rounded mean, or 0.0 when there is nothing to average
    """
    if not values:
        return 0.0
    return _round(sum(values) / len(values))


def _require_non_empty_string(value: object, field_name: str, source: str) -> str:
    """Validate that a fixture field is a non-empty string.

    Args:
        value: Raw value from the fixture
        field_name: Field name, used in the error message
        source: Fixture file path, used in the error message

    Returns:
        The validated string

    Raises:
        BenchmarkFixtureError: If the value is missing, not a string, or blank
    """
    if not isinstance(value, str) or not value.strip():
        raise BenchmarkFixtureError(f"{source}: '{field_name}' must be a non-empty string")
    return value


def parse_portfolio(data: object, source: str) -> BenchmarkPortfolio:
    """Validate one decoded fixture and turn it into a BenchmarkPortfolio.

    Validation fails loudly rather than skipping a bad fixture: silently dropping
    one would shrink the benchmark set and move the aggregate with no explanation
    in the report.

    Args:
        data: Decoded JSON from a fixture file
        source: Fixture file path, used in error messages

    Returns:
        Validated BenchmarkPortfolio

    Raises:
        BenchmarkFixtureError: If any required field is missing or malformed
    """
    if not isinstance(data, dict):
        raise BenchmarkFixtureError(f"{source}: fixture must be a JSON object")

    portfolio_id = _require_non_empty_string(data.get("portfolio_id"), "portfolio_id", source)
    description = _require_non_empty_string(data.get("description"), "description", source)

    profile = data.get("profile", {})
    if not isinstance(profile, dict):
        raise BenchmarkFixtureError(f"{source}: 'profile' must be an object")

    raw_queries = data.get("queries")
    if not isinstance(raw_queries, list) or not raw_queries:
        raise BenchmarkFixtureError(f"{source}: 'queries' must be a non-empty list")

    queries = [
        _require_non_empty_string(query, f"queries[{index}]", source)
        for index, query in enumerate(raw_queries)
    ]

    return BenchmarkPortfolio(
        portfolio_id=portfolio_id,
        description=description,
        profile=profile,
        documents=_parse_documents(data.get("documents"), source),
        queries=queries,
    )


def _parse_documents(raw_documents: object, source: str) -> list[BenchmarkDocument]:
    """Validate a fixture's documents list.

    Args:
        raw_documents: The fixture's 'documents' value
        source: Fixture file path, used in error messages

    Returns:
        Validated documents in fixture order

    Raises:
        BenchmarkFixtureError: If the list is missing, empty, contains a
            malformed entry, or repeats a source_id
    """
    if not isinstance(raw_documents, list) or not raw_documents:
        raise BenchmarkFixtureError(f"{source}: 'documents' must be a non-empty list")

    documents = []
    seen_source_ids = set()

    for index, raw_document in enumerate(raw_documents):
        if not isinstance(raw_document, dict):
            raise BenchmarkFixtureError(f"{source}: documents[{index}] must be an object")

        location = f"documents[{index}]"
        source_id = _require_non_empty_string(
            raw_document.get("source_id"), f"{location}.source_id", source
        )
        source_type = _require_non_empty_string(
            raw_document.get("source_type"), f"{location}.source_type", source
        )
        text = _require_non_empty_string(raw_document.get("text"), f"{location}.text", source)

        if source_id in seen_source_ids:
            raise BenchmarkFixtureError(f"{source}: duplicate source_id '{source_id}'")
        seen_source_ids.add(source_id)

        documents.append(BenchmarkDocument(source_id=source_id, source_type=source_type, text=text))

    return documents


def load_benchmark_portfolios(
    fixtures_dir: Path = DEFAULT_FIXTURES_DIR,
) -> list[BenchmarkPortfolio]:
    """Load every benchmark portfolio from a fixtures directory.

    Files are read in sorted filename order so the report's portfolio ordering is
    stable across machines and filesystems.

    Args:
        fixtures_dir: Directory holding one JSON fixture per portfolio

    Returns:
        Validated portfolios, ordered by filename

    Raises:
        BenchmarkFixtureError: If the directory is missing or empty, a file is not
            valid JSON, a fixture is malformed, or two fixtures share an id
    """
    directory = Path(fixtures_dir)
    if not directory.is_dir():
        raise BenchmarkFixtureError(f"Benchmark fixtures directory not found: {directory}")

    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise BenchmarkFixtureError(f"No benchmark fixtures (*.json) found in {directory}")

    portfolios = []
    seen_ids = set()
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise BenchmarkFixtureError(f"{path}: invalid JSON ({exc})") from exc

        portfolio = parse_portfolio(data, str(path))
        if portfolio.portfolio_id in seen_ids:
            raise BenchmarkFixtureError(
                f"{path}: duplicate portfolio_id '{portfolio.portfolio_id}'"
            )
        seen_ids.add(portfolio.portfolio_id)
        portfolios.append(portfolio)

    logger.info("benchmark_fixtures_loaded", count=len(portfolios), directory=str(directory))
    return portfolios


@dataclass
class _IndexedPortfolio:
    """Chunks and embeddings prepared for one portfolio."""

    chunks: list[Chunk] = field(default_factory=list)
    embeddings: list[list[float]] = field(default_factory=list)
    chunk_dicts: list[dict] = field(default_factory=list)


class BenchmarkRunner:
    """Run benchmark portfolios through the real RAG pipeline, offline.

    The runner uses the production chunker, vector store, keyword searcher,
    hybrid retriever and eval suite, substituting deterministic providers only at
    the two model boundaries — embeddings and generation. That keeps the report a
    genuine signal about the retrieval and scoring code while removing every
    source of run-to-run variation.
    """

    def __init__(
        self,
        provider_name: str | None = None,
        max_chunks: int | None = None,
        min_score: float | None = None,
    ):
        """Initialise the runner.

        Args:
            provider_name: LLM provider name; defaults to settings.llm_provider
            max_chunks: Maximum chunks per query; defaults to
                settings.max_chunks_per_query
            min_score: Minimum blended retrieval score; defaults to
                settings.min_relevance_score
        """
        self.provider_name = provider_name or settings.llm_provider
        self.max_chunks = max_chunks if max_chunks is not None else settings.max_chunks_per_query
        self.min_score = min_score if min_score is not None else settings.min_relevance_score

        self.chunker = StrategySelector()
        self.embedding_provider = get_embedding_provider(self.provider_name)
        self.generator = get_review_generator(self.provider_name)
        self.eval_suite = EvalSuite()

    def run(self, portfolios: list[BenchmarkPortfolio]) -> BenchmarkReport:
        """Run every portfolio and aggregate the results.

        The vector store is created inside a temporary directory that is removed
        when the run finishes, so a run leaves no ``.chromadb/`` residue in the
        working tree and cannot inherit a stale collection from a previous run.

        Args:
            portfolios: Validated benchmark portfolios

        Returns:
            The aggregated BenchmarkReport

        Raises:
            BenchmarkFixtureError: If no portfolios were supplied
        """
        if not portfolios:
            raise BenchmarkFixtureError("No benchmark portfolios to run")

        with tempfile.TemporaryDirectory(prefix="pathreview-eval-") as persist_dir:
            vector_store = VectorStore(persist_dir=persist_dir)
            results = [self.run_portfolio(portfolio, vector_store) for portfolio in portfolios]

        report = BenchmarkReport(
            llm_provider=self.provider_name,
            portfolios=results,
            relevance_score=_mean([r.relevance_score for r in results]),
            faithfulness_score=_mean([r.faithfulness_score for r in results]),
            overall_score=_mean([r.overall_score for r in results]),
        )

        logger.info(
            "benchmark_run_complete",
            portfolio_count=len(results),
            query_count=report.query_count,
            overall_score=report.overall_score,
        )
        return report

    def run_portfolio(
        self,
        portfolio: BenchmarkPortfolio,
        vector_store: VectorStore,
    ) -> PortfolioResult:
        """Index one portfolio and score every one of its queries.

        Args:
            portfolio: The portfolio to run
            vector_store: Vector store to index into

        Returns:
            PortfolioResult with per-query and aggregated scores

        Raises:
            BenchmarkFixtureError: If the portfolio produces too few or
                non-unique chunks
        """
        indexed = self._index(portfolio, vector_store)

        keyword_searcher = KeywordSearcher()
        keyword_searcher.index(indexed.chunk_dicts)
        retriever = HybridRetriever(vector_store, keyword_searcher)

        query_results = [
            self._score_query(portfolio, query, retriever) for query in portfolio.queries
        ]

        return PortfolioResult(
            portfolio_id=portfolio.portfolio_id,
            description=portfolio.description,
            chunk_count=len(indexed.chunks),
            queries=query_results,
            relevance_score=_mean([q.relevance_score for q in query_results]),
            faithfulness_score=_mean([q.faithfulness_score for q in query_results]),
            overall_score=_mean([q.overall_score for q in query_results]),
        )

    def _index(
        self,
        portfolio: BenchmarkPortfolio,
        vector_store: VectorStore,
    ) -> _IndexedPortfolio:
        """Chunk, embed and index one portfolio's documents.

        Both retrieval halves are populated from the same chunk list, and each
        keyword chunk dict carries the vector store's id. HybridRetriever joins
        the two halves on that id and silently drops keyword hits without one, so
        omitting it would zero the BM25 contribution with no error raised.

        Args:
            portfolio: The portfolio to index
            vector_store: Vector store to index into

        Returns:
            The chunks, embeddings and chunk dicts for this portfolio

        Raises:
            BenchmarkFixtureError: If a document produces no chunks, the
                portfolio is below MIN_CHUNKS_PER_PORTFOLIO, or two chunks
                collide on the same id or on identical text
        """
        indexed = _IndexedPortfolio()

        for document in portfolio.documents:
            chunks = self.chunker.chunk(
                document.text,
                {"source_id": document.source_id, "source_type": document.source_type},
            )
            if not chunks:
                raise BenchmarkFixtureError(
                    f"Portfolio '{portfolio.portfolio_id}': document "
                    f"'{document.source_id}' produced no chunks"
                )
            indexed.chunks.extend(chunks)

        if len(indexed.chunks) < MIN_CHUNKS_PER_PORTFOLIO:
            raise BenchmarkFixtureError(
                f"Portfolio '{portfolio.portfolio_id}' produced {len(indexed.chunks)} chunks; "
                f"at least {MIN_CHUNKS_PER_PORTFOLIO} are required for stable BM25 scoring"
            )

        indexed.embeddings = self.embedding_provider.embed([c.text for c in indexed.chunks])
        indexed.chunk_dicts = self._keyword_documents(portfolio, indexed.chunks)

        vector_store.add_chunks(
            list(zip(indexed.chunks, indexed.embeddings, strict=True)),
            f"profile_{portfolio.portfolio_id}",
        )
        return indexed

    @classmethod
    def _keyword_documents(
        cls,
        portfolio: BenchmarkPortfolio,
        chunks: list[Chunk],
    ) -> list[dict]:
        """Build the BM25 documents, rejecting chunks that cannot be told apart.

        Each document carries the same id VectorStore.add_chunks derives, because
        HybridRetriever joins its two halves on that id.

        Args:
            portfolio: The portfolio being indexed, named in error messages
            chunks: The portfolio's chunks

        Returns:
            Chunk dicts ready for KeywordSearcher.index

        Raises:
            BenchmarkFixtureError: If two chunks share an id or share their text
        """
        documents = []
        seen_ids: set[str] = set()
        seen_texts: dict[str, str] = {}

        for chunk in chunks:
            chunk_id = cls._chunk_id(chunk)

            if chunk_id in seen_ids:
                raise BenchmarkFixtureError(
                    f"Portfolio '{portfolio.portfolio_id}': duplicate chunk id '{chunk_id}'; "
                    "upserting it would silently overwrite an earlier chunk"
                )
            seen_ids.add(chunk_id)

            # Identical text yields an identical mock embedding and an identical
            # BM25 score, so the two chunks tie exactly. HybridRetriever resolves
            # its blended results by iterating a set of ids, whose order is not
            # stable across processes, so a tie spanning the max_chunks boundary
            # would make which chunk survives depend on PYTHONHASHSEED.
            if chunk.text in seen_texts:
                raise BenchmarkFixtureError(
                    f"Portfolio '{portfolio.portfolio_id}': chunks '{seen_texts[chunk.text]}' "
                    f"and '{chunk_id}' have identical text, which produces an exact "
                    "retrieval score tie and makes the benchmark non-reproducible"
                )
            seen_texts[chunk.text] = chunk_id

            documents.append({"id": chunk_id, "text": chunk.text, "metadata": dict(chunk.metadata)})

        return documents

    def _score_query(
        self,
        portfolio: BenchmarkPortfolio,
        query: str,
        retriever: HybridRetriever,
    ) -> QueryResult:
        """Retrieve, generate and score a single query.

        Retrieval is capped at ``max_chunks`` so that the generator and the
        scorer see the same context: ReviewGenerator truncates its context to ten
        chunks while EvalSuite scores every chunk it is handed, and an uncapped
        retrieval would score context the generator never saw.

        Retrieved chunks are re-sorted on ``(-score, id)`` before use.
        HybridRetriever builds its result list by iterating a set of chunk ids,
        whose order is not stable across processes, so equally scored chunks can
        come back in a different order from one run to the next.

        Args:
            portfolio: The portfolio being scored
            query: The eval query
            retriever: Retriever bound to this portfolio's indexes

        Returns:
            QueryResult for this query
        """
        query_embedding = self.embedding_provider.embed([query])[0]
        chunks = retriever.retrieve(
            query,
            portfolio.portfolio_id,
            query_embedding,
            max_chunks=self.max_chunks,
            min_score=self.min_score,
        )
        chunks = sorted(
            chunks,
            key=lambda chunk: (-float(chunk.get("score", 0.0) or 0.0), str(chunk.get("id", ""))),
        )

        sections = self.generator.generate_full_review(portfolio.profile, chunks)
        feedback = "\n\n".join(section.content for section in sections if section.content)

        result = self.eval_suite.run(query, chunks, feedback)

        if not chunks:
            logger.warning(
                "benchmark_query_retrieved_nothing",
                portfolio_id=portfolio.portfolio_id,
                query=query,
            )

        return QueryResult(
            query=query,
            retrieved_count=len(chunks),
            generated_sections=len(sections),
            retrieval_empty=not chunks,
            relevance_score=_round(result.relevance_score),
            faithfulness_score=_round(result.faithfulness_score),
            overall_score=_round(result.overall_score),
        )

    @staticmethod
    def _chunk_id(chunk: Chunk) -> str:
        """Derive a chunk's vector store id.

        Mirrors VectorStore.add_chunks so the keyword index and the vector index
        agree on identity.

        Args:
            chunk: The chunk to identify

        Returns:
            The chunk's id
        """
        metadata = chunk.metadata or {}
        return f"{metadata.get('source_id', 'unknown')}_chunk_{metadata.get('chunk_index', 0)}"


def run_benchmarks(
    fixtures_dir: Path = DEFAULT_FIXTURES_DIR,
    provider_name: str | None = None,
) -> BenchmarkReport:
    """Load the benchmark set and run it end to end.

    Args:
        fixtures_dir: Directory holding the benchmark fixtures
        provider_name: LLM provider name; defaults to settings.llm_provider

    Returns:
        The aggregated BenchmarkReport

    Raises:
        BenchmarkFixtureError: If the benchmark set cannot be loaded or run
    """
    portfolios = load_benchmark_portfolios(fixtures_dir)
    return BenchmarkRunner(provider_name=provider_name).run(portfolios)


def write_report(report: BenchmarkReport, output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    """Write a report to disk as sorted, indented JSON.

    Keys are sorted and floats are pre-rounded so that two runs over the same
    fixtures produce byte-identical files.

    Args:
        report: The report to write
        output_path: Destination path; parent directories are created if needed

    Returns:
        The path that was written

    Raises:
        OSError: If the destination cannot be created or written
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(report.to_dict(), indent=2, sort_keys=True)
    path.write_text(payload + "\n", encoding="utf-8")

    logger.info("benchmark_report_written", path=str(path), bytes=len(payload))
    return path
