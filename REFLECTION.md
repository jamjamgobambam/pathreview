# Reflection: Module 3 Contribution to PathReview

**Issue:** #101, add a "Copy link" button to share a public review summary
**PR:** https://github.com/ascherj/pathreview/pull/897

## Why I picked this issue

I work as a frontend intern, mostly in Angular, so I wanted something that was really a frontend feature but still forced me to touch the whole stack. The Tier 1 frontend issues on the board were small polish or test tasks, and I could have finished one of those quickly and safely. I went with #101 instead because it was a complete, user facing feature that a real person would actually use. You finish a review, you want to send it to a mentor, and right now you just cannot. That was easy to picture, which told me the requirements were clear even though the work spanned three layers.

Looking back, the scope estimate of five to eight hours was honest for the coding itself. What I did not budget for was everything around the code, which ended up taking as long as the feature.

## What I built

The old Share button just copied the review's own URL, which sits behind login, so anyone without an account got bounced to the login page. My fix adds a real public link. On the backend that meant a new share_links table and migration, a service that mints an unguessable token tied to a review, and two endpoints: an authenticated one for the owner to create a link, and a public one to read it. The link expires after 30 days, and I made sure that expiry is checked on the server, not just hidden in the interface. On the frontend I replaced the alert with a proper "Link copied!" confirmation and built a read only page that anyone can open with no login.

A few decisions I had to make on my own since the maintainer was not around to ask. I return a 404 for both an unknown token and an expired one, so the response does not leak whether a token ever existed. I reuse an existing unexpired link instead of minting a new one on every click. And I only allow completed reviews to be shared. I wrote all of these into the PR so a reviewer can push back on any of them.

## What surprised me and what was hardest

The feature was the easy part. The hard part was that when I ran the project's own quality checks to measure my work against a clean baseline, the baseline was already broken. make lint reported 162 errors, the type checker would not even run because of a Python version mismatch with a library stub, dozens of files were not formatted, and the pre commit hook runs the type checker without the project's own dependencies, so it flagged normal framework code as errors. My clean feature kept getting blocked by problems that were not mine.

That turned into the most useful lesson of the whole module. The real skill was not writing the share link, it was telling my own signal apart from the repo's noise, and being able to prove which was which. I confirmed my files passed every check in isolation, then documented the broken baseline honestly in the PR with evidence, and committed with the hook bypassed rather than pretending the checks were green or drowning my feature in unrelated fixes. I also hit a Windows only bug where the dev server could not reach the backend over IPv6, which cost me a confusing half hour on what looked like a wrong password.

## What I learned about large codebases

Before writing anything I spent real time reading how the existing code was shaped, how reviews were fetched, how auth was enforced, how migrations were written, how tests were structured. That paid off. My new files look like the files next to them because I copied the patterns instead of inventing my own. Matching the house style made the change feel small even though it crossed the whole stack.

## What I would do differently

I would run the project's checks on day one, before touching anything, so I discover a broken baseline early instead of at commit time. That is a conversation you want to have with a maintainer before you open the PR, not after. I would also reproduce the issue live in the browser sooner. I proved it quickly at the API level, which was solid, but seeing it fail in a real browser earlier would have grounded my plan even faster.

Overall I am proud that I never guessed. Every design decision I made, I checked against the running app, not just in my head.
