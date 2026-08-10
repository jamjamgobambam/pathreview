# Prompt Injection Research — Issue #71

Research notes for the red-teaming test suite (issue #71). Feeds `tests/fixtures/injection_attempts/`
and `tests/security/test_prompt_injection.py`. See [PLAN.md](../PLAN.md) for the overall solution plan.

## Threat model

The app ingests resumes (external documents), so **indirect injection is the primary real threat
surface** — instructions hidden inside document content the LLM is designed to trust, not just
literal text typed by a user. `safety/prompt_defense.py` currently only tests direct, inline text
patterns via regex. Note also: nothing in the app currently calls `PromptDefense` from the ingestion
path, so "blocked" in test assertions currently means "the function returns `True`," not that
ingestion actually rejects the input — that gap should be flagged, not silently assumed fixed by
this test suite.

## OWASP LLM01:2025 classification

- **Direct injection** — attacker-controlled text goes straight into the prompt.
- **Indirect injection** — malicious instructions arrive via retrieved/trusted content (e.g. resume
  file, linked GitHub README, fetched URL). Called out as the most widely exploited vulnerability in
  production LLM deployments today.

## Technique coverage vs. `safety/prompt_defense.py`

| Technique | Covered today? | Notes |
|---|---|---|
| Role-switching (`System:`/`Human:`/`Assistant:`) | Yes | Regex-based, case-insensitive |
| Separator/delimiter breakout (`---`) | Yes | Only dash-style; `###`, `<<<`, `===`, XML tags not covered |
| Template/logic injection (`{{ }}`, `{% %}`) | Yes | |
| Instruction-override keywords (ignore/forget/disregard/override) | Yes | Keyword-based — bypassable via synonyms ("disavow", "nullify") or rephrasing |
| Code-execution calls (`execute(`, `run(`, `eval(`) | Yes | |
| DAN / persona role-play jailbreaks | No | No pattern targets persona-hijacking language |
| Payload splitting (benign fragments that combine into a malicious instruction) | No | Defeats regex-per-string matching by design — needs a different detection strategy |
| Indirect injection via document content (hidden instructions inside resume text/metadata) | No | Actual attack surface per PLAN.md — no fixtures or tests simulate a malicious resume |
| Obfuscation / encoding (base64, unicode homoglyphs, zero-width chars, leetspeak) | No | Regexes match literal ASCII keywords; encoded payloads pass through undetected |
| Multi-turn / context-stuffing | No | Confirm whether app is single-turn; if so, lower priority |
| Prompt leaking / exfiltration ("repeat your system prompt") | No | Different goal than override — extracts the system prompt rather than replacing it |
| Alternative delimiter/markup styles (`###`, `<<<SYS>>>`, markdown fenced "system" blocks, `<system>` tags) | No | Only `{{ }}`/`{% %}`/`<>` are stripped |
| Whitespace/invisible-character evasion (zero-width spaces splitting trigger keywords) | No | `\s*` in the regexes handles ordinary spacing but not zero-width/non-breaking chars |

## Concrete deliverables (issue acceptance criteria)

| Requirement | Status |
|---|---|
| Curated set of known prompt injection attacks | Not started — this document is prep, not fixtures |
| `tests/fixtures/injection_attempts/` | Doesn't exist yet |
| `tests/security/test_prompt_injection.py` | Empty file |
| Test suite verifies all attacks are blocked | N/A yet — and "blocked" should be defined against `PromptDefense`, with the ingestion-wiring gap noted above called out explicitly rather than assumed away |
| Runs in CI on every PR touching `safety/` | `.github/workflows/ci.yml` has no job for `tests/security` and no path-filtering at all — every job currently runs on every PR regardless of what changed |

Remaining sub-tasks:
1. Build the fixture corpus in `tests/fixtures/injection_attempts/` — one or more payloads per gap
   row above.
2. Write `test_prompt_injection.py` to load fixtures and assert `PromptDefense.is_injection_attempt()`
   returns `True` for each, plus the two edge cases from PLAN.md: a PR that doesn't touch `safety/`,
   and a PR that modifies or removes the security tests themselves.
3. Add a CI job (or path filter) so the suite actually gates PRs touching `safety/`.

## Sources

- [LLM01:2025 Prompt Injection - OWASP Gen AI Security Project](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [OWASP LLM Top 10 (2026): The 10 Critical LLM Security Risks Explained | Repello AI](https://repello.ai/blog/owasp-llm-top-10-2026)
- [Fooling AI Agents: Web-Based Indirect Prompt Injection Observed in the Wild](https://unit42.paloaltonetworks.com/ai-agent-prompt-injection/)
- [Prompt Injection vs Jailbreaking: What's the Difference? | Promptfoo](https://www.promptfoo.dev/blog/jailbreaking-vs-prompt-injection/)
- [Prompt Injection & Jailbreak Techniques — Comprehensive Reference](https://gist.github.com/kibotu/c06f54d6fbc4705e886a50fb2e59e6ae)
