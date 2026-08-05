## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/149]

**Issue title:** [Structural chunker silently drops documents that contain no headings
]

**Tier:** [#] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The function, StructuralChunker.chunk(), returns an empty list for any document without markdown headings, and it removes the entire document from the RAG index instead of being it chunked as a single block or falling back to another strategy. I will reproduce the error and then work with the test_document_with_no_headings in tests/unit/test_structural_chunker.py to show a successful fix

**Branch name:** [149-structural-chunker-silently-drops-documents-that-contain-no-headings]

**Setup confirmation:** [#] App runs locally at localhost:5173

**Cohort ledger:** [#] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [e422a33](https://github.com/folusho-adeyemi/pathreview/commit/e422a33bff82ece44e63c35db4ac256909524e05)

**Reproduction summary:**
Ran `StructuralChunker().chunk("This is a plain document with no headings at all. " * 20, {})` and it returned 0 chunks, and `pytest tests/unit/test_structural_chunker.py::TestStructuralChunker::test_document_with_no_headings` failed with `assert 0 >= 1`. Root cause: `_extract_sections()` only collects content and emits a section once a heading has been seen (`if heading_stack ...`), so a document with no headings never populates `heading_stack` and produces no sections. I documented this at the exact guard in `ingestion/chunking/structural_chunker.py`.

**PLAN.md link:** [PLAN.md](https://github.com/folusho-adeyemi/pathreview/blob/149-structural-chunker-silently-drops-documents-that-contain-no-headings/PLAN.md)

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
Need to confirm whether any downstream consumer of the RAG index assumes a non-empty `heading_path` before committing to `heading_path == ""` for heading-less documents (vs. falling back to the source name). This file also has pre-existing ruff/mypy failures that the Week 9 fix commit will need to clean up.
## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

Recorded a baseline of the repo's pre-existing failures before touching anything (`make test-unit`: 53 failed / 375 passed; `make lint`: 182 errors; `make typecheck`: 5 errors), so I could prove my change introduces no new ones.

PLAN.md steps 1–3 are done:

1. **Content collection fixed** — `_extract_sections()` now appends every regular content line instead of gating on `if heading_stack or current_section_lines`.
2. **Section emission fixed** — pulled the duplicated section-dict construction into a new `_build_section()` helper that returns `None` when the collected lines hold no content, and routed both the mid-loop and final emission branches through it. Content outside any heading gets `heading_path == ""` and `heading_level == 0`.
3. **Large-doc path verified** — a 1261-token heading-less document is sub-chunked into 3 chunks through the existing `chunk()` → `SemanticChunker` branch with metadata preserved. No new code needed, as the plan predicted.

I also closed out the Week 8 blocker: I grepped `heading_path`/`heading_level` across `api/`, `core/`, `ingestion/`, `rag/`, `agent/`, `safety/` and `frontend/src/`, and **no code consumes either field** — only a docstring on `BaseChunker.chunk()` mentions them ("heading_path if applicable"). So `heading_path == ""` is safe and the `metadata["source"]` fallback I was considering isn't needed.

Fix committed as `bb391e9` — `fix(ingestion): emit sections for markdown without headings`.

**Next steps:**

PLAN.md steps 4–5: add unit tests for the heading-less, large-heading-less and preamble cases, then re-run `make check` and `make test-unit` against my baseline to confirm no new failures. Then rename the branch to the convention and open the PR.

**Blockers:**

None blocking. Two pre-existing tooling problems I have to work around rather than fix:

- The pre-commit mypy hook has no `tests/` exclude, so it flags all **413** unannotated test functions across all **19** files in `tests/unit/` — while `make typecheck` deliberately scopes to source directories only. I'll match the suite's convention and leave test functions unannotated.
- The pinned pre-commit black (24.1.0) and the black installed by `pip install -e ".[dev]"` (26.5.1) format the same pre-existing code differently and each reverts the other.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/927

**Branch:** `fix/149-structural-chunker-drops-heading-less-docs`

(Renamed from `149-structural-chunker-silently-drops-documents-that-contain-no-headings`, which didn't follow the `<type>/<issue-number>-<short-description>` convention in CONTRIBUTING.md. The earlier PR #242 from the old branch name has been filled in for the record and closed, pointing at #927.)

**What you built:**

`StructuralChunker` silently dropped every markdown document with no headings — `_extract_sections()` only collected content and emitted sections once a heading had been seen, so a heading-less document produced zero sections and `chunk()` returned `[]`. Since `StrategySelector` sends all `readme` documents to this chunker, a heading-less README never entered the RAG index and nothing raised an error. The fix collects content unconditionally and emits a section whenever the collected lines hold content, labelling content outside any heading with an empty breadcrumb and level 0; this also recovers preamble text before the first heading, which was being discarded by the same guard.

**Tests added or updated:**

`tests/unit/test_structural_chunker.py` — four new tests plus one strengthened:

- `test_heading_less_document_has_empty_heading_path` — the `heading_path == ""` / `heading_level == 0` contract.
- `test_heading_less_document_preserves_source_metadata` — caller metadata survives the heading-less path.
- `test_large_heading_less_document_sub_chunked` — a heading-less doc over `SECTION_TOKEN_LIMIT` is sub-chunked via `SemanticChunker` instead of emitted as one oversized chunk.
- `test_preamble_before_first_heading_preserved` — content before the first heading is retained as a leading chunk.
- `test_document_with_no_headings` (the issue's own test) — now also asserts the document text survives, not just the chunk count.

All five fail against the pre-fix chunker and pass against the fix, verified by restoring `main`'s copy of the file and re-running the suite (5 failed / 14 passed → 19 passed). I also completed two assertions in `test_heading_path_format` and `test_heading_path_breadcrumb` that were computed but never checked, so those tests now verify the breadcrumb they describe.

**Self-review confirmation:** [#] make check passes  [#] make test-unit passes

Both in the "introduces no new failures" sense the assignment defines, against the baseline I recorded on `main`:

| Check | Baseline on `main` | With this branch | Delta |
| --- | --- | --- | --- |
| `make test-unit` | 53 failed, 375 passed | 52 failed, 380 passed | 0 new failures; fixes `test_document_with_no_headings`; +4 new tests |
| `make lint` | 182 errors | 178 errors | 0 new errors; clears the 4 in the files I touched |
| `make typecheck` | 5 errors | 5 errors | byte-identical output |

Both files I touched are individually clean: `ruff check ingestion/chunking/structural_chunker.py tests/unit/test_structural_chunker.py` → `All checks passed!`. The 52 remaining test failures are pre-existing and in unrelated modules; the 5 typecheck errors are missing third-party stubs plus a numpy stub syntax error that halts checking before any project file is reached. `make test-integration` was not run — it needs Docker services I don't have available, and this change is a pure-function chunker with no I/O.

**Draft PR feedback received from:** none — I did not get a peer review on a draft before finalising. #242 was open all week from the Week 8 reproduction but attracted no comments or reviews.
