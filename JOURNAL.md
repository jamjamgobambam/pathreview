\## Week 7 — Issue Selection



\*\*Issue link:\*\* https://github.com/ascherj/pathreview/issues/36



\*\*Issue title:\*\* Architecture doc doesn't explain the hybrid retrieval scoring formula



\*\*Tier:\*\* \[x] Tier 1  \[ ] Tier 2  \[ ] Tier 3



\*\*Problem summary:\*\*

The architecture documentation explains that hybrid retrieval combines vector similarity and keyword relevance, but it does not show how those scores are mathematically combined. It also does not identify the default weights used by the system, making the retrieval process harder for contributors to understand or reproduce. This issue affects `docs/ARCHITECTURE.md` and does not require changing the application's runtime behavior. A successful fix will document the scoring formula, state the default weights, and include a clear worked example.



\*\*Selection reasoning:\*\*

I selected this issue because it is a Tier 1 task with a clearly defined and manageable scope. The work is limited to one documentation file, and I can inspect the existing retrieval code to confirm the formula and weights before writing the explanation. It does not require redesigning the application or modifying several unrelated modules. This makes it appropriate for my current experience while still requiring me to understand how the hybrid retrieval system works.



\*\*Branch name:\*\* `docs/36-hybrid-retrieval-scoring`



\*\*Setup confirmation:\*\* \[x] App runs locally at localhost:5173



\*\*Cohort ledger:\*\* \[x] Issue added to cohort ledger

