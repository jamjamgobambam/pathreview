# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The safety layer runs every piece of user text through `PIIScrubber` in
`safety/pii_scrubber.py` so that personal details from uploaded resumes never
reach LLM prompts or stored review output. The US phone regex there only
accepts dots or dashes between digit groups, so the most common written
format — `(555) 123-4567`, with a space after the closing paren — passes
through both `scrub()` and `detect()` completely unredacted. I reproduced it
locally: 4 of the tests named in the issue fail in
`tests/unit/test_pii_scrubber.py` (plus a 5th failure caused by an unrelated
street-address false-positive bug). A successful fix makes the pattern accept
space separators (including formats like `+1 555 123 4567`) and consume the
opening paren, so the whole number is replaced by `[REDACTED]` and all four
tests pass without breaking the twenty that currently pass.

**Branch name:** `fix/146-pii-scrubber-paren-phone`

**Setup confirmation:** [ ] App runs locally at localhost:5173
*Status: venv + Python deps, frontend `npm install`, and `.env` (mock LLM
provider) are done, and the unit-test loop runs in under a second. Full
`make setup`/`make run` is still blocked: my user isn't in the `docker` group
and the compose plugin is missing, so postgres/redis/chroma can't start yet.
Fix queued: `sudo apt install docker-compose-v2 && sudo usermod -aG docker
$USER`, re-login, then `docker compose up -d && make setup && make run`.*

**Cohort ledger:** [ ] Issue added to cohort ledger

### Selection notes — "Is this right for me?" checklist

- **Scoped small enough?** Yes — one regex constant in one file
  (`safety/pii_scrubber.py`), one test file, estimated 1–3 hours in the
  issue manifest.
- **Can I reproduce it?** Yes — already did; the issue even names the exact
  failing tests, so "done" is unambiguous.
- **Can I develop and verify it locally?** Yes — the scrubber is pure Python
  with no DB/LLM dependency, so the docker blocker above doesn't slow this
  issue down at all.
- **Do I understand the domain?** Yes — it's regex plus a clear behavioral
  contract (`scrub()` replaces, `detect()` reports), both easy to reason
  about and test.
- **Does it matter?** Yes — PII scrubbing is the safety layer's core job,
  and this bug leaks the single most common US phone format from real
  resumes.
- **Risk noted:** several classmates have also claimed #146 (parallel work
  is normal in this cohort since everyone submits from their own fork), so
  my PR needs to stand on its own quality, not on being first.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/DeDeMouse/pathreview/commit/63cfafbc462949089bde133c027d2481db2ccc08

**Reproduction summary:**
On a clean checkout I ran the scrubber's unit suite and the issue's REPL
snippet: the four issue-named tests fail, and `(555) 123-4567` /
`+1 555 123 4567` pass through `scrub()` unchanged with `detect()` returning
`[]`, while dashed/dotted formats redact correctly — so the bug is isolated
to space/paren handling in the `phone_us` regex (full transcript in PLAN.md
under "Understand").

**PLAN.md link:** https://github.com/DeDeMouse/pathreview/blob/fix/146-pii-scrubber-paren-phone/PLAN.md

**Walkthrough video (recommended):** _not recorded yet — will add before
asking for early feedback_

**Blockers or open questions:**
`test_mixed_pii_and_text` fails from a *separate* bug (the `street_address`
pattern + `IGNORECASE` matches the "pl" in "applications", swallowing
"Python"), so it will still be red after my phone fix. Open question for
Week 9: fix it in the same PR to keep the suite green, or file it as its own
issue and note the pre-existing failure in the PR description? Currently
leaning toward filing it separately. (Docker group fix is still pending on
my machine, but this issue's dev loop is pure Python and unaffected.)
