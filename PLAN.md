## Solution plan

**Issue:** [fix/43-agent-session-state-not-cleared](https://github.com/ascherj/pathreview/issues/43)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The root cause of the issue is due to the orchestrator agent that loads previous per-profile session data. This results in the same review output when it is suppose to start fresh. 

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

In orchestrator.py, the def run function runs an analysis on a previous user if they have data already available. If found, they reload the previous session state. Resulting in the reload of stale data. This is shown in the console logs that refresh the same data at the same time it was first found. It shows that the profile data was loaded at 12:11:35 every time I upload a new review, even if it is past that time. 

It lies in the session persistence and state accumulation. 

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

I think when a user wants to review a previous portfolio review, that is when a saved session is needed but when a user creates a new review with the same profile it needs to save it using a different id per review. So I want to create a session id that is different from a user id. So when a new review is created it is stored with that session id and when a user wants to search a previous review, it searches again by the session id and not the user id. I believe some of this is already implemented so I will review the code and again and see how loading previous reviews work. 

I will make sure the key that helps with state persistence is purged from it's old keys so it doesn't use stale data.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

My fix would take a new session store key by review_id instead of profile_id. This would preserve past review histories for a user profile while generating new reviews as well. 

### Risks & unknowns
What could go wrong? What are you still unsure about?

Connecting every other file and making sure it reads the new key I created. 

### Edge cases
What inputs or states should your fix handle gracefully?

If a user starts a second review for the same profile before or after a prior review has completed, the new run should begin without inheriting stale session state from the earlier run.

If no prior session data exists for a profile, the orchestrator should treat that as a fresh review and continue without error.