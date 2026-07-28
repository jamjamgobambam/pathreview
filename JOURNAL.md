## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/101

**Issue title:** Add a "Copy link" button to share a public review summary

**Tier:** Tier 2 

**Problem summary:**
A new feature request has been made that allows the user to click a copy link button that renders a page displaying a given review. The link should expire after 30 days, and it should not require any authentication to view. A button will be added to the ReviewPage.tsx that copies a link to clipboard, a new shareService.ts file will be generated to handle the logic for serving the links, and it will call a new unauthenticated public endpoint in reviews.py in order to pull the review text (the existing get route can't be used because it requires login and ownership). In addition, a new database table and schema will be created to hold the expiration date of the newly generated link.

**Branch name:** feat/101-add-copy-link-button

**Setup confirmation:** [ X ] App runs locally at localhost:5173

**Cohort ledger:** [ X ] Issue added to cohort ledger

**Is this issue right for me?**
This is a Tier 2 issue and it's a good fit for me. I've worked as a dev on React apps with backend APIs, so a feature that touches the frontend, a new service, and an API endpoint is in my wheelhouse. I've already located and read the code it affects-the Share button in ReviewPage.tsx and the get route in reviews.py, and reading the route is what told me I'll need a new unauthenticated endpoint instead of reusing the existing one. Right now the Share button copies an authenticated URL only the owner can open, and after the fix it copies a public link anyone can view for 30 days.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/crbridges/pathreview/commit/43e1ce6a3b55b22bf467055d0f4384abd93dd609

**Reproduction summary:**
This issue is a new feature (labeled `enhancement`), so there's no bug to reproduce. I confirmed the gap by tracing the code: every route in `api/routes/reviews.py` depends on `get_current_user`, `ReviewPage` is wrapped in `<ProtectedRoute>` in `App.tsx`, and the current Share button just copies `window.location.href` — so there is no way to view a review without logging in, and no public endpoint exists yet.

**PLAN.md link:** https://github.com/crbridges/pathreview/blob/feat/101-add-copy-link-button/PLAN.md

**Walkthrough video (recommended):** not recorded

**Blockers or open questions:**
The new `/shared/:token` route has to be registered outside `<ProtectedRoute>` or logged-out visitors get bounced to `/login`, and `<NavBar />` renders on every route so it may need to be hidden on the public page. Still deciding whether the public view exposes the full review or a trimmed summary.