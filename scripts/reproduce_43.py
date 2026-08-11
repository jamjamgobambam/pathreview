"""
Reproduction script for issue #43:
Agent session state / tool-result cache is not cleared between reviews
for the same user, so a second review can silently return stale results.

Root cause: Orchestrator holds a single long-lived ContextManager instance
(self.context_manager) created once in __init__. _execute_tool() checks
this cache BEFORE running a tool, keyed only on hash(tool_name + tool_input).
If a second review's tool_input hashes the same as a previous review's
(e.g. same repo_name string, even though the repo's contents changed on
GitHub), the tool is never re-executed -- the old cached result is returned.

Run with:
    python scripts/reproduce_43.py
"""

from agent.orchestrator import Orchestrator


class StubGithubTool:
    """Fake tool that records how many times it actually executes."""

    name = "github_tool"

    def __init__(self) -> None:
        self.call_count = 0

    def execute(self, tool_input: dict) -> dict:
        self.call_count += 1
        return {"stars": 10 * self.call_count, "call_number": self.call_count}


def main() -> None:
    stub_tool = StubGithubTool()
    orchestrator = Orchestrator(tools={"github_tool": stub_tool})

    profile_data = {
        "github_username": "someuser",
        "projects": [{"github_repo": "my-portfolio-site"}],
    }

    print("--- First review ---")
    first = orchestrator.run(profile_id="user-123", profile_data=profile_data)
    print("tool_results:", first["tool_results"])
    print("stub_tool.call_count:", stub_tool.call_count)

    print("\n--- User updates their portfolio (repo content changes on GitHub), ---")
    print("--- then requests a SECOND review with the same repo_name ---")
    second = orchestrator.run(profile_id="user-123", profile_data=profile_data)
    print("tool_results:", second["tool_results"])
    print("stub_tool.call_count:", stub_tool.call_count)

    print("\n--- Verdict ---")
    if stub_tool.call_count == 1:
        print(
            "BUG REPRODUCED: tool only executed once. The second review "
            "returned a cached/stale result instead of re-running the tool."
        )
    else:
        print("Tool executed twice as expected -- bug not present.")


if __name__ == "__main__":
    main()
