## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/101

**Issue title:** Add a "Copy link" button to share a public review summary

**Tier:** Tier 2 

**Problem summary:**
A new feature request has been made that allows the user to click a copy link button that renders a page displaying a given review. The link should expire after 30 days, and it should not require any authentication to view. A button will be added to the ReviewPage.tsx that copies a link to clipboard, a new shareService.ts file will be generated to handle the logic for serving the links, and it will call a new unauthenticated public endpoint in reviews.py in order to pull the review text (the existing get route can't be used because it requires login and ownership). In addition, a new database table and schema will be created to hold the expiration date of the newly generated link.

**Branch name:** enhancement/101-add-copy-link-button

**Setup confirmation:** [ X ] App runs locally at localhost:5173

**Cohort ledger:** [ X ] Issue added to cohort ledger

**Is this issue right for me?**
This is a Tier 2 issue and it's a good fit for me. I've worked as a dev on React apps with backend APIs, so a feature that touches the frontend, a new service, and an API endpoint is in my wheelhouse. I've already located and read the code it affects: the Share button in ReviewPage.tsx and the get route in reviews.py, and reading the route is what told me I'll need a new unauthenticated endpoint instead of reusing the existing one. The before-and-after is clear too: right now the Share button copies an authenticated URL only the owner can open, and after the fix it copies a public link anyone can view for 30 days. I'm confident I can finish it before the Week 9 deadline and there are no blockers.