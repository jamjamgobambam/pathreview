## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings
 #151

**Tier:** [x] Tier 1

**Problem summary:**
The regex patterns in bias_detector.py is based on deterministic word-by-word matching (such as using self-taught|online\s+course) to detect if the feedback dismisses the porfolio because online courses are unqualify. Other factors include college background, internship experience, project maturity, age, demographics. 

For the users, this is problematic because their portfolios are judge based on the title and popularity of the organizations they worked with, rather than their actual accomplishment and learning and skills. The feedback does not touch on any things that application could change (for exmaple, demographics) and this exarcebate the discrimination/ class difference between proviledged and unpriviledge communities.

The bias detection should be able to detect if the AI feedback is reasoning based on description of the experience, instead of merely the title.

Original logic:
```
    # Genuinely dismissive phrases about educational background
    DISMISSIVE_PATTERNS = [
        r"(?:bootcamp|self-taught|online\s+course)\s+(?:education|training)\s+is\s+(?:insufficient|inadequate|lacks)",
        r"(?:bootcamp|self-taught)\s+(?:graduates?|developers?)\s+(?:lack|missing)\s+(?:rigor|fundamentals|proper\s+training)",
        r"(?:bootcamp|coding\s+bootcamp)\s+(?:doesn't|does\s+not)\s+prepare\s+(?:you|developers?)",
        r"(?:self-taught|bootcamp)\s+is\s+(?:not|never)\s+(?:equal|comparable)\s+to\s+(?:university|traditional|formal)",
    ]

    # Demographic assumptions (about age, background, identity)
    DEMOGRAPHIC_PATTERNS = [
        r"(?:young|old|aged)\s+(?:person|developer|programmer)\s+(?:can't|cannot|won't|will\s+not)",
        r"(?:person\s+from|coming\s+from)\s+(?:poor|rich|working[\s-]?class)",
        r"(?:immigrant|international|foreign)\s+developers?.*(?:can't|cannot|won't|struggle)",
    ]
```

**"Is this right for me?" checklist**
This is a tier 1 issue, the fix only requires change the BiasDetector logic in `safety.bias_detector` and does not have interconnected logic to other files -> this is the right scope for beginner

**Branch name:** fix/151-fix-bias-detection

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger

----------------------------------------------------------------------------------
## Week 8 — Reproduction & solution planning

**Reproduction commit link:** The reproduction steps are recorded in the Reproduction summary section below

**Reproduction summary:**
Reproduced issue #151 locally.

Steps:
1. Ran:
   pytest tests/unit/test_bias_detector.py

2. Observed:
   9 failed, 23 passed

3. Example reproduction:
   ```python
   from safety.bias_detector import BiasDetector

   BiasDetector.detect_bias(
       "The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education"
   )
   -> This returns (False, '') which is an expected failure because we fail to detect the bias in this AI portfolio review

**PLAN.md link:** https://github.com/MeeTrannn/pathreview/blob/fix/151-fix-bias-detection/PLAN.md

**Blockers or open questions:**
Resolved going into Week 9: decided regex expansion is the right approach for this Tier 1 issue; LLM-based detection is out of scope.

----------------------------------------------------------------------------------
## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented Steps 0–6 from PLAN.md on branch `fix/151-fix-bias-detection`:

1. Added reusable regex fragments to `BiasDetector` (`_EDU_SOURCE`, `_ROLE`, `_DISMISSAL_VERB`, `_DEMOGRAPHIC_ROLE`, `_SOCIOECONOMIC_BACKGROUND`)
2. Refactored `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` to use those fragments and catch natural phrasing variations (optional `is`, plural roles, dismissal verbs like `can't`, `coding bootcamp` prefix, bootcamp vs formal CS comparison)
3. All 9 previously failing tests now pass; all 23 regression tests still pass
4. Added `test_bootcamp_formal_cs_comparison_detected` for the issue reproduction example

**Next steps:**
- Run final self-review (`make check`, `make test-unit`)
- Commit changes with conventional commit messages
- Open PR with pre-existing failure documentation

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/982

**Branch:** `fix/151-fix-bias-detection`

**What you built:**
Broadened the regex patterns in `BiasDetector` so they catch natural phrasing variations of educational-background dismissal and demographic assumptions — not just near-exact phrase sequences. Introduced reusable regex fragments to keep patterns maintainable, and refactored both `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` to handle plurals, optional words, and causal phrasing like "bootcamp attendance means inadequate training."

**Tests added or updated:**
- `tests/unit/test_bias_detector.py` — added `test_bootcamp_formal_cs_comparison_detected` covering the issue reproduction example ("only attended a bootcamp… lacks the rigor of a formal CS education"). The 9 previously failing tests and 23 existing regression tests validate all pattern changes with no new tests needed for fixes already covered by the existing suite.

**Self-review confirmation:** [x] make check passes (no new failures — 182 pre-existing lint errors repo-wide)  [x] make test-unit passes (33/33 bias detector tests pass; no new repo-wide failures)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback
"One area to focus on going forward is the maintainability of regex-based detection. You introduced reusable fragments like _EDU_SOURCE, _ROLE, and _DISMISSAL_VERB, which is a good instinct for reducing duplication. However, as pattern sets grow, raw regex strings embedded in class variables become increasingly hard to read and debug. Consider whether a small helper method that builds patterns from structured data (e.g., a list of tuples describing subject, verb, and object groups) would make it easier for the next contributor to extend the detector without needing to mentally parse complex regex. This kind of thinking — "how easy is it for someone else to modify this six months from now?" — is one of the most valuable habits you can build. "

**Summary of feedback:**
The review mainly is on the maintainability of regex-based detection.

**How you'd responde:**
I just refactor the code so that I keep an extensible list of synonum (for exampe, course, class, module, etc) as a natural language list and create regex patterns later from that list so that review can just extend the synonym list without parsing the plex regex.

### Reflection

**What was harder than you expected?**
What surprised me most is that I only needed to fix the code to address the remaining failing test cases — without necessarily solving the whole bias detection problem. The issue was scoped to making the existing regex patterns catch natural phrasing variations, not building a complete bias detection system.

**What did you learn about working in a large codebase?**
I need to be careful not to touch other people's code or introduce new errors. Changes should stay within the issue's scope, and I need to document pre-existing failures so reviewers know my PR didn't make things worse.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful when writing code based on clear instructions — once I knew which files the error was in, which file/function to change, and what the tests expected. It was less helpful for deciding scope (e.g., regex vs. LLM) and understanding what the issue was actually asking for vs. what would be ideal in production.

**What would you do differently if you started over?**
Start by reading the failing tests before planning, so I know exactly which cases my code needs to fix. That would also help me clarify issue scope early — whether I should focus on fixing only the remaining failing tests or try to build a full bias detection solution.

**What are you most proud of from this module?**
Opening my first pull request and getting all 33 bias detector tests passing on a real open-source codebase.
