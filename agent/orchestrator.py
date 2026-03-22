"""Plan-execute orchestrator for agent tools."""

import time
import structlog
from typing import Optional

from .memory.session_store import SessionStore
from .memory.context_manager import ContextManager
from .error_handling import retry_with_backoff

logger = structlog.get_logger()


class Orchestrator:
    """Orchestrate tool execution with planning and memoization."""

    def __init__(self, tools: dict, session_store: Optional[SessionStore] = None,
                 tool_timeout: float = 30.0):
        """Initialize orchestrator.

        Args:
            tools: Dict mapping tool names to tool instances
            session_store: Redis-backed session store (optional)
            tool_timeout: Timeout per tool in seconds
        """
        self.tools = tools
        self.session_store = session_store
        self.tool_timeout = tool_timeout
        self.context_manager = ContextManager()

    def run(self, profile_id: str, profile_data: dict) -> dict:
        """Execute analysis plan for a profile.

        Args:
            profile_id: Profile identifier
            profile_data: Profile data dict with github_username, projects, etc.

        Returns:
            Dict with analysis results from all tools
        """
        logger.info("orchestrator_start", profile_id=profile_id)

        # Build execution plan
        plan = self._build_plan(profile_data)

        # Load previous session state if available
        session_state = {}
        if self.session_store:
            session_state = self.session_store.get(profile_id) or {}

        # Execute plan
        results = {}
        for tool_name, tool_input in plan:
            try:
                result = self._execute_tool(tool_name, tool_input)
                results[tool_name] = result.data if hasattr(result, 'data') else result

                logger.info("tool_executed", tool=tool_name, success=True)

            except Exception as e:
                logger.error("tool_execution_failed", tool=tool_name, error=str(e))
                results[tool_name] = {"error": str(e), "success": False}

        # Persist state
        if self.session_store:
            session_state.update(results)
            self.session_store.set(profile_id, session_state)

        logger.info("orchestrator_complete", profile_id=profile_id,
                   tools_executed=len(results))

        return {
            "profile_id": profile_id,
            "tool_results": results,
            "cached_results": self.context_manager.get_all_results()
        }

    def _build_plan(self, profile_data: dict) -> list[tuple[str, dict]]:
        """Build execution plan based on available data.

        Args:
            profile_data: Profile data

        Returns:
            List of (tool_name, tool_input) tuples
        """
        plan = []

        # Conditionally add GitHub tool
        if profile_data.get("github_username"):
            for project in profile_data.get("projects", []):
                if project.get("github_repo"):
                    plan.append((
                        "github_tool",
                        {
                            "github_username": profile_data["github_username"],
                            "repo_name": project["github_repo"]
                        }
                    ))
                    break  # Only process first repo for now

        # Tech detector (if files available)
        if profile_data.get("files"):
            plan.append((
                "tech_detector",
                {"files": profile_data["files"]}
            ))

        # README scorer
        if profile_data.get("readme_content"):
            plan.append((
                "readme_scorer",
                {"readme_content": profile_data["readme_content"]}
            ))

        # Skill extractor
        if profile_data.get("resume_text"):
            plan.append((
                "skill_extractor",
                {
                    "resume_text": profile_data["resume_text"],
                    "repo_metadata": profile_data.get("repo_metadata", {})
                }
            ))

        # Market analyzer (if skills detected)
        if plan:  # Only if other tools executed
            plan.append((
                "market_analyzer",
                {"detected_skills": {}}  # Will be populated by context
            ))

        logger.info("plan_built", plan_size=len(plan))
        return plan

    def _execute_tool(self, tool_name: str, tool_input: dict):
        """Execute a single tool with retry and memoization.

        Args:
            tool_name: Name of tool to execute
            tool_input: Input dict for tool

        Returns:
            Tool result
        """
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Check context cache
        input_hash = ContextManager.hash_input(tool_input)
        cached_result = self.context_manager.get_tool_result(tool_name, input_hash)

        if cached_result:
            logger.info("tool_cache_hit", tool=tool_name)
            return cached_result

        # Execute with retry and timeout
        tool = self.tools[tool_name]

        try:
            result = self._execute_with_timeout(tool, tool_input)

            # Cache result
            self.context_manager.store_tool_result(tool_name, input_hash, result)

            return result

        except TimeoutError:
            logger.error("tool_timeout", tool=tool_name, timeout=self.tool_timeout)
            raise
        except Exception as e:
            logger.error("tool_execution_error", tool=tool_name, error=str(e))
            raise

    def _execute_with_timeout(self, tool, tool_input: dict, timeout: Optional[float] = None):
        """Execute tool with timeout.

        Args:
            tool: Tool instance
            tool_input: Tool input
            timeout: Timeout in seconds

        Returns:
            Tool result

        Raises:
            TimeoutError if tool takes too long
        """
        timeout = timeout or self.tool_timeout

        @retry_with_backoff(max_retries=2, backoff_factor=1.5)
        def _execute():
            return tool.execute(tool_input)

        start = time.time()
        result = _execute()
        elapsed = time.time() - start

        if elapsed > timeout:
            logger.warning("tool_slow", tool=tool.name, elapsed=elapsed, timeout=timeout)

        return result
