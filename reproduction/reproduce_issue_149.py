"""Minimal runtime reproduction for PathReview issue #149.

Issue: Structural chunker silently drops documents that contain no headings.
https://github.com/ascherj/pathreview/issues/149

Running this script passes a valid, nonempty, heading-less document to
``StructuralChunker.chunk()`` and prints the number of chunks it returns.
Expected (post-fix): at least one chunk. Actual (current): zero chunks.
"""

from ingestion.chunking.structural_chunker import StructuralChunker


def main() -> None:
    """Show that a nonempty heading-less document returns no chunks."""
    text = "This is a plain document with no headings at all. " * 20

    metadata = {
        "source": "week-8-reproduction",
        "source_type": "readme",
    }

    chunker = StructuralChunker()
    chunks = chunker.chunk(text, metadata)

    print(f"Input characters: {len(text)}")
    print(f"Chunks returned: {len(chunks)}")
    print("Expected chunks: at least 1")
    print(f"Actual chunks: {chunks}")


if __name__ == "__main__":
    main()
