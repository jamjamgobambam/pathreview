"""Plan-execute orchestrator for agent tools."""

import time
import uuid
from typing import Any

import structlog

from .error_handling import retry_with_backoff
from .memory.context_manager import ContextManager
from .memory.session_store import SessionStore

logger = structlog.get_logger()


class Orchestrator:
    """Orchestrate tool execution with planning and memoization."""

    def __init__(
        self,
        tools: dict[str, Any],
        session_store: SessionStore | None = None,
        tool_timeout: float = 30.0,
    ) -> None:
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

    def run(
        self, profile_id: str, profile_data: dict[str, Any], review_id: str | None = None
    ) -> dict[str, Any]:
        """Execute analysis plan for a profile with session isolation.

        Args:
            profile_id: Profile identifier
            profile_data: Profile data dict with github_username, projects, etc.
            review_id: Unique review run identifier. If not provided, resolves from
                       profile_data or generates a UUID to isolate state.

        Returns:
            Dict with analysis results from all tools
        """
        # Resolve isolated review run ID and composite session key
        effective_review_id = review_id or profile_data.get("review_id") or str(uuid.uuid4())
        session_key = f"{profile_id}:{effective_review_id}"

        # Clear in-memory context manager so past runs don't pollute this run
        self.context_manager = ContextManager()

        logger.info(
            "orchestrator_start",
            profile_id=profile_id,
            review_id=effective_review_id,
            session_key=session_key,
        )

        # Build execution plan
        plan = self._build_plan(profile_data)

        # Load previous session state if available for this specific run
        session_state: dict[str, Any] = {}
        if self.session_store:
            session_state = self.session_store.get(session_key) or {}

        # Execute plan
        results: dict[str, Any] = {}
        for tool_name, tool_input in plan:
            try:
                result = self._execute_tool(tool_name, tool_input)
                if isinstance(result, dict):
                    results[tool_name] = result.get("data", result)
                elif hasattr(result, "data"):
                    results[tool_name] = result.data
                else:
                    results[tool_name] = result

                logger.info("tool_executed", tool=tool_name, success=True)

            except Exception as e:
                logger.error("tool_execution_failed", tool=tool_name, error=str(e))
                results[tool_name] = {"error": str(e), "success": False}

        # Persist isolated state using session_key
        if self.session_store:
            session_state.update(results)
            self.session_store.set(session_key, session_state)

        logger.info(
            "orchestrator_complete",
            profile_id=profile_id,
            review_id=effective_review_id,
            tools_executed=len(results),
        )

        return {
            "profile_id": profile_id,
            "review_id": effective_review_id,
            "tool_results": results,
            "cached_results": self.context_manager.get_all_results(),
        }

    def _build_plan(self, profile_data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        """Build execution plan based on available data.

        Args:
            profile_data: Profile data

        Returns:
            List of (tool_name, tool_input) tuples
        """
        plan: list[tuple[str, dict[str, Any]]] = []

        # Conditionally add GitHub tool
        if profile_data.get("github_username"):
            for project in profile_data.get("projects", []):
                if project.get("github_repo"):
                    plan.append(
                        (
                            "github_tool",
                            {
                                "github_username": profile_data["github_username"],
                                "repo_name": project["github_repo"],
                            },
                        )
                    )
                    break  # Only process first repo for now

        # Tech detector (if files available)
        if profile_data.get("files"):
            plan.append(("tech_detector", {"files": profile_data["files"]}))

        # README scorer
        if profile_data.get("readme_content"):
            plan.append(("readme_scorer", {"readme_content": profile_data["readme_content"]}))

        # Skill extractor
        if profile_data.get("resume_text"):
            plan.append(
                (
                    "skill_extractor",
                    {
                        "resume_text": profile_data["resume_text"],
                        "repo_metadata": profile_data.get("repo_metadata", {}),
                    },
                )
            )

        # Market analyzer (if skills detected)
        if plan:  # Only if other tools executed
            plan.append(
                ("market_analyzer", {"detected_skills": {}})  # Will be populated by context
            )

        logger.info("plan_built", plan_size=len(plan))
        return plan

    def _execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
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

    def _execute_with_timeout(
        self, tool: Any, tool_input: dict[str, Any], timeout: float | None = None
    ) -> Any:
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
        def _execute() -> Any:
            return tool.execute(tool_input)

        start = time.time()
        result = _execute()
        elapsed = time.time() - start

        if elapsed > timeout:
            logger.warning(
                "tool_slow", tool=getattr(tool, "name", "unknown"), elapsed=elapsed, timeout=timeout
            )

        return result
