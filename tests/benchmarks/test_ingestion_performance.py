import time
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ingestion.pipeline import IngestionPipeline


@pytest.mark.benchmark
def test_ingestion_performance(benchmark, large_portfolio):
    """Benchmark: ingest a portfolio of 5 repos + 1 resume and assert mean <= 30s.

    This test uses lightweight parser/strategy mocks and a mocked batch
    processor so it can run quickly in CI while still measuring orchestration
    overhead. It records the run with `pytest-benchmark` and asserts the
    measured mean across a few runs is below the 30s threshold.
    """

    vector_db = Mock()
    db_session = Mock()
    embedding_provider = Mock()

    pipeline = IngestionPipeline(vector_db, db_session, embedding_provider)

    # Replace heavy components with fast, deterministic mocks
    pipeline.batch_processor.process = Mock(return_value=None)
    pipeline.repo_analyzer.parse = lambda repo: SimpleNamespace(text=repo.get("description", ""), metadata={})
    pipeline.readme_parser.parse = lambda content: SimpleNamespace(text=(content.decode() if isinstance(content, bytes) else content), metadata={})
    pipeline.resume_parser.parse = lambda content: SimpleNamespace(text=(content.decode() if isinstance(content, bytes) else content), metadata={})
    pipeline.strategy_selector.chunk = lambda text, metadata: [{"text": text, "metadata": metadata}]

    repos, resume_content = large_portfolio
    repo_template = {"description": "Sample repo content\n" * 100, "name": "repo"}

    def run():
        for repo in repos:
            pipeline.ingest_repo_metadata("profile1", repo)
        pipeline.ingest_resume("profile1", resume_content, "resume.pdf")

    # Record the benchmark for historical tracking
    benchmark(run)

    # Run a few measured iterations and assert mean runtime is below threshold
    runs = 3
    durations = []
    for _ in range(runs):
        t0 = time.perf_counter()
        run()
        durations.append(time.perf_counter() - t0)

    mean = sum(durations) / len(durations)
    assert mean <= 30.0, f"Mean ingestion time {mean:.2f}s exceeds 30s"
