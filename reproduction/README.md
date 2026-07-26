# Issue #149 Reproduction

## Issue

* **Repository:** `ascherj/pathreview`
* **Fork:** `techmilano/pathreview`
* **Issue:** `#149`
* **Title:** Structural chunker silently drops documents that contain no headings
* **Branch:** `fix/149-handle-documents-without-headings`
* **Commit tested:** `c6b7d7994205596f7486b1028fb3bc4a3c16ba17`

## Reproduction Status

**Confirmed**

`StructuralChunker.chunk()` returns an empty list when it receives a valid,
nonempty document without Markdown headings.

## Environment

* **Operating system:** Ubuntu 24.04.4 LTS (Linux 6.17.0-20-generic)
* **Python version:** 3.12.3
* **Pytest version:** 9.1.1
* **tiktoken version:** 0.13.0
* **Git commit:** `c6b7d7994205596f7486b1028fb3bc4a3c16ba17`

> Note: reproduction was run in a lightweight virtual environment containing
> only `pytest` and `tiktoken` (the sole runtime import of
> `structural_chunker.py`). The direct script was executed from the repository
> root with `PYTHONPATH=.` so the `ingestion` package resolves the same way it
> would after `pip install -e .`.

## Automated Test Reproduction

Command:

```bash
pytest \
  tests/unit/test_structural_chunker.py::TestStructuralChunker::test_document_with_no_headings \
  -v
```

Expected:

```text
The nonempty heading-less document returns at least one Chunk.
```

Actual:

```text
The chunker returns an empty list and the test fails with `assert 0 >= 1`.
```

Evidence:

```text
reproduction/failing_test_output.txt
```

## Direct Runtime Reproduction

Command:

```bash
PYTHONPATH=. python reproduction/reproduce_issue_149.py
```

Expected:

```text
Chunks returned: at least 1
```

Actual:

```text
Input characters: 1000
Chunks returned: 0
Expected chunks: at least 1
Actual chunks: []
```

The script was run twice and produced byte-identical output, confirming the
failure is deterministic.

Evidence:

```text
reproduction/direct_reproduction_output.txt
```

## Root Cause

The issue occurs in:

```text
ingestion/chunking/structural_chunker.py
```

`_extract_sections()` collects non-heading lines only after a heading or
existing section content is already present:

```python
else:
    # Regular content line
    if heading_stack or current_section_lines:  # never true without a heading
        current_section_lines.append(line)
```

A heading-less document never satisfies that guard, so every content line is
discarded, the final save condition `if current_section_lines and heading_stack`
also stays false, and `_extract_sections()` returns `[]`. `chunk()` then loops
over zero sections and returns `[]`. Downstream, the pipeline treats an empty
chunk list as success and stores no embeddings — silent data loss, no
exception.

## Related Preamble Investigation

Command:

```bash
PYTHONPATH=. python - <<'PY'
from ingestion.chunking.structural_chunker import StructuralChunker
text = """Introductory content before the first heading.

# Installation

Installation instructions.
"""
chunks = StructuralChunker().chunk(text, {"source": "week-8-preamble-check"})
print(f"Chunks returned: {len(chunks)}")
for i, c in enumerate(chunks):
    print(i, c.metadata.get("heading_path"), repr(c.text))
PY
```

Result:

```text
Chunks returned: 1
Chunk 0 -> heading_path "Installation", text "Installation instructions."
Introductory content present in any chunk? NO — the preamble was dropped.
```

The introductory content before the first heading does **not** appear in any
returned chunk. This is caused by the same guard in `_extract_sections()`.

Scope decision:

```text
Preamble-before-heading behavior is related but is not included in the narrow
issue #149 fix unless maintainers confirm that it belongs in scope.
```

## Existing Behavior Baseline

Command:

```bash
pytest tests/unit/test_structural_chunker.py \
  -k "not test_document_with_no_headings" \
  -v
```

Result:

```text
14 passed, 1 deselected in 0.17s
```

All non-target structural chunker tests pass (empty/whitespace input returns
`[]`, nested heading paths, breadcrumbs, large-section sub-chunking, heading
levels, caller metadata, multiple H1 headings, chunk text content). These
behaviors must remain unchanged by the Week 9 fix.

Evidence:

```text
reproduction/related_tests_output.txt
```

## Week 8 Scope

This commit documents the broken behavior and where it occurs.

It does **not** implement the production fix. The fix is planned in the
root-level `PLAN.md` and will be implemented in Week 9.
