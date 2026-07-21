Week 7 — Issue selection

Issue link: https://github.com/ascherj/pathreview/issues/153

Issue title: Faithfulness checker crashes when a context chunk has text: None

Tier: [x] Tier 1  [ ] Tier 2  [ ] Tier 3

Problem summary:
The RAG system's faithfulness checker verifies that generated review feedback is actually supported by the retrieved context chunks. When building that context, it pulls each chunk's text using chunk.get("text", ""), assuming a missing key falls back to an empty string, but a dict's .get() only applies the default when the key is absent, not when the key exists with a None value. If any chunk in the context has text: None (rather than a missing text field entirely), the subsequent string-join over all chunk texts crashes with a TypeError instead of gracefully treating it as empty. A successful fix would normalize None text values to an empty string (or filter them out) before joining, so the faithfulness checker degrades gracefully instead of crashing when upstream ingestion produces a chunk with no text.

Branch name: fix/153-faithfulness-checker-none-text

Setup confirmation: [x] App runs locally at localhost:5173

Cohort ledger: [x] Issue added to cohort ledger 