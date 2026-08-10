# Issue #159 — pytest/structlog `caplog` Routing Architecture Lock

**Status:** LOCKED for implementation  
**Issue:** [#159 — structlog output is not captured by pytest `caplog`](https://github.com/ascherj/pathreview/issues/159)  
**Branch:** `test/159-structlog-caplog-propagation`  
**Scope decision:** **Hold Scope.** The issue is correctly bounded to the test harness and its regression coverage. Any architectural change requires explicit human re-approval.

## 1. Office-Hours Problem Framing: Six Forcing Questions

### 1. What problem are we actually solving?
Tests need structlog events emitted by code under test to become standard-library `LogRecord` objects because pytest `caplog` cannot observe structlog's unconfigured stdout-only `PrintLoggerFactory` output.

### 2. Who is affected and how?
- Contributors writing or running Python tests are directly affected: valid log assertions fail despite visible stdout output.
- Reviewers and CI are indirectly affected: the canonical unit test fails and future caplog assertions would be unreliable suite-wide.
- Application users are not affected by this change; runtime logging behavior must remain unchanged.

### 3. What does success look like?
- A new test that imports a structlog logger at module-import time and relies only on shared `tests/conftest.py` configuration fails before the fix and passes after it.
- The existing `test_empty_chunks_list_returns_empty` assertion sees the warning in `caplog` and passes.
- `caplog.set_level(...)` / `caplog.at_level(...)` controls lower-level capture normally.
- The unit suite and project quality checks pass without application-source, dependency, or infrastructure changes.

### 4. What are the failure modes?
Highest blast radius first: global test configuration could break logging in unrelated tests; configuration could occur after test modules bind loggers; logger caching could retain a stale backend; an incompatible final processor could prevent stdlib emission; capture thresholds could intentionally filter INFO/DEBUG; repeated handlers could duplicate records. Recovery is to keep configuration import-time, minimal, cache-free, handler-free, and verified first by a focused harness test and then the unit suite.

### 5. What is the simplest version that delivers value?
Configure structlog once at `tests/conftest.py` import time with `structlog.stdlib.LoggerFactory`, a deterministic renderer, and `cache_logger_on_first_use=False`; add one dedicated shared-routing regression test; retain the existing batch-processor bug test unchanged.

### 6. What are we explicitly not doing?
No production logging changes, no batch-processor changes, no pytest plugin or dependency changes, no global pytest logging options, no broad log-assertion rewrite, no API startup fix, and no chromadb/chroma or NumPy remediation.

## 2. Scope and Non-Goals

### In scope
- Shared pytest-only structlog-to-stdlib routing in `tests/conftest.py`.
- A dedicated RED/GREEN regression test proving shared conftest routing, import-time logger compatibility, level mapping, and structured message observability.
- Validation of the existing batch-processor failure and the unit suite.
- Week 9 journal and PR evidence for #159.

### Non-goals
- Calling or changing `core.logging.configure_logging()`.
- Modifying `core/logging.py`, `ingestion/embeddings/batch_processor.py`, existing batch-processor test logic, `pyproject.toml`, dependencies, or application startup.
- Adding stdlib handlers or calling `logging.basicConfig()` from tests; pytest owns capture handlers.
- Solving the `chromadb/chroma:0.4.22` startup failure caused by NumPy 2.x. Unit validation uses mocks and needs no Docker services.
## 3. Locked Approach and Resolved Open Questions

### Decision A — dedicated test configuration, not `core.configure_logging()`
`tests/conftest.py` will own a minimal test-only configuration. It will **not** import or call `core.logging.configure_logging()` because that function reads environment-backed application settings, selects production/development presentation, installs a stdout handler via `logging.basicConfig()`, and caches loggers. Those are runtime concerns and can couple tests to environment, formatting, handler ordering, and duplicate-output behavior.

The test configuration will:
1. Import `logging` (for tests/typing where needed) and `structlog` alongside pytest.
2. Define a private, fully typed helper such as `_configure_structlog_for_tests() -> None`.
3. Call that helper at `tests/conftest.py` module import, before fixture definitions and before pytest imports test modules.
4. Call `structlog.configure()` with this exact intent:
   - `context_class=dict`.
   - `wrapper_class=structlog.stdlib.BoundLogger`.
   - `logger_factory=structlog.stdlib.LoggerFactory()` so calls emit stdlib records.
   - processors, in order: `structlog.stdlib.filter_by_level`, `structlog.stdlib.add_logger_name`, `structlog.stdlib.add_log_level`, `structlog.stdlib.PositionalArgumentsFormatter()`, `structlog.processors.format_exc_info`, then `structlog.processors.JSONRenderer(sort_keys=True)` as the terminal deterministic renderer.
   - `cache_logger_on_first_use=False`.
5. Not install, remove, or mutate stdlib handlers. pytest's logging plugin and `caplog` remain the capture owner.

JSON is a test presentation detail, not a contract. Tests assert record existence, stdlib level, and semantic message/field substrings rather than the entire rendered line.

### Decision B — import-time setup and `cache_logger_on_first_use=False`
A session-scoped autouse fixture is rejected because fixtures run after test-module collection/import, while `batch_processor.py` and many other modules bind loggers at module import. Import-time conftest setup gives the earliest repository-controlled pytest hook.

Caching is explicitly disabled in tests. Existing module-level `structlog.get_logger()` objects are lazy proxies; with first-use caching disabled, each call resolves against the active shared configuration rather than permanently retaining a wrapper assembled from stale/default settings. Production remains at `cache_logger_on_first_use=True` in `core/logging.py`.

### Capture-level contract
The shared harness does not force root logging to DEBUG or INFO. pytest/caplog thresholds retain normal stdlib semantics:
- WARNING and above are captured under the default threshold (covers the existing bug).
- Tests expecting INFO/DEBUG must use `caplog.set_level(logging.INFO)` or `with caplog.at_level(logging.INFO):` before emission.
- `filter_by_level` intentionally drops events below the effective stdlib level; that is not a routing failure.

## 4. Data Flow

```text
pytest startup
    |
    v
load tests/conftest.py
    |
    +--> _configure_structlog_for_tests() ------------------------------+
    |       LoggerFactory -> stdlib BoundLogger -> cache disabled       |
    |                                                                  |
    v                                                                  |
import test module -> import application module                         |
    |                        |                                          |
    |                        +--> module_logger = structlog.get_logger() |
    |                             (lazy proxy; no backend frozen)        |
    v                                                                  |
activate caplog handler + test-selected stdlib level                    |
    |                                                                  |
    v                                                                  |
code under test calls logger.info/warning(..., structured_fields=...) <-+
    |
    v
filter_by_level -- below threshold --> intentionally dropped --> empty caplog
    |
    | accepted
    v
add logger name/level -> positional/exception processing -> JSON render
    |
    v
structlog.stdlib.BoundLogger -> logging.Logger -> propagate to root
    |
    +--> pytest caplog handler -> LogRecord -> caplog.records/caplog.text
    |
    +--> processor/render/emission error -> test fails visibly (no swallowing)
```

There is no storage, network, database, vector database, or Docker path in this change.
## 5. State and Lifecycle Sequencing

| State | Trigger | Required side effect | Reversible? / next state |
|---|---|---|---|
| S0 pytest bootstrap | `.venv\Scripts\python.exe -m pytest ...` | pytest logging/capture plugin initializes | Yes; process exit. Next S1. |
| S1 shared conftest import | pytest establishes test root during collection | Python imports `tests/conftest.py` before test modules beneath `tests/` | Import cache persists for process. Next S2. |
| S2 structlog test-configured | module-level helper call | Global structlog defaults point at stdlib, deterministic processors, caching off; no handler added | Reconfigurable in-process, but this design has no reset. Next S3. |
| S3 test/application import | pytest imports test module, which imports `batch_processor` or creates a test logger | `structlog.get_logger()` returns a lazy proxy; no stale default logger is cached | Module remains imported. Next S4. |
| S4 caplog active | test setup injects `caplog`; test optionally sets level | pytest handler is attached and effective level selected | caplog restores handlers/levels after test. Next S5. |
| S5 event processed | code calls a structlog level method | Proxy resolves current configuration; processors run; accepted event becomes one stdlib `LogRecord` | Per-event. Next S6 or filtered terminal path. |
| S6 asserted | test inspects `caplog.records` / `caplog.text` | Semantic event, structured field, and stdlib level are observable | Test terminal state: pass/fail. |
| S7 test teardown | fixture teardown | caplog restores stdlib levels/handlers; structlog shared config intentionally remains for later tests | Next test returns to S3/S4; process exit is terminal. |

Critical ordering invariant: **S2 must precede S3, and S4 must precede S5.** An autouse fixture would place configuration after S3 and is therefore not accepted.

## 6. Error Paths and Failure Modes

| Failure | Detection | Expected handling/recovery | User/CI impact |
|---|---|---|---|
| Conftest config omitted or not loaded | Dedicated RED test has no matching `caplog.records`; event appears on captured stdout | Fix shared test-root/config loading, not the application test | Focused failure identifies harness regression. |
| Config runs only in a fixture | Import-time logger regression test fails under stale/cached behavior | Move call to conftest module import | Collection succeeds, assertion fails. |
| Logger cached against old/default config | Dedicated import-time probe or existing bug test has empty caplog | Keep `cache_logger_on_first_use=False`; do not override later | Potential suite-wide caplog failures. |
| Wrong logger factory | Event prints to stdout and no `LogRecord` exists | Use only `structlog.stdlib.LoggerFactory()` | Same signature as #159. |
| Processor chain lacks a terminal renderer or returns invalid shape | Structlog raises during the log call | Keep locked processor order and let error fail the test; do not swallow | Immediate focused-test error. |
| ProcessorFormatter wrapper used without matching formatter | Record may contain an event dict or formatter errors | Do not use `ProcessorFormatter.wrap_for_formatter`; terminal JSON renderer emits a string directly | Formatting/capture assertion failure. |
| INFO/DEBUG unexpectedly absent | Record below effective logger/root threshold | Set level in the individual test before logging; do not globally lower all tests | Local test failure, no production effect. |
| Duplicate records/output | More than one matching record in dedicated test | Ensure conftest does not call `basicConfig` or add handlers; assert exactly one probe record | Noisy/flaky assertions. |
| Structured value is not normally JSON serializable | Renderer fallback represents value, or logging call raises in focused coverage | Keep semantic assertions and structlog renderer defaults; do not add application coercion in #159 | Limited to test process. |
| Another test deliberately calls `structlog.configure()` | Later shared-routing checks could observe changed globals | Treat as test isolation violation; restore shared config in that test if introduced later | Order-dependent unit failures; full suite detects it. |
| Existing unrelated unit failures | Focused tests pass but suite fails | Report separately; do not broaden #159 without approval | PR must distinguish baseline failures. |
| Chroma/NumPy service failure | Docker/vector integration startup fails | Do not start or change it; unit tests use mocks | Explicitly out of scope and no effect on acceptance. |

## 7. Test Matrix

| Component/contract | Test type | RED/GREEN intent | What to mock | DI/capture boundary | Coverage target |
|---|---|---|---|---|---|
| Shared `tests/conftest.py` routing | Harness integration test in `tests/unit/test_logging_config.py` | **RED before config:** module-level named `structlog.get_logger(...)`; under `caplog.at_level(logging.INFO)`, emit unique event plus structured probe field; require exactly one matching record, INFO level, event text, and field text. No local configure call. GREEN only from shared conftest. | Nothing | pytest `caplog` is the injected capture boundary; stdlib root propagation is the interface | Proves shared routing, not merely batch behavior; import-time logger; INFO level mapping; kwargs rendered; no duplication. |
| Existing batch empty-input warning | Existing unit regression | Must change from empty caplog failure to pass with no edits to test/application | Existing processor fixtures already mock provider/vector DB | `caplog`; `BatchEmbeddingProcessor` constructor mocks external provider and vector DB | Canonical #159 acceptance and return value unchanged. |
| Threshold semantics | Included in shared routing test | INFO is captured only because test sets INFO | Nothing | `caplog.at_level(logging.INFO)` | Prevents a false pass based only on default WARNING. |
| Test-wide side effects | Unit-suite regression | All marked unit tests pass | Existing suite mocks | Existing project test boundaries | No global structlog config regressions. |
| Production logging isolation | Static diff/review | `core/logging.py` and app sources remain unchanged | N/A | File boundary | No runtime behavior change. |
| Chroma/vector infrastructure | Not run for #159 | Explicit exclusion | Existing batch tests use `Mock` | `vector_db` constructor argument | No Docker/network dependency introduced. |

The new harness test must not import a helper from conftest, invoke `structlog.configure()`, invoke `core.configure_logging()`, or merely call `BatchEmbeddingProcessor`. Its sole production dependency is structlog itself; that is what makes failure specifically diagnose missing shared routing.
## 8. Exact File Plan

### Add during implementation
- `tests/unit/test_logging_config.py` — dedicated shared-conftest RED/GREEN routing test.

### Modify during implementation
- `tests/conftest.py` — add only the private import-time test logging setup; retain existing fixtures.
- `JOURNAL.md` — append Week 9 evidence after implementation and validation.

### Read-only / explicitly unchanged
- `core/logging.py`
- `ingestion/embeddings/batch_processor.py`
- `tests/unit/test_batch_processor.py`
- `pyproject.toml`
- Dependencies/lock state, Docker/Chroma configuration, and all application files

### Architect-phase output
- `.pipeline/design-doc.md` — this document is the only file created or modified by the architecture task.

## 9. 2–5 Minute Implementation Tasks

All commands are PowerShell-compatible and run from the repository root. They deliberately use the virtualenv Python rather than `make`, whose configured shell is Git Bash; project-equivalent commands are listed in validation.

### Task 1 (3 min): Add the dedicated RED harness test
- **Files:** add `tests/unit/test_logging_config.py`.
- **Code intent:** import `logging`, `structlog`, and `pytest`; create a uniquely named logger at module scope; add one `@pytest.mark.unit` test using `caplog.at_level(logging.INFO)`; emit a unique event with a unique structured field; select matching records and assert exactly one, `record.levelno == logging.INFO`, and semantic event/field presence in `record.getMessage()`.
- **Do not:** configure structlog in this file or call application logging configuration.
- **Verify RED:** `.venv\Scripts\python.exe -m pytest tests\unit\test_logging_config.py -q`
- **Expected before Task 2:** failure because `caplog.records` has no matching record and pytest captures stdout instead.
- **Depends on:** none.

### Task 2 (4 min): Implement shared import-time routing
- **Files:** modify `tests/conftest.py`.
- **Code intent:** add the private typed helper and exact processor/factory/cache configuration locked in Section 3; invoke it at module import before fixture definitions; do not add a fixture, stdlib handler, `basicConfig`, environment/settings import, or production-config import.
- **Verify GREEN:** `.venv\Scripts\python.exe -m pytest tests\unit\test_logging_config.py -q`
- **Expected:** one passing test and no duplicate probe record.
- **Depends on:** Task 1.

### Task 3 (2 min): Verify the canonical #159 regression
- **Files:** no edits.
- **Code intent:** run the existing warning/empty-list test unchanged so success cannot be attributed to weakening its assertion.
- **Verify:** `.venv\Scripts\python.exe -m pytest tests\unit\test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -q`
- **Expected:** pass; no Docker services required.
- **Depends on:** Task 2.

### Task 4 (3 min): Run focused-file regression
- **Files:** no edits unless Task 2 violates the locked design.
- **Code intent:** run both the new routing contract and all batch processor behaviors.
- **Verify:** `.venv\Scripts\python.exe -m pytest tests\unit\test_logging_config.py tests\unit\test_batch_processor.py -q`
- **Depends on:** Task 3.

### Task 5 (5 min): Run unit suite
- **Files:** no edits unless an issue caused by this configuration is found; architecture changes require re-approval.
- **Code intent:** detect process-global config regressions and order-dependent behavior.
- **Verify:** `.venv\Scripts\python.exe -m pytest tests\unit -v -m unit`
- **Make equivalent:** `make test-unit` when GNU Make/Git Bash is available.
- **Depends on:** Task 4.

### Task 6 (5 min): Run quality gates
- **Files:** review-only; do not use formatting as an excuse for unrelated repository edits.
- **Verify lint:** `.venv\Scripts\python.exe -m ruff check tests\conftest.py tests\unit\test_logging_config.py`
- **Verify formatting without mutation:** `.venv\Scripts\python.exe -m black --check tests\conftest.py tests\unit\test_logging_config.py`
- **Verify project typecheck:** `.venv\Scripts\python.exe -m mypy api core ingestion rag agent safety`
- **Optional project equivalents:** `make lint`, `make typecheck`; avoid `make format` for validation because it rewrites files. The CONTRIBUTING combined equivalent is `make check`, but inspect/revert unrelated formatter changes if used.
- **Depends on:** Task 5.

### Task 7 (4 min): Record Week 9 evidence
- **Files:** modify `JOURNAL.md` only.
- **Code intent:** append the exact Week 9 fields in Section 12 with real commit/PR URLs and observed command outcomes; never claim an unchecked command passed.
- **Verify:** `.venv\Scripts\python.exe -m ruff check tests\conftest.py tests\unit\test_logging_config.py` and manually inspect `git diff -- JOURNAL.md`.
- **Depends on:** Tasks 5–6 and available links.

### Task 8 (3 min): Final diff and PR readiness
- **Files:** no new edits expected.
- **Code intent:** ensure only `.pipeline/design-doc.md`, `tests/conftest.py`, `tests/unit/test_logging_config.py`, and `JOURNAL.md` are in the issue diff; confirm protected source files and dependency files are unchanged; populate the PR template per Section 13.
- **Verify:** `git diff --name-only main...HEAD` and `git diff -- core\logging.py ingestion\embeddings\batch_processor.py tests\unit\test_batch_processor.py pyproject.toml`
- **Depends on:** Task 7.
## 10. Validation Plan and Acceptance Gates

Run in this order so failures localize cleanly:

1. **RED evidence:** new harness test fails before shared configuration, specifically with no matching caplog record.
2. **Focused GREEN:** new harness test passes after conftest change.
3. **Issue acceptance:** existing empty-chunks test passes unchanged.
4. **Focused regression:** new logging test plus full batch-processor file pass.
5. **Unit regression:** `.venv\Scripts\python.exe -m pytest tests\unit -v -m unit` passes.
6. **Ruff:** focused changed Python files pass.
7. **Black:** focused changed Python files pass under `--check`.
8. **Mypy:** existing application target set passes; tests are not in the project's Makefile typecheck target.
9. **Diff audit:** no application, dependency, pytest settings, or chroma/numpy files changed.

Acceptance requires the observed RED result and all GREEN gates above. Integration tests are not required for this isolated test-harness change; if they are not run, the PR checkbox remains unchecked with an explicit “not run/not required; no service path changed” note. A baseline failure unrelated to #159 must be documented rather than silently fixed or misreported.

## 11. Security and Performance Considerations

### Security
- No auth, authorization, user input, secrets, network, persistence, or production trust boundary changes.
- Structured test fields must use synthetic probe values and must not log `.env` contents or credentials.
- Deterministic JSON rendering exists only in pytest; it does not change production exposure or redaction.
- Global mutable structlog configuration is confined to the test process.

### Performance
- Disabling first-use caching adds negligible per-log-call wrapper assembly in tests only; correctness and isolation take priority.
- `filter_by_level` drops lower-level work early.
- No extra handlers prevents duplicate processing and memory growth.
- One small regression test and import-time configuration add negligible suite time.
- Production retains its existing cached logger behavior.

## 12. Commit Plan and JOURNAL Week 9

### Commit plan
Do not commit the intentionally broken RED state by itself. Capture its console output locally, then make it GREEN and commit coherent checkpoints:

1. `docs(ingestion): lock issue 159 logging test design`  
   Files: `.pipeline/design-doc.md` only.
2. `test(ingestion): route structlog logs through caplog`  
   Files: `tests/conftest.py`, `tests/unit/test_logging_config.py`. Body should state the RED observation, why setup is import-time/cache-free, and `Fixes #159` or leave closure to the PR (do not duplicate an incorrect issue link).
3. `docs(ingestion): record issue 159 implementation results`  
   File: `JOURNAL.md` only, after links/evidence exist.

Do not amend published commits unless explicitly requested; do not push directly to `main`.

### Exact Week 9 section/fields to append to `JOURNAL.md`

```markdown
## Week 9 — Implementation, validation & pull request

**Implementation commit link:** <real commit URL>

**Pull request link:** <real PR URL>

**Implementation summary:** <test-only conftest routing, import-time ordering, caching disabled, dedicated regression test>

**Resolved design questions:** Dedicated test configuration was chosen instead of `core.configure_logging()`; `cache_logger_on_first_use=False` is used in tests so import-time lazy loggers resolve the active test configuration. Production logging remains unchanged.

**RED test evidence:** <exact command and concise pre-fix failure: no matching caplog record / stdout-only event>

**GREEN test evidence:** <exact focused, canonical, unit-suite, ruff, black --check, and mypy commands with outcomes>

**Files changed:** `.pipeline/design-doc.md`, `tests/conftest.py`, `tests/unit/test_logging_config.py`, `JOURNAL.md`.

**Scope confirmation:** No application files, dependencies, pytest settings, or chromadb/numpy infrastructure were changed.

**Blockers or follow-ups:** <none, or truthful unrelated baseline failures>; chromadb/numpy remains a separate infrastructure issue.

**Walkthrough video (recommended):** <URL or “not recorded”>
```

Use actual evidence; do not paste placeholders into the final journal update.

## 13. Pull Request Template Content Requirements

Populate `.github/PULL_REQUEST_TEMPLATE.md` completely:

- **Summary:** One paragraph: pytest did not route unconfigured structlog events through stdlib, so caplog assertions were empty; this PR adds deterministic, import-time, test-only routing and a dedicated shared-harness regression test without changing production logging.
- **Issue:** `Closes #159`.
- **Changes:** bullets for (1) shared conftest stdlib logger factory/processors, (2) cache disabled to support import-time logger proxies, (3) dedicated conftest-routing regression test, and (4) Week 9 journal evidence. Explicitly say no application logging change.
- **Testing:** check Unit tests, Linter, Type checker, and New/updated tests only when those commands actually pass. Add Black `--check` evidence even though the template has no formatter checkbox. Leave Integration tests unchecked if not run and explain they are not required because the change has no service boundary.
- **Screenshots / Demo:** `N/A — backend test-harness change`; optionally link the walkthrough video.
- **Notes for Reviewers:** ask reviewers to focus on import-time ordering, `cache_logger_on_first_use=False`, absence of handlers/`basicConfig`, and the fact the new test proves shared conftest routing. State that the chromadb/NumPy issue is known, unrelated, and deliberately untouched.

## 14. Architecture Lock Checklist

- [x] Scope is held to #159.
- [x] Six forcing questions are answered.
- [x] Dedicated test configuration is selected over production configuration reuse.
- [x] Import-time setup and `cache_logger_on_first_use=False` are locked.
- [x] Data flow, lifecycle ordering, failure paths, and capture levels are defined.
- [x] The test matrix includes an independent shared-conftest RED test.
- [x] Exact file boundaries, short tasks, Windows commands, validation, commits, journal fields, and PR content are defined.
- [x] Chroma/NumPy infrastructure remains untouched.

Implementation must follow this document. Any change to the logger factory, processor/renderer strategy, initialization timing, cache policy, source-file boundary, or infrastructure scope requires explicit human re-approval.