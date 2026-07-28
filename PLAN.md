## Solution plan

**Issue:** API docs don't include example `curl` commands [https://github.com/ascherj/pathreview/issues/117]

### Understand
The root issue of this problem is a lack in documentation. The behaviour that is expected here is that once you open `docs/API.md`, `curl` commands should be listed to help users setting up the program for the first time. However, no such information exists in `docs/API.md`.

### Map
I only expect to touch `docs/API.md` for this change.

### Plan
1) Understand the stucture of the file.

2) Document the necessary `curl` commands needed.

3) Add the `curl` commands to `docs/API.md` in an understandable way to new users.

### Inputs & outputs
This change shouldn't have and inputs or outputs. It's a documentation change.

### Risks & unknowns
There shouldn't be any risks involved. The only thing I am changing is a .md file, as this is a documentation issue, not a code one.

### Edge cases
There shouldn't be any edge cases that I need to solve in this fix, as it is a documentation fix, not one that interacts directly with the code.