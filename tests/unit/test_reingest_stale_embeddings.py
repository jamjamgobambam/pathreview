"""Regression tests for issue #27: stale embeddings survive document re-ingestion.

https://github.com/jamjamgobambam/pathreview/issues/27

The ingestion pipeline appended embeddings via a raw ``vector_db.add(...)`` and never
deleted a source's prior vectors. Because ``source_id`` embeds a content hash, editing a
document produced a new source_id and its old vectors lingered in the collection.

The fix upserts the new chunks and then deletes any vector sharing the stable
``base_source_id`` except the version just stored (``IngestionPipeline._purge_stale_vectors``).
Storing before deleting means a mid-store failure cannot leave the source with neither the
old nor the new vectors. These tests drive the real re-ingestion path across all three
ingest methods.
"""

from typing import Any
from unittest.mock import MagicMock

import pytest

from ingestion.pipeline import IngestionPipeline


class FakeCollection:
    """In-memory stand-in for a ChromaDB collection (upsert/add/get/delete + where)."""

    def __init__(self) -> None:
        self.store: dict[str, dict[str, Any]] = {}  # id -> {embedding, metadata, document}

    def upsert(
        self,
        ids: list[str],
        embeddings: list | None = None,
        metadatas: list | None = None,
        documents: list | None = None,
    ) -> None:
        for i, _id in enumerate(ids):
            self.store[_id] = {
                "embedding": embeddings[i] if embeddings else None,
                "metadata": metadatas[i] if metadatas else {},
                "document": documents[i] if documents else "",
            }

    # The pipeline uses upsert; keep add as an alias for completeness.
    add = upsert

    @staticmethod
    def _matches(metadata: dict, where: dict) -> bool:
        """Evaluate a subset of ChromaDB's ``where`` grammar ($and/$or/$eq/$ne)."""
        if "$and" in where:
            return all(FakeCollection._matches(metadata, c) for c in where["$and"])
        if "$or" in where:
            return any(FakeCollection._matches(metadata, c) for c in where["$or"])
        for key, cond in where.items():
            value = metadata.get(key)
            if isinstance(cond, dict):
                for op, want in cond.items():
                    if op == "$eq" and value != want:
                        return False
                    if op == "$ne" and value == want:
                        return False
            elif value != cond:
                return False
        return True

    def get(self, where: dict | None = None, ids: list | None = None) -> dict[str, list]:
        matched = []
        for _id, rec in self.store.items():
            if ids is not None and _id not in ids:
                continue
            if where is not None and not self._matches(rec["metadata"], where):
                continue
            matched.append(_id)
        return {
            "ids": matched,
            "metadatas": [self.store[i]["metadata"] for i in matched],
            "documents": [self.store[i]["document"] for i in matched],
        }

    def delete(self, ids: list | None = None, where: dict | None = None) -> None:
        target = set(self.get(where=where, ids=ids)["ids"]) if (ids or where) else set(self.store)
        for _id in list(target):
            self.store.pop(_id, None)

    def all_source_ids(self) -> set:
        return {rec["metadata"].get("source_id") for rec in self.store.values()}


def _make_pipeline() -> tuple[IngestionPipeline, FakeCollection, MagicMock]:
    """Build a pipeline over an in-memory collection; return it, the store, and the provider."""
    vector_db = FakeCollection()
    db_session = MagicMock()
    # _check_skip queries db_session; make it return None so re-ingestion proceeds.
    db_session.query.return_value.filter_by.return_value.first.return_value = None
    provider = MagicMock()
    provider.embed = lambda texts: [[0.1] * 8 for _ in texts]
    p = IngestionPipeline(
        vector_db=vector_db,
        db_session=db_session,
        embedding_provider=provider,
    )
    return p, vector_db, provider


@pytest.fixture
def pipeline() -> tuple[IngestionPipeline, FakeCollection]:
    p, vector_db, _ = _make_pipeline()
    return p, vector_db


@pytest.mark.unit
def test_reingesting_edited_readme_purges_old_vectors(
    pipeline: tuple[IngestionPipeline, FakeCollection],
) -> None:
    """Editing and re-ingesting a README leaves only the current version's vectors."""
    p, vector_db = pipeline

    r1 = p.ingest_readme("profile-1", "repoX", "# Project\n\nInitial version of the docs.\n")
    r2 = p.ingest_readme("profile-1", "repoX", "# Project\n\nEdited version, content changed.\n")

    # Sanity: editing the content produced a new content-hashed source_id.
    assert r1.source_id != r2.source_id

    stored = vector_db.all_source_ids()
    assert r1.source_id not in stored, (
        f"Stale vectors from the previous README version {r1.source_id} "
        f"survived re-ingestion; store holds source_ids {stored}"
    )
    assert stored == {r2.source_id}


