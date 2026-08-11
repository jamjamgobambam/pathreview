# Solution Plan

## Issue

Add support for ingesting a portfolio website URL

https://github.com/ascherj/pathreview/issues/11

---

## Understand

Currently users can upload resumes and GitHub repositories, but not portfolio websites.

The application does not have:

- a portfolio URL field
- a web parser
- pipeline support for websites

The goal is to fetch a portfolio website, extract useful text, and send it through the existing ingestion pipeline.

---

## Map

Files I expect to modify:

- api/schemas/profile.py
- ingestion/pipeline.py
- ingestion/parsers/web_parser.py

I will also look for any tests related to ingestion.

---

## Plan

1. Add a portfolio URL field to the profile schema.
2. Create `web_parser.py`.
3. Fetch the webpage.
4. Extract useful text such as bio and projects.
5. Connect the parser to the ingestion pipeline.
6. Add tests.

---

## Inputs & Outputs

### Input

A portfolio website URL.

### Output

Extracted text added to the ingestion pipeline and stored in the vector database.

---

## Risks & Unknowns

- Different websites have different HTML.
- Some websites may not load.
- Some websites may redirect.
- Need to safely fetch user-provided URLs.

---

## Edge Cases

- Invalid URL
- Timeout
- Empty page
- Redirects
- 404 page
- Missing project descriptions