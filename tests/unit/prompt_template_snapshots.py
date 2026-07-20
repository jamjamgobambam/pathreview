"""
Snapshot hashes for prompt templates.

Regenerate with: python -m tests.unit.generate_prompt_snapshots

Only regenerate when you've intentionally added/changed a version key.
If a hash here changes for an EXISTING version (e.g. "v1" -> new hash)
without a new version key being added, that's the exact thing this
snapshot system exists to catch — don't just silently regenerate it.
"""

TEMPLATE_SNAPSHOTS = {
    "first_impression": {
        "v1": "9e7697ff3efd892c82c63ffcc8365690685fb1c29f79d45d84e057b2d0672dd0",
    },
    "gaps_feedback": {
        "v1": "b2673a1a1f018f2f2fdf37b2dfb6b30634404ba7bb2c241cc01b6240b9097950",
    },
    "presentation_feedback": {
        "v1": "87230b7045d66a1fae7d06e2509c6fae31046e0c4e8d30a3c3d6fe9ad2a7a3d7",
    },
    "projects_feedback": {
        "v1": "7e53575582f45389e4a3e4f93c7c137da629d3a14809e16f746732b9a06740d1",
    },
    "skills_feedback": {
        "v1": "a24d6d717d4f365c28a686f28b3e77f47204c325ce892fc32d68eb82259f6816",
    },
}
