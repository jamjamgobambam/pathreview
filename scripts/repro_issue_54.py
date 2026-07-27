"""Reproduction script for issue #54.

Issue: "Add a plan validation step that checks tool prerequisites before
executing the plan."

This script confirms, in the local environment, that the agent orchestrator
executes tools without checking their dependencies. It uses the real tools
(no network, no Redis, no LLM) and shows two concrete symptoms:

  1. `Orchestrator._build_plan` hands `market_analyzer` a hardcoded, empty
     `{"detected_skills": {}}` input, so the market analysis NEVER sees the
     skills that `skill_extractor` produced in the same run.
  2. Because there is no prerequisite validation, `market_analyzer` still runs
     and returns `success=True` with an all-zero result — the failure is
     completely silent.

Run:  .venv/bin/python scripts/repro_issue_54.py
"""

from agent.orchestrator import Orchestrator
from agent.tools.market_analyzer import MarketAnalyzer
from agent.tools.readme_scorer import ReadmeScorer
from agent.tools.skill_extractor import SkillExtractor
from agent.tools.tech_detector import TechDetector


def build_orchestrator() -> Orchestrator:
    """Build an orchestrator with the real, side-effect-free tools."""
    tools = {
        "tech_detector": TechDetector(),
        "readme_scorer": ReadmeScorer(),
        "skill_extractor": SkillExtractor(),
        "market_analyzer": MarketAnalyzer(),  # redis_client=None -> no network
    }
    return Orchestrator(tools)


def main() -> None:
    orch = build_orchestrator()

    # A profile whose resume is packed with in-demand skills.
    profile_data = {
        "resume_text": (
            "Senior software engineer with 5 years of Python and TypeScript. "
            "Built React front-ends, Django and FastAPI back-ends, deployed on "
            "AWS with Docker and Kubernetes. Strong SQL and PostgreSQL, plus Redis."
        ),
        "files": ["main.py", "app.tsx", "Dockerfile", "package.json"],
        "readme_content": "# Project\n\n## Installation\n\n## Usage\n",
    }

    print("=" * 72)
    print("STEP 1 — Inspect the plan the orchestrator builds")
    print("=" * 72)
    plan = orch._build_plan(profile_data)
    for tool_name, tool_input in plan:
        print(f"  - {tool_name:<16} input_keys={list(tool_input.keys())}")
        if tool_name == "market_analyzer":
            print(f"      >>> detected_skills passed in = {tool_input['detected_skills']!r}")
            print("      >>> EVIDENCE: market_analyzer is fed an EMPTY dict,")
            print("      >>> regardless of what skill_extractor will detect.")

    print()
    print("=" * 72)
    print("STEP 2 — Run the plan and compare skill_extractor vs market_analyzer")
    print("=" * 72)
    result = orch.run("repro-profile-54", profile_data)
    tool_results = result["tool_results"]

    skills = tool_results.get("skill_extractor", {})
    flat_skills = (
        sorted({s for group in skills.values() for s in group}) if isinstance(skills, dict) else []
    )
    market = tool_results.get("market_analyzer", {})

    print(f"  skill_extractor detected {len(flat_skills)} skills: {flat_skills}")
    print(f"  market_analyzer.in_demand_skills        = {market.get('in_demand_skills')}")
    print(f"  market_analyzer.market_alignment_score  = {market.get('market_alignment_score')}")

    print()
    print("=" * 72)
    print("RESULT")
    print("=" * 72)
    bug_confirmed = (
        len(flat_skills) > 0
        and market.get("market_alignment_score") == 0.0
        and not market.get("in_demand_skills")
    )
    if bug_confirmed:
        print("  BUG CONFIRMED: skill_extractor found real skills, yet market_analyzer")
        print("  returned an all-zero analysis because its prerequisite's output was")
        print("  never propagated -- and NOTHING validated the prerequisite or flagged")
        print("  the empty input. The orchestrator reported overall success.")
    else:
        print("  Bug NOT reproduced -- current behavior differs from the report.")


if __name__ == "__main__":
    main()
