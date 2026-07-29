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


def _chunks_for_source(collection: FakeChromaCollection, source_id: str) -> list[dict]:
    """Return the stored records whose metadata belongs to ``source_id``."""
    return [
        rec for rec in collection._store.values() if rec["metadata"].get("source_id") == source_id
    ]


@pytest.mark.unit
class TestReingestionIsIdempotentAcrossSources:
    """The delete-before-insert fix must hold on every ingest path and edge case.

    These complement the README replacement test above: they assert that
    re-ingestion never leaves a prior version's chunks behind for resumes and
    repo metadata, that a shorter document does not strand orphaned chunks, that
    re-ingesting identical content does not accumulate duplicates, and that
    editing one source does not disturb a sibling source.
    """

    @pytest.fixture
    def collection(self):
        return FakeChromaCollection()

    @pytest.fixture
    def pipeline(self, collection):
        # Force _check_skip's lookup to "not found" so ingestion always proceeds;
        # idempotency must come from the delete step, not from skipping.
        db_session = Mock()
        db_session.query.return_value.filter_by.return_value.first.return_value = None
        return IngestionPipeline(
            vector_db=collection,
            db_session=db_session,
            embedding_provider=FakeEmbeddingProvider(),
        )

    def test_edited_resume_replaces_old_chunks(self, pipeline, collection):
        """The resume path must be idempotent, not just the README path."""
        pipeline.ingest_resume(
            profile_id="P", content="# Resume\n\nSkilled in Flask.\n", filename="cv.md"
        )
        assert any("Flask" in doc for doc in collection.all_documents())

        pipeline.ingest_resume(
            profile_id="P", content="# Resume\n\nSkilled in FastAPI.\n", filename="cv.md"
        )
        docs = collection.all_documents()
        assert any("FastAPI" in doc for doc in docs), "re-ingested resume content missing"
        assert not any("Flask" in doc for doc in docs), "stale resume chunk survived"

    def test_edited_repo_metadata_replaces_old_chunks(self, pipeline, collection):
        """The repo-metadata path must be idempotent too.

        Rather than assert on parser-generated text, check that only one content
        version remains for the source — a robust proxy for "no stale chunks".
        """
        repo_v1 = {"name": "proj", "description": "A Flask service.", "language": "Python"}
        repo_v2 = {"name": "proj", "description": "A FastAPI service.", "language": "Python"}

        pipeline.ingest_repo_metadata(profile_id="P", repo_data=repo_v1)
        pipeline.ingest_repo_metadata(profile_id="P", repo_data=repo_v2)

        chunks = _chunks_for_source(collection, "repo_P_proj")
        assert chunks, "repo metadata was not ingested"
        hashes = {rec["metadata"]["content_hash"] for rec in chunks}
        assert len(hashes) == 1, "more than one content version survived for the source"

    def test_shrinking_readme_removes_orphaned_chunks(self, pipeline, collection):
        """A shorter re-ingest must not strand chunks from the longer version."""
        long_readme = (
            "# Project\n\nIntro section.\n\n"
            "## Setup\n\nSetup details here.\n\n"
            "## Usage\n\nUsage details here.\n"
        )
        short_readme = "# Project\n\nJust an intro now.\n"

        pipeline.ingest_readme(profile_id="P", repo_name="r", content=long_readme)
        long_count = len(_chunks_for_source(collection, "readme_P_r"))

        pipeline.ingest_readme(profile_id="P", repo_name="r", content=short_readme)

        docs = collection.all_documents()
        assert not any("Setup details" in d for d in docs), "orphaned 'Setup' chunk survived"
        assert not any("Usage details" in d for d in docs), "orphaned 'Usage' chunk survived"
        assert len(_chunks_for_source(collection, "readme_P_r")) < long_count

    def test_reingesting_identical_content_does_not_duplicate(self, pipeline, collection):
        """Re-ingesting unchanged content (skip bypassed) must not accumulate chunks."""
        readme = "# Project\n\nStable content.\n"

        pipeline.ingest_readme(profile_id="P", repo_name="r", content=readme)
        first_count = len(_chunks_for_source(collection, "readme_P_r"))

        pipeline.ingest_readme(profile_id="P", repo_name="r", content=readme)
        assert len(_chunks_for_source(collection, "readme_P_r")) == first_count

    def test_editing_one_repo_leaves_sibling_source_intact(self, pipeline, collection):
        """Deletes are scoped to a source_id; a sibling repo must be untouched."""
        pipeline.ingest_readme(profile_id="P", repo_name="a", content="# A\n\nAlpha content.\n")
        pipeline.ingest_readme(profile_id="P", repo_name="b", content="# B\n\nBeta content.\n")

        pipeline.ingest_readme(profile_id="P", repo_name="a", content="# A\n\nAlpha v2 content.\n")

        docs = collection.all_documents()
        assert any("Beta content" in d for d in docs), "sibling source B was wrongly deleted"
        assert any("Alpha v2 content" in d for d in docs), "edited source A missing new content"
        # Source A retains exactly one content version after the edit.
        a_hashes = {
            rec["metadata"]["content_hash"] for rec in _chunks_for_source(collection, "readme_P_a")
        }
        assert len(a_hashes) == 1
