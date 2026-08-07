# Development Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/11

**Issue title:** Add support for ingesting a portfolio website URL

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview currently collects user information from sources like GitHub repositories and resumes, but it does not support personal portfolio websites. This issue adds the ability for users to provide a portfolio URL, allowing the ingestion pipeline to fetch and extract useful content such as biographies and project descriptions. The extracted information should be processed and stored in the vector database alongside existing profile data so it can improve future AI-generated reviews.

**Selection reasoning:**
I selected this Tier 2 issue because it requires understanding multiple parts of the application, including API schemas, ingestion pipelines, and document parsing. This issue aligns with my goal of learning how AI systems collect, process, and use user data in real-world applications. I also see this issue as an opportunity to develop a troubleshooting mindset by handling edge cases such as invalid URLs, missing webpage content, and extraction failures. Understanding how users submit data through APIs and how the backend processes that information connects well with solution engineering responsibilities.


**Branch name:** feature/11-portfolio-url-ingestion

**Setup confirmation:** [x] App runs locally at localhost:5173 

**Setup notes:**
Used Docker Compose to start the required services (PostgreSQL, Redis, and ChromaDB). Resolved a ChromaDB startup issue caused by a NumPy version incompatibility by pinning NumPy to version 1.26.4. After restarting the containers, completed the project setup with `make setup` and verified the application by running `make run` and logging in successfully with the seeded test account.

**Cohort ledger:** [x] Issue added to cohort ledger




## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Vig270/pathreview/commit/7597f54

**Reproduction summary:**
I reproduced the issue by running PathReview locally with Docker Compose and submitting a review request containing a portfolio URL. The application accepts and stores the URL, but the ingestion pipeline currently does not fetch or process portfolio website content.

**PLAN.md link:** https://github.com/Vig270/pathreview/blob/feature/11-portfolio-url-ingestion/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
Need to determine the best approach for fetching and parsing different portfolio website structures.



## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the portfolio URL ingestion feature for issue #11. Created a new `PortfolioParser` to fetch portfolio webpage content, extract readable text, and return structured metadata. Integrated the parser into the ingestion pipeline and added unit tests for portfolio parsing behavior.

**Next steps:**
Run project checks (`make check` and `make test-unit`), review changes, create a pull request, and request peer/mentor feedback.

**Blockers:**
The full test suite contains existing failures unrelated to my portfolio ingestion changes. The new portfolio parser tests pass successfully.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/522

**Branch:** feature/11-portfolio-url-ingestion

**What you built:**
Added portfolio URL ingestion support by creating a `PortfolioParser` that fetches webpage content, extracts readable text, and integrates with the existing ingestion pipeline. The extracted portfolio content can now be chunked and processed alongside other profile sources.

**Tests added or updated:**
Added `tests/unit/test_portfolio_parser.py`.

Tests cover:
- Successful portfolio webpage text extraction using mocked HTTP responses
- Invalid input handling for unsupported content types

**Self-review confirmation:**
[ ] make check passes  
[ ] make test-unit passes  

**Notes:**
Verified the new portfolio parser functionality using `pytest tests/unit/test_portfolio_parser.py`, which passes successfully. Full project checks (`make check`, `make test-unit`, and `make typecheck`) reported failures unrelated to the portfolio ingestion implementation.







## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback has been received yet. The pull request is open and awaiting review.

**How you responded:**


---

### Reflection

**What was harder than you expected?**
The hardest part was debugging and setting up Docker. Thankfully, I had previous experience using Docker in CodePath CYB 101, so I already had it installed and understood the basics. Even so, I still had to troubleshoot setup issues and plan a roadmap before implementing my changes. I chose Issue #11 because it aligns with my long-term career goal of becoming a Solution Engineer or a similar customer-facing technical role. Working on this issue also helped me become more comfortable reading and understanding an unfamiliar codebase.

**What did you learn about working in a large codebase?**
I learned that contributing to a large codebase requires understanding how different files connect rather than focusing on a single file. Before making changes, I needed to read the existing implementation, understand the project structure, and identify which files were responsible for specific functionality. Following the existing coding style and project organization was just as important as writing the new code itself.

**How did AI tools help — and where did they fall short?**
AI helped me understand unfamiliar parts of the codebase, explain how the ingestion pipeline worked, debug Git commands, write unit tests, and learn the GitHub pull request workflow. It was especially useful for explaining concepts and suggesting approaches when I was unsure where to begin. However, AI could not replace reading the project's code or understanding the repository's structure. I still needed to verify suggestions, debug issues myself, and determine which problems were caused by my changes versus existing issues in the project.

**What would you do differently if you started over?**
If I started over, I would spend more time exploring the codebase before writing any code so I could better understand how the different components interact. I would also make smaller, more frequent commits and spend more time understanding the project's testing process before implementing my changes.

**What are you most proud of from this module?**
I am most proud of learning the GitHub workflow. Before this module, I mostly used GitHub to upload projects from VS Code or download ZIP files. Through this project, I learned how to clone repositories, create branches, commit changes, push to a fork, and open a pull request. Most importantly, this was my first contribution to an open-source project, and it gave me confidence in working with a large, unfamiliar codebase. This experience has been incredibly rewarding, and I am proud of what I accomplished. It is something I would be excited to include on my resume and potentially share in a LinkedIn post as an important milestone in my learning journey.