# PathReview — Issue #149 Presentation
### Structural Chunker Silently Drops Heading-Free Documents

---

## 1. The Project: PathReview

PathReview is an **AI-powered portfolio review assistant** for early-career developers.

A user submits their GitHub profile, resume, and project repositories. The system analyzes
everything and returns structured, actionable feedback on:
- Portfolio completeness
- Project quality
- Skill gaps
- Presentation improvements

The feedback is powered by a **RAG (Retrieval-Augmented Generation)** pipeline — meaning
the AI's responses are grounded in the user's actual documents, not generic advice.

```
User uploads GitHub / Resume / Repos
           ↓
  Ingestion Pipeline  ← parse → chunk → embed → store in vector DB
           ↓
  Agent Orchestrator  ← GitHub, skills, README, market, tech tools
           ↓
  RAG System          ← retrieve context → generate feedback
           ↓
  Safety Layer        ← bias check, PII scrub, content filter
           ↓
      Review Output
```

---

## 2. The Problem

**Issue #149 — Structural chunker silently drops documents that contain no headings**

### What is chunking?

Before a document can be searched or fed to an LLM, it must be split into smaller pieces
called **chunks**. PathReview's `StructuralChunker` does this by splitting on markdown
headings (`#`, `##`, `###`).

### The bug

When a document has **no markdown headings at all** — like a plain-text resume or a
prose-only README — the chunker returned an empty list `[]` with no error or warning.

That empty list meant the document was **silently excluded from the vector index**. The RAG
system had nothing to retrieve from it, so the generated review had an invisible gap.

### Root cause (inside `_extract_sections()`)

```python
else:
    # Regular content line
    if heading_stack or current_section_lines:  # ← GUARD
        current_section_lines.append(line)
```

For a heading-free document, `heading_stack` is always empty and
`current_section_lines` starts empty, so the guard is `False` for **every single line**.
Nothing is ever collected.

The "save final section" block had the same problem:

```python
if current_section_lines and heading_stack:  # ← heading_stack is empty → skipped
```

Result: `_extract_sections()` returns `[]`, `chunk()` returns `[]`, and the document
disappears from the pipeline with no log message, no exception, nothing.

### Impact

| Document type          | Before fix     | After fix         |
|------------------------|----------------|-------------------|
| Plain-text resume      | ❌ Silently dropped | ✅ Chunked & indexed |
| Prose-only README      | ❌ Silently dropped | ✅ Chunked & indexed |
| Standard markdown doc  | ✅ Works fine   | ✅ Still works fine  |

---

## 3. The Solution

### Strategy

Add a **no-headings fallback** in `chunk()` — after `_extract_sections()` runs, if it
returned empty, wrap the entire document text in a single synthetic section and let the
existing loop handle it normally.

This approach:
- Touches exactly **one method** in **one file**
- Carries **zero regression risk** for documents that already have headings
- Automatically handles both small and large heading-free documents using the same
  sub-chunking path that already exists for oversized headed sections

### The fix (15 lines added to `structural_chunker.py`)

```python
def chunk(self, text: str, metadata: dict) -> list[Chunk]:
    if not text or not text.strip():
        return []

    sections = self._extract_sections(text)

    # ✅ NEW: Fallback for heading-free documents (issue #149)
    if not sections:
        sections = [
            {
                "content": text.strip(),
                "path": [],
                "level": 0,
            }
        ]

    # Existing loop — unchanged
    chunks = []
    for section in sections:
        heading_path = " > ".join(section["path"])
        section_text = section["content"]
        section_tokens = len(self.encoder.encode(section_text))

        if section_tokens > self.SECTION_TOKEN_LIMIT:
            # Large section → delegate to SemanticChunker
            section_metadata = metadata.copy()
            section_metadata.update({
                "heading_path": heading_path,
                "heading_level": section["level"],
            })
            sub_chunks = self.semantic_chunker.chunk(section_text, section_metadata)
            chunks.extend(sub_chunks)
        else:
            # Small section → single Chunk
            section_metadata = metadata.copy()
            section_metadata.update({
                "heading_path": heading_path,
                "heading_level": section["level"],
                "chunk_index": len(chunks),
                "char_start": 0,
                "char_end": len(section_text),
            })
            chunks.append(Chunk(text=section_text, metadata=section_metadata))

    return chunks
```

### How it flows for different inputs

```
Heading-free document, ≤ 800 tokens
  └─ sections = [{ content: full_text, path: [], level: 0 }]
  └─ section_tokens ≤ 800
  └─ → 1 Chunk  ✅

Heading-free document, > 800 tokens
  └─ sections = [{ content: full_text, path: [], level: 0 }]
  └─ section_tokens > 800
  └─ → SemanticChunker.chunk(full_text, ...)
  └─ → N Chunks  ✅

Document with headings
  └─ _extract_sections() returns non-empty list
  └─ fallback is skipped entirely
  └─ → existing behavior, unchanged  ✅

Empty or whitespace-only document
  └─ early guard at top of chunk() catches it
  └─ → []  ✅ (unchanged)
```

---

## 4. Edge Cases Considered

| Input | Behavior |
|---|---|
| Heading-free, ≤ 800 tokens | 1 Chunk, `heading_level=0`, `heading_path=""` |
| Heading-free, > 800 tokens | Multiple Chunks from SemanticChunker, metadata preserved |
| Empty string | Returns `[]` — unchanged |
| Whitespace only | Returns `[]` — unchanged |
| Heading inside a code block | Pre-existing issue, out of scope (known) |
| Empty metadata dict `{}` | `metadata.copy()` on `{}` is safe |

---

## 5. Tests

Two tests in `tests/unit/test_structural_chunker.py`:

### Existing test — now passes
```python
def test_document_with_no_headings(self, chunker):
    """Test document with no headings returns single chunk."""
    text = "This is plain text without any markdown headings. " * 20
    result = chunker.chunk(text, {"source": "test"})

    assert len(result) >= 1                         # was failing: returned 0
    assert isinstance(result[0], Chunk)
    assert all(isinstance(c, Chunk) for c in result)
```

### New regression test — large heading-free document
```python
def test_large_heading_free_document_is_sub_chunked(self, chunker):
    """Heading-free document > 800 tokens must be sub-chunked."""
    sentence = "This is a sentence in a long plain-text document without any headings. "
    large_text = sentence * 100  # ~1,401 tokens

    result = chunker.chunk(large_text, {"source": "plain-resume"})

    assert len(result) > 1                                      # sub-chunked
    assert all(isinstance(c, Chunk) for c in result)
    assert all(c.text.strip() for c in result)
    assert all(c.metadata.get("source") == "plain-resume" for c in result)  # metadata preserved
    assert all(c.metadata.get("heading_level") == 0 for c in result)        # correct level
```

### Full suite result
```
16/16 tests pass — 0 regressions
```

---

## 6. What Was Verified

| Check | Result |
|---|---|
| `pytest tests/unit/test_structural_chunker.py` | ✅ 16/16 pass |
| `strategy_selector.py` does not rely on empty return | ✅ Confirmed by code review |
| `pipeline.py` does not rely on empty return | ✅ Confirmed by code review |
| `SemanticChunker` preserves `heading_path` metadata | ✅ Confirmed by code review |
| No new lint errors introduced | ✅ Pre-existing errors only, none in changed file |
| No new mypy errors introduced | ✅ Pre-existing stub errors only |

---

## 7. PR

**Branch:** `fix/149-structural-chunker-no-headings`  
**PR:** https://github.com/ascherj/pathreview/pull/353

Files changed:
- `ingestion/chunking/structural_chunker.py` — +15 lines (fallback block)
- `tests/unit/test_structural_chunker.py` — +1 new regression test

No schema changes. No API changes. No database migrations.

---

## 8. Key Takeaways

1. **Silent failures are the worst failures.** Returning `[]` with no log or exception made this bug invisible in production — documents were being dropped with no trace.

2. **Minimal, targeted fixes beat large refactors.** The root cause was in `_extract_sections()`, but fixing it there would have required restructuring the whole method. A 15-line fallback in `chunk()` solved the problem without touching the parsing logic at all.

3. **Reuse existing paths.** The fallback doesn't implement new sub-chunking logic — it feeds the synthetic section into the loop that was already there, which already handles the `SemanticChunker` delegation. No duplication.

4. **Understand before changing.** Before writing a line, the plan mapped all callers of `chunk()` and checked whether any depended on the broken empty-return behavior. They didn't — which made the fix safe.
