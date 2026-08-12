## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer comments came in during the week. Per the Su26 course note,
reviewer feedback is not a feature this term.

**How you responded:**
N/A — no feedback to address.

---

### Reflection

**What was harder than you expected?**
The environment setup was the biggest surprise. Before I could touch a
single line of code, I had to get Homebrew, Node, Docker, and pre-commit
all working on Apple Silicon — and the PATH issues for each one had to be
debugged independently. I expected maybe 30 minutes of setup; it took
multiple sessions. The actual regex fix was one line. The surrounding
infrastructure to even run the linter and submit cleanly took far longer
than the fix itself.

**What did you learn about working in a large codebase?**
The codebase has opinions about everything — commit message format,
branch naming, hook checks, PR templates — and none of that is optional.
In my own projects I skip all of it. Here, the process *is* part of the
contribution. I also learned to read existing code defensively: the
`pii_scrubber.py` file had a clear pattern I could follow, which made it
easier to write a fix that fit in rather than one that just worked.

**How did AI tools help — and where did they fall short?**
AI was most useful for understanding regex quickly — I could describe the
phone format I needed to match and get a working pattern explained in
context. It also helped me think through edge cases (parenthesized vs.
dashed formats) before writing the fix. Where it fell short: it couldn't
tell me that heredocs hang in my specific terminal setup, and it couldn't
debug the Apple Silicon PATH issues without me feeding it the exact error
output first. Anything environment-specific required trial and error on my
end; AI could only react to what I reported.

**What would you do differently if you started over?**
I'd pick an issue with a smaller blast radius. Issue #146 turned out to be
straightforward once I understood it, but I didn't know that at the start —
I just knew it was labeled "good first issue." Next time I'd spend more
time reading the surrounding code and existing tests before committing to
an issue, so I'm not discovering scope surprises mid-week.

**What are you most proud of from this module?**
Submitting the PR from my phone via GitHub's mobile web interface when my
computer was unavailable. Everything up to that point had been CLI-based,
and I'd never submitted a PR that way before. It worked, the branch was
correct, and the commit history was clean. That felt like actually knowing
what I was doing rather than just following steps.
