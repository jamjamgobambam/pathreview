\## Week 7 — Issue selection



\*\*Issue link:\*\* https://github.com/ascherj/pathreview/issues/38



\*\*Issue title:\*\* \[Add an integration test that runs the full RAG pipeline against a mock LLM

]



\*\*Tier:\*\* \[ ] Tier 1  \[X] Tier 2  \[ ] Tier 3



\*\*Problem summary:\*\*

\[3–5 sentences, your own words]

The Integration Tests is missing for each component of the RAG Pipeline. It needs to be developed as there is currently no integration testing. 

The full query/pipeline is: retrieval → reranking → generation → parsing
The goal is to add one to the tests/integration/test\_rag\_pipeline.py file



\*\*Branch name:\*\* test/38-integration-test\_rag-pipeline



\*\*Setup confirmation:\*\* \[x] App runs locally at localhost:5173



\*\*Cohort ledger:\*\* \[X] Issue added to cohort ledger: Added on Row 70



\*\*Scope and Reasoning Checklist:\*\*

Work through the checklist and note your scope reasoning in your selection notes



\*Part 1 — Understanding the Issue\* \[X]

The issue asks for a new integration test that exercises the full RAG pipeline

which is: retrieval → reranking → generation → parsing. It needs to use the mock LLM

provider instead of a live API call.

The file tests/integration/test\_rag\_pipeline.py needs to be developed as currently only the initializer (\_\_init\_\_.py) is present.

Right now the repo only has unit tests for each RAG component in isolation, so

there's no test verifying the components actually work together correctly.

I've opened those app and modules. I have confirmed the function/class names I'll need to

import and mock 



\*Part 2 — Tier Fit\* \[X]

I selected a Tier 2, since it requires understanding how retrieval, reranking,

generation, and parsing interact as a pipeline rather than editing a single

isolated file. It's not too complex like an infrastructure change but not simple like a documentation update

I have contributed once to an first open-source contribution but it has been a while so I believe a Tier 2 is a reasonable stretch for me right now.



\*Part 3 — Codebase Readiness\* \[X]

I've located the existing unit tests for retrieval, reranking, generation,

and parsing. I understand the related folders for rag (evaluator, generator, and retriever) and related tests in conftest and tests/unit. These will be important for understanding the context when trying to implement test/integration/test\_rag\_pipeline.py



\*Part 4 — Scope and Time\* \[X]

I checked the issue comments and the cohort ledger's Claims count for issue

\#38. I am estimating 4-6 hours on this Tier 2 issue.

Given this is a Tier 2 issue, I'm estimating roughly 8–12 hours: time to trace

the pipeline's actual call chain, wire up the mock LLM, write realistic

fixtures for each stage, and assert on the final parsed output.

I've checked for "blockers" that may prevent me from completing this feature additioni and found none. 