@pytest.mark.unit
def test_reingesting_edited_resume_purges_old_vectors(
    pipeline: tuple[IngestionPipeline, FakeCollection],
) -> None:
    """The resume ingest path is also idempotent across content edits."""
    p, vector_db = pipeline

    r1 = p.ingest_resume("profile-1", "Summary\n\nBuilt project A at Company.", "resume.md")
    r2 = p.ingest_resume(
        "profile-1", "Summary\n\nBuilt project B at Company, revised.", "resume.md"
    )

    assert r1.source_id != r2.source_id
    stored = vector_db.all_source_ids()
    assert r1.source_id not in stored
    assert stored == {r2.source_id}


@pytest.mark.unit
def test_reingesting_edited_repo_purges_old_vectors(
    pipeline: tuple[IngestionPipeline, FakeCollection],
) -> None:
    """The repo-metadata ingest path is also idempotent across content edits."""
    p, vector_db = pipeline

    r1 = p.ingest_repo_metadata(
        "profile-1", {"name": "repoX", "description": "v1", "language": "Python"}
    )
    r2 = p.ingest_repo_metadata(
        "profile-1", {"name": "repoX", "description": "v2 edited", "language": "Python"}
    )

    assert r1.source_id != r2.source_id
    stored = vector_db.all_source_ids()
    assert r1.source_id not in stored
    assert stored == {r2.source_id}


@pytest.mark.unit
def test_identical_reingest_keeps_single_version(
    pipeline: tuple[IngestionPipeline, FakeCollection],
) -> None:
    """Re-ingesting identical content upserts the same ids without duplicating or erroring."""
    p, vector_db = pipeline
    content = "# Project\n\nUnchanged content ingested twice.\n"

    p.ingest_readme("profile-1", "repoX", content)
    ids_after_first = set(vector_db.store)
    p.ingest_readme("profile-1", "repoX", content)

    assert set(vector_db.store) == ids_after_first


@pytest.mark.unit
def test_first_time_ingest_purge_is_noop(
    pipeline: tuple[IngestionPipeline, FakeCollection],
) -> None:
    """The purge step is a safe no-op when the source has never been ingested before."""
    p, vector_db = pipeline

    result = p.ingest_readme("profile-1", "repoX", "# Project\n\nFirst ever ingest.\n")

    assert vector_db.all_source_ids() == {result.source_id}


@pytest.mark.unit
def test_reingest_scoped_to_repo_leaves_other_repo(
    pipeline: tuple[IngestionPipeline, FakeCollection],
) -> None:
    """Re-ingesting one repo's README must not delete another repo's vectors."""
    p, vector_db = pipeline

    repo_y = p.ingest_readme("profile-1", "repoY", "# Y\n\nRepo Y documentation.\n")
    p.ingest_readme("profile-1", "repoX", "# X\n\nRepo X documentation.\n")
    p.ingest_readme("profile-1", "repoX", "# X\n\nRepo X documentation, edited.\n")

    assert repo_y.source_id in vector_db.all_source_ids()


@pytest.mark.unit
def test_reingest_removes_all_old_chunks_multichunk(
    pipeline: tuple[IngestionPipeline, FakeCollection],
) -> None:
    """A multi-section document purges every old chunk, not just the first."""
    p, vector_db = pipeline
    v1 = "# Title\n\nIntro one.\n\n## Setup\n\nInstall one.\n\n## Usage\n\nRun one.\n"
    v2 = "# Title\n\nIntro two.\n\n## Setup\n\nInstall two.\n\n## Usage\n\nRun two.\n"

    r1 = p.ingest_readme("profile-1", "repoX", v1)
    r2 = p.ingest_readme("profile-1", "repoX", v2)

    stored = vector_db.all_source_ids()
    assert r1.source_id not in stored
    assert stored == {r2.source_id}


@pytest.mark.unit
def test_store_failure_preserves_previous_version() -> None:
    """If storing the new version fails, the previous version's vectors survive.

    This is the point of storing before deleting: a failed re-ingest must not leave the
    source with neither the old nor the new vectors.
    """
    p, vector_db, provider = _make_pipeline()

    r1 = p.ingest_readme("profile-1", "repoX", "# T\n\nOriginal content.\n")

    # The next ingestion fails while embedding the new version.
    provider.embed = MagicMock(side_effect=RuntimeError("embedding backend down"))
    with pytest.raises(RuntimeError):
        p.ingest_readme("profile-1", "repoX", "# T\n\nEdited content that fails to embed.\n")

    # The old version is still present and intact.
    assert vector_db.all_source_ids() == {r1.source_id}
