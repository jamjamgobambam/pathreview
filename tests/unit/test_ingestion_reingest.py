"""Regression tests for stale embeddings after README re-ingestion.

When a README is edited and re-ingested for the same (profile_id, repo_name),
the ingestion pipeline must NOT leave the previous version's chunks behind in
the vector store. Today it does: the chunk IDs embed a hash of the content
(see ingestion/pipeline.py -> _hash_content, and
ingestion/embeddings/batch_processor.py -> _store_embedding), so an edited
README produces brand-new IDs that are *added alongside* the old ones instead
of replacing them. The retriever can then surface stale chunks.

These tests fail on the buggy code and should pass once re-ingestion becomes
idempotent (delete/overwrite a document's existing chunks before writing new
ones, keyed on the document's stable identity rather than its content hash).
Once the fix lands they stay in the suite as regression guards, so the stale-
embedding behavior cannot silently return.
"""

from unittest.mock import Mock

import pytest

from ingestion.embeddings.provider import EmbeddingProvider
from ingestion.pipeline import IngestionPipeline


def _where_matches(metadata: dict, where: dict | None) -> bool:
    """Mimic ChromaDB's `where` metadata filter (supports plain and $eq forms)."""
    if not where:
        return True
    for key, cond in where.items():
        if isinstance(cond, dict) and "$eq" in cond:
            if metadata.get(key) != cond["$eq"]:
                return False
        elif metadata.get(key) != cond:
            return False
    return True


class FakeChromaCollection:
    """In-memory stand-in for a ChromaDB collection.

    Implements just enough of the API (`add`, `get`, `delete`, `count`) for the
    pipeline — and for a correct fix — to run without a real vector store, while
    letting the test observe exactly which chunks are stored.
    """

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}  # id -> {document, metadata, embedding}

    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
        documents: list[str],
    ) -> None:
        for i, chunk_id in enumerate(ids):
            self._store[chunk_id] = {
                "document": documents[i],
                "metadata": metadatas[i],
                "embedding": embeddings[i],
            }

    def get(self, where: dict | None = None, ids: list[str] | None = None) -> dict:
        result_ids, docs, metas = [], [], []
        for chunk_id, rec in self._store.items():
            if ids is not None and chunk_id not in ids:
                continue
            if _where_matches(rec["metadata"], where):
                result_ids.append(chunk_id)
                docs.append(rec["document"])
                metas.append(rec["metadata"])
        return {"ids": result_ids, "documents": docs, "metadatas": metas}

    def delete(self, ids: list[str] | None = None, where: dict | None = None) -> None:
        to_delete = [
            chunk_id
            for chunk_id, rec in self._store.items()
            if (ids is not None and chunk_id in ids)
            or (ids is None and where is not None and _where_matches(rec["metadata"], where))
        ]
        for chunk_id in to_delete:
            del self._store[chunk_id]

    def count(self) -> int:
        return len(self._store)

    # --- test helper ---
    def all_documents(self) -> list[str]:
        return [rec["document"] for rec in self._store.values()]


class FakeEmbeddingProvider(EmbeddingProvider):
    """Deterministic embeddings so no network/model is needed."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(t))] * 8 for t in texts]


@pytest.mark.unit
class TestReadmeReingestionIdempotency:
    """Re-ingesting an edited README must not leave stale chunks behind."""

    @pytest.fixture
    def collection(self) -> FakeChromaCollection:
        return FakeChromaCollection()

    @pytest.fixture
    def pipeline(self, collection: FakeChromaCollection) -> IngestionPipeline:
        # db_session is only used by _check_skip / _record_ingested_source, both of
        # which swallow errors. Force _check_skip's lookup to return "not found" so
        # ingestion actually proceeds on every call.
        db_session = Mock()
        db_session.query.return_value.filter_by.return_value.first.return_value = None
        return IngestionPipeline(
            vector_db=collection,
            db_session=db_session,
            embedding_provider=FakeEmbeddingProvider(),
        )

    def test_edited_readme_replaces_old_chunks(
        self, pipeline: IngestionPipeline, collection: FakeChromaCollection
    ) -> None:
        """Editing and re-ingesting a repo's README should replace its chunks,
        not accumulate them: the old version must not remain retrievable."""
        readme_v1 = "# MyRepo\n\nThis project is built with Flask.\n"
        readme_v2 = "# MyRepo\n\nThis project is built with FastAPI.\n"

        # First ingest — establishes the baseline; the v1 content must be present.
        pipeline.ingest_readme(profile_id="P", repo_name="myrepo", content=readme_v1)
        assert any(
            "Flask" in doc for doc in collection.all_documents()
        ), "sanity check failed: v1 README was not ingested"

        # Author edits the README and re-ingests the SAME repo.
        pipeline.ingest_readme(profile_id="P", repo_name="myrepo", content=readme_v2)

        docs = collection.all_documents()

        # The new version must be retrievable...
        assert any("FastAPI" in doc for doc in docs), "re-ingested (v2) content missing"

        # ...and the OLD version must be gone. This is the bug: today the stale
        # "Flask" chunk survives because the edited README hashes to a new ID that
        # is added alongside the old one instead of replacing it.
        assert not any("Flask" in doc for doc in docs), (
            "stale embedding: the previous README version's chunk survived "
            "re-ingestion; retrieval can now return outdated content"
        )
