"""Reproduction / verification for issue #6 — duplicate embeddings on re-ingest.

Drives the real IngestionPipeline with the app's own components:
- rag.retriever.vector_store.VectorStore (ChromaDB persistent client)
- ingestion.embeddings.provider.MockEmbeddingProvider (deterministic, offline)
- core.database.AsyncSessionLocal (the app's real session factory)

Each part prints a PASS/FAIL verdict, so the same script serves as both the
before-the-fix reproduction (4 of the 6 checks fail) and the after-the-fix
verification (6/6 pass). Exits non-zero if any check fails.

Run from the repo root:
    .venv/bin/python scripts/repro_issue_6.py

Requires the docker-compose Postgres to be up and seeded (`make seed`) — the
profile is looked up from it, and after the fix the dedup rows are written to it.
"""

import asyncio
import shutil

from sqlalchemy import delete, func, select

from core.database import AsyncSessionLocal
from core.models.ingested_source import IngestedSource
from core.models.profile import Profile
from ingestion.embeddings.provider import MockEmbeddingProvider
from ingestion.pipeline import IngestionPipeline
from rag.retriever.vector_store import VectorStore

CHROMA_DIR = "/tmp/repro6_chroma"

README = """# TaskTracker

A todo app built with FastAPI and React.

## Features

- Create, edit, and complete tasks
- Tag-based filtering and search
- Offline-first sync

## Setup

Run `make dev` and open localhost:3000.
"""


class CountingProvider(MockEmbeddingProvider):
    """Counts embed() calls to expose re-billing on re-ingest."""

    def __init__(self) -> None:
        self.calls = 0
        self.texts_embedded = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        self.texts_embedded += len(texts)
        return super().embed(texts)


def github_fetch(stars: int, pushed_at: str) -> dict:
    """Simulate the GitHub API response for the SAME repo at two points in time."""
    return {
        "name": "tasktracker",
        "description": "A todo app built with FastAPI and React",
        "language": "Python",
        "languages": {"Python": 6000, "TypeScript": 4000},
        "topics": ["fastapi", "react", "productivity"],
        "html_url": "https://github.com/example/tasktracker",
        "stargazers_count": stars,  # volatile
        "pushed_at": pushed_at,  # volatile
    }


def verdict(ok: bool, message: str) -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {message}")
    return ok


async def main() -> None:
    shutil.rmtree(CHROMA_DIR, ignore_errors=True)
    store = VectorStore(persist_dir=CHROMA_DIR)
    collection = store.get_collection("portfolio")
    provider = CountingProvider()

    async with AsyncSessionLocal() as session:
        profile_id = (await session.execute(select(Profile.id).limit(1))).scalar_one_or_none()
        if profile_id is None:
            raise SystemExit("No profiles in the database. Run `make seed` before this script.")

        # Start from a clean dedup ledger so repeated runs are meaningful.
        await session.execute(delete(IngestedSource).where(IngestedSource.profile_id == profile_id))
        await session.commit()

        pipeline = IngestionPipeline(
            vector_db=collection, db_session=session, embedding_provider=provider
        )
        results = []

        print("=" * 72)
        print("PART A — re-ingest the SAME README (byte-identical content)")
        print("=" * 72)
        r1 = await pipeline.ingest_readme(profile_id, "tasktracker", README)
        calls_after_first = provider.calls
        r2 = await pipeline.ingest_readme(profile_id, "tasktracker", README)
        rebilled = provider.calls - calls_after_first
        print(f"\n  1st ingest: skipped={r1.skipped}  chunk_count={r1.chunk_count}")
        print(f"  2nd ingest: skipped={r2.skipped}  chunk_count={r2.chunk_count}")
        results.append(verdict(r2.skipped, "2nd identical README ingest is skipped"))
        results.append(verdict(rebilled == 0, f"embedding provider re-billed {rebilled} time(s)"))

        print()
        print("=" * 72)
        print("PART B — re-ingest the SAME REPO after a routine metadata re-fetch")
        print("        (star count 41 -> 42; nothing about the code changed)")
        print("=" * 72)
        b1 = await pipeline.ingest_repo_metadata(
            profile_id, github_fetch(41, "2026-07-14T10:00:00Z")
        )
        count_after_first = collection.count()
        b2 = await pipeline.ingest_repo_metadata(
            profile_id, github_fetch(42, "2026-07-21T09:00:00Z")
        )
        count_after_second = collection.count()
        print(f"\n  1st ingest: skipped={b1.skipped}  source_id={b1.source_id}")
        print(f"  2nd ingest: skipped={b2.skipped}  source_id={b2.source_id}")
        results.append(
            verdict(
                b1.source_id == b2.source_id,
                "same repo keeps one source_id across a volatile-field change",
            )
        )
        results.append(
            verdict(
                count_after_first == count_after_second,
                f"chroma vector count stable ({count_after_first} -> " f"{count_after_second})",
            )
        )

        print()
        print("=" * 72)
        print("PART C — what retrieval now sees for a query about this repo")
        print("=" * 72)
        query_emb = MockEmbeddingProvider().embed(["python fastapi todo project"])[0]
        hits = store.query(query_emb, "portfolio", n_results=6)
        for h in hits:
            sid = h["metadata"].get("source_id", "?")
            print(f"  score={h['score']:.4f}  source={sid[:44]:44s}  text={h['text'][:40]!r}")
        repo_hits = [h for h in hits if h["metadata"].get("source_type") == "repo"]
        distinct = {h["metadata"]["source_id"] for h in repo_hits}
        print()
        results.append(
            verdict(
                len(distinct) <= 1,
                f"repo 'tasktracker' appears under {len(distinct)} source_id(s) "
                f"across {len(repo_hits)} of the top {len(hits)} hits",
            )
        )

        print()
        print("=" * 72)
        print("PART D — the dedup ledger")
        print("=" * 72)
        rows = (
            (
                await session.execute(
                    select(IngestedSource.source_id, IngestedSource.chunk_count).where(
                        IngestedSource.profile_id == profile_id
                    )
                )
            )
            .tuples()
            .all()
        )
        total = (
            await session.execute(
                select(func.count())
                .select_from(IngestedSource)
                .where(IngestedSource.profile_id == profile_id)
            )
        ).scalar_one()
        for source_id, chunk_count in rows:
            print(f"  {source_id}  chunks={chunk_count}")
        print()
        results.append(verdict(total == 2, f"ingested_sources holds {total} row(s), expected 2"))

        print()
        print("SUMMARY")
        print(
            f"  embed() batches billed : {provider.calls} "
            f"(texts embedded: {provider.texts_embedded})"
        )
        print(f"  chroma vectors stored  : {collection.count()}")
        print(f"  ingested_sources rows  : {total}")
        print()
        passed = sum(1 for r in results if r)
        print(f"  {passed}/{len(results)} checks passed")
        if passed != len(results):
            raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
