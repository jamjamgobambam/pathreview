"""Job market comparison tool."""

import redis
import json
import structlog
from .base import BaseTool, ToolResult

logger = structlog.get_logger()


class MarketAnalyzer(BaseTool):
    """Analyze user skills against job market demands."""

    name = "market_analyzer"
    description = "Analyze skills against job market demands"

    # Static market data: skills and demand scores
    MARKET_DATA = {
        "Python": 0.95,
        "JavaScript": 0.93,
        "TypeScript": 0.85,
        "React": 0.90,
        "AWS": 0.88,
        "Docker": 0.82,
        "Kubernetes": 0.78,
        "SQL": 0.92,
        "Java": 0.87,
        "C#": 0.80,
        "Go": 0.75,
        "Rust": 0.72,
        "Node.js": 0.88,
        "PostgreSQL": 0.85,
        "MongoDB": 0.75,
        "Redis": 0.73,
        "GraphQL": 0.70,
        "Git": 0.98,
        "REST": 0.89,
        "GCP": 0.78,
    }

    def __init__(self, redis_client: redis.Redis | None = None):
        """Initialize market analyzer.

        Args:
            redis_client: Redis client for caching (optional)
        """
        self.redis_client = redis_client

    def execute(self, input_data: dict) -> ToolResult:
        """Analyze user skills against market.

        Args:
            input_data: Must contain 'detected_skills' dict

        Returns:
            ToolResult with market analysis
        """
        detected_skills = input_data.get("detected_skills", {})

        if not detected_skills:
            logger.warning("market_analyzer_no_skills")
            return ToolResult(
                success=True,
                data={
                    "in_demand_skills": [],
                    "missing_high_demand_skills": [],
                    "market_alignment_score": 0.0,
                }
            )

        try:
            analysis = self._analyze_market(detected_skills)
            return ToolResult(success=True, data=analysis)

        except Exception as e:
            logger.error("market_analyzer_error", error=str(e))
            return ToolResult(
                success=False,
                data={},
                error=str(e)
            )

    def _analyze_market(self, detected_skills: dict) -> dict:
        """Analyze skills against market data.

        Args:
            detected_skills: Dict of skills by category

        Returns:
            Dict with market analysis
        """
        # Flatten detected skills
        all_detected = set()
        for category, skills_list in detected_skills.items():
            all_detected.update(skills_list)

        # Find in-demand skills the user has
        in_demand = []
        for skill, demand in self.MARKET_DATA.items():
            if skill in all_detected:
                in_demand.append({
                    "skill": skill,
                    "demand_score": demand
                })

        # Sort by demand
        in_demand.sort(key=lambda x: x["demand_score"], reverse=True)

        # Find high-demand skills they're missing (>0.80)
        missing_high_demand = []
        for skill, demand in self.MARKET_DATA.items():
            if skill not in all_detected and demand > 0.80:
                missing_high_demand.append({
                    "skill": skill,
                    "demand_score": demand
                })

        # Sort by demand
        missing_high_demand.sort(key=lambda x: x["demand_score"], reverse=True)

        # Calculate alignment score
        if in_demand:
            avg_demand = sum([s["demand_score"] for s in in_demand]) / len(in_demand)
        else:
            avg_demand = 0.0

        market_alignment = min(avg_demand * 0.8, 1.0)

        logger.info("market_analyzed", user_skills=len(all_detected),
                   in_demand=len(in_demand), missing_high_demand=len(missing_high_demand),
                   alignment=market_alignment)

        result = {
            "in_demand_skills": in_demand,
            "missing_high_demand_skills": missing_high_demand,
            "market_alignment_score": market_alignment,
        }

        # Cache in Redis if available
        if self.redis_client:
            self._cache_result(result)

        return result

    def _cache_result(self, result: dict, ttl_seconds: int = 86400) -> None:
        """Cache result in Redis with 24-hour TTL.

        Args:
            result: Result to cache
            ttl_seconds: TTL in seconds (default 24 hours)
        """
        if not self.redis_client:
            return

        try:
            self.redis_client.setex(
                "market_analysis:latest",
                ttl_seconds,
                json.dumps(result)
            )
            logger.info("market_analysis_cached", ttl_seconds=ttl_seconds)
        except Exception as e:
            logger.warning("market_analysis_cache_failed", error=str(e))
