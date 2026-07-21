# JOURNAL

## Week 7 — Issue selection

**Issue link:**
https://github.com/ascherj/pathreview/issues/11

**Issue title:**
Add support for ingesting a portfolio website URL

**Tier:**
☑ Tier 2

**Problem summary:**

Currently, PathReview supports ingesting resumes and GitHub repositories, but it cannot ingest content from a user's personal portfolio website. This feature will allow users to submit a portfolio URL, fetch the webpage, extract relevant information such as the user's bio and project descriptions, and send the extracted content through the existing ingestion pipeline. The implementation will involve creating a web parser, updating the ingestion pipeline, and extending the API schema to accept portfolio URLs.

**Branch name:**
feat/11-portfolio-url-ingestion

**Setup confirmation:**
☑ App runs locally at localhost:5173

**Cohort ledger:**
☑ Issue added to cohort ledger

### Issue selection reasoning

I chose this Tier 2 issue because it matches my experience building portfolio websites while giving me the opportunity to understand a larger AI codebase. The scope is manageable, but it also requires working across multiple modules, including the API layer, ingestion pipeline, and parser implementation. I believe it is a good balance between learning new concepts and applying my existing backend and web development skills.