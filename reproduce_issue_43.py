"""
Reproduction script for issue #43:
"Agent session state is not cleared between reviews for the same user"

Run with:
    python reproduce_issue_43.py

What this shows:
    The Orchestrator's per-tool result cache (ContextManager) is keyed only
    on a hash of the tool's input parameters, with no TTL and no way to
    force a refresh. If the same Orchestrator instance handles a second
    review request for the same profile -- and the tool's input parameters
    look the same as last time (e.g. same github_repo name) -- the cached
    result from the FIRST review is returned instead of re-running the tool.

    This is a problem because tools like github_tool or market_analyzer can
    produce different real-world output over time even when called with the
    exact same input parameters (e.g. the user pushed new commits, or the
    job market data changed) -- but the cache has no way to know that and
    will happily serve stale data forever.

Expected (correct) behavior:
    The tool should execute once per review request, so review #2 reflects
    current reality.

Actual (buggy) behavior:
    The tool executes once total. Review #2 silently reuses review #1's
    result.
"""

from agent.orchestrator import Orchestrator


class CountingTool:
    """A fake tool that tracks how many times it was actually executed."""

    name = "tech_detector"

    def __init__(self) -> None:
        self.call_count = 0

    def execute(self, tool_input: dict) -> dict:
        self.call_count += 1
        return {
            "call_number": self.call_count,
            "note": f"This is the result from execution #{self.call_count}",
        }


def main() -> None:
    tool = CountingTool()
    orchestrator = Orchestrator(tools={"tech_detector": tool}, session_store=None)

    profile_id = "profile-123"
    profile_data = {"files": ["main.py"]}  # unchanged between "reviews"

    print("=== Review request #1 (user's first review) ===")
    result_1 = orchestrator.run(profile_id, profile_data)
    print("tech_detector result:", result_1["tool_results"]["tech_detector"])
    print(f"Tool has actually been executed {tool.call_count} time(s) so far.\n")

    print("=== User asks for a second review (e.g. re-checks their profile) ===")
    result_2 = orchestrator.run(profile_id, profile_data)
    print("tech_detector result:", result_2["tool_results"]["tech_detector"])
    print(f"Tool has actually been executed {tool.call_count} time(s) so far.\n")

    if tool.call_count == 1:
        print(
            "BUG REPRODUCED: the tool was only executed once, even though "
            "the orchestrator ran twice. The second review silently reused "
            "the first review's cached result instead of generating a "
            "fresh one."
        )
    else:
        print("Tool executed fresh each time -- bug not present in this run.")


if __name__ == "__main__":
    main()
