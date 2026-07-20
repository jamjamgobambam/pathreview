## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [will fill in after pushing]

**Reproduction summary:**
Ran `.venv/bin/pytest tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -q` and confirmed the failure: the warning log "Empty chunks list provided to BatchEmbeddingProcessor" is clearly printed to stdout, but `caplog.text` is empty, causing the assertion to fail. This confirms structlog output isn't propagating into Python's standard `logging` module, which is what pytest's `caplog` fixture reads from.

**PLAN.md link:** [will fill in after creating it]

**Walkthrough video (recommended):** [optional — skip or add later]

**Blockers or open questions:**
Need to determine the cleanest way to configure structlog to propagate to stdlib logging in tests/conftest.py — likely via structlog.stdlib processors or the capture_logs context manager.
