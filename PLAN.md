## Solution plan

**Issue:** [`README.md` is missing the project overview and feature list](https://github.com/jamjamgobambam/pathreview/issues/114)

---

### Understand

**Root cause:** The `README.md` was written as a minimal setup guide. It listed features as one-line bullets and included a bare architecture table, but it never answered the two questions a new reader asks first: *"What problem does this solve?"* and *"Who is this for?"* There was no problem statement, no target-audience section, no step-by-step explanation of the end-to-end user flow, and no prose context for the architecture table.

**Expected behavior:** A reader who lands on the README with no prior knowledge can understand what PathReview is, why it exists, who it's designed for, and how it works — before they ever look at any code.

**Actual behavior:** The README jumped straight to a feature bullet list and a Quick Start section, leaving the "why" and "who" completely undefined. Contributors and students browsing the issue tracker had no way to orient themselves.

---

### Map

Only one file requires changes:

| File | Role |
|---|---|
| `README.md` | Root-level project README — the only file this issue touches |

Supporting reference files (read-only, used to write accurate descriptions):

| File | Why it was read |
|---|---|
| `docs/ARCHITECTURE.md` | Verify subsystem descriptions and data flow |
| `agent/` | Confirm the five analysis tools and their behavior |
| `ingestion/` | Confirm supported parsers (PDF, Markdown, GitHub, repo README) |
| `rag/` | Confirm hybrid retrieval (vector + BM25) and feedback generation |
| `safety/` | Confirm the four-stage safety pipeline stages |
| `frontend/` | Confirm the React + TypeScript dashboard capabilities |

---

### Plan

1. **Read the codebase and existing docs** — Explore each subsystem directory and read `docs/ARCHITECTURE.md` to build an accurate picture of what PathReview does. This ensures every sentence added to the README is verifiable against the code.

2. **Add a "The Problem" section** — Write a concise explanation of why early-career developers need this tool and what gap it fills. Place it immediately after the tagline so the reader understands the motivation before anything else.

3. **Add a "Who It's For" section** — List the four target audiences (bootcamp graduates, CS students, career changers, mentors/coaches) with a one-sentence description of each. This gives readers a quick way to self-identify as a user.

4. **Expand the Features section** — Replace the five one-line bullets with full paragraphs. Each feature section should name the subsystem directory, describe what it does, and call out any notable implementation detail (e.g., hybrid retrieval, the five agent tools, the four safety stages).

5. **Add a "How It Works" step-by-step flow** — Write a numbered ASCII-diagram walkthrough showing the data path from user submission through ingestion → agent orchestration → RAG feedback → safety filtering → dashboard display.

---

### Inputs & outputs

**Input:** The existing `README.md` with its minimal feature bullets and bare architecture table.

**Output:** An enriched `README.md` that adds:
- A Table of Contents linking to all major sections
- "The Problem" section (~2 paragraphs)
- "Who It's For" section (4 audience bullets with descriptions)
- Expanded Features section (5 subsections with full prose and a tool reference table)
- "How It Works" step-by-step ASCII flow (6 steps)

The Quick Start, Architecture table, Development, Contributing, and License sections remain unchanged.

---

### Risks & unknowns

- **Accuracy risk:** If a subsystem description is wrong (e.g., misidentifying the retrieval strategy in `rag/` or the safety stages in `safety/`), the README becomes actively misleading. Mitigation: cross-check every claim against the relevant source file before committing.
- **Scope creep:** It would be easy to keep expanding the README indefinitely. The fix is scoped to the four missing sections named in the issue — any further changes (e.g., adding badges, a changelog, or a demo GIF) are out of scope for this PR.
- **Duplication with `docs/`:** The project has a `docs/ARCHITECTURE.md` and `docs/SETUP.md`. New README content should summarize and link to those files, not duplicate them verbatim.

---

### Edge cases

- **Reader unfamiliar with RAG or AI tooling:** Descriptions should avoid assuming the reader knows what "retrieval-augmented generation" or "vector embeddings" mean. Either define the term in plain language or omit the jargon.
- **Reader on mobile or a slow connection:** No images or large assets are added. The ASCII flow diagram is plain text and renders in any Markdown viewer.
- **README rendered on GitHub vs. local Markdown viewer:** All added sections use standard CommonMark syntax (headings, bullet lists, tables, fenced code blocks) — no GitHub-specific extensions that would break in other renderers.
- **Future codebase changes:** If subsystem names or tool counts change, the README will drift. The "How It Works" and Features sections reference directory names (e.g., `agent/`, `rag/`) so a future contributor can quickly locate and update the affected prose.
