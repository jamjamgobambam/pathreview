# Week 7 — Issue #149: Structural chunker silently drops documents that contain no headings

## Issue

- **Link:** https://github.com/ascherj/pathreview/issues/149
- **Title:** Structural chunker silently drops documents that contain no headings
- **Type:** `fix`
- **Subsystem / scope:** `ingestion` (chunking)

## Problem summary

The `StructuralChunker` (used for READMEs) splits markdown on heading
boundaries. When a document contains **no markdown headings at all**, the
chunker returns an **empty list** instead of chunking the plain text. Because
the ingestion pipeline treats an empty chunk list as a successful (non-error)
outcome, the document is recorded as "ingested" with `chunk_count = 0`, no
embeddings are stored, and the content becomes silently unretrievable — no
exception, no user-visible warning.

This matters for READMEs, which are routed to the `StructuralChunker` by the
strategy selector. A heading-less README (common for small projects) would be
accepted by the pipeline yet contribute nothing to retrieval.

## Week 7 deliverables checklist

| Deliverable | Status | Evidence |
|---|---|---|
| Issue link | ✅ | See above |
| Concise problem summary | ✅ | See above |
| Forked repository | ✅ | `origin` → `https://github.com/techmilano/pathreview.git` |
| Configured upstream remote | ✅ | `upstream` → `https://github.com/ascherj/pathreview.git` |
| Issue-specific branch | ✅ | `fix/149-handle-documents-without-headings` (see below) |
| Meaningful setup / documentation commits | ⏳ | This week's docs commit (proposed below) |

## Branch-name verification

`docs/CONTRIBUTING.md` requires: `<type>/<issue-number>-<short-description>`
with types `fix`, `feat`, `test`, `docs`, `refactor`, `perf`, `chore`.

Current branch: **`fix/149-handle-documents-without-headings`**

- `<type>` = `fix` ✅ (valid type)
- `<issue-number>` = `149` ✅ (matches issue)
- `<short-description>` = `handle-documents-without-headings` ✅ (kebab-case)

**Verdict:** Compliant.

## Repository subsystems (per `README.md` / observed layout)

| Subsystem | Directory | Role |
|---|---|---|
| API Layer | `api/` | FastAPI REST API |
| Ingestion Pipeline | `ingestion/` | Parsing, **chunking**, embeddings |
| RAG System | `rag/` | Retrieval, generation, evaluation |
| Agent System | `agent/` | Multi-tool orchestration |
| Safety Layer | `safety/` | Filtering, bias/PII, prompt defense |
| Frontend | `frontend/` | React + TypeScript (Vite) |
| Core | `core/` | Config + shared models |
| Tests | `tests/` | Unit tests + fixtures |

Issue #149 lives entirely in the **Ingestion Pipeline → chunking** area.

## Scope guardrails for this week

- No production code or tests modified (documentation only).
- Root cause is described from static reading of the code; **reproduction and a
  `PLAN.md` are deferred to Week 8**.
- No push, PR, or GitHub issue changes.

## Detailed findings

See [`INVESTIGATION.md`](INVESTIGATION.md) for the execution path, implicated
files, existing patterns, and the metadata contract a future fix must preserve.

## Proposed Conventional Commit (documentation only)

```
docs(ingestion): add week 7 investigation notes for issue #149

Document the structural chunker's silent-drop behavior for heading-less
documents: execution path, implicated files, existing chunker patterns,
and the chunk metadata contract a future fix must preserve. No production
code or tests changed.

Refs #149
```

> Scope note: `docs/CONTRIBUTING.md` lists `ingestion` among the valid scopes.
> `docs(ingestion)` ties the documentation to the affected subsystem. A plain
> `docs: ...` (no scope) is also acceptable per the spec if a scopeless subject
> is preferred.
</content>
</invoke>
