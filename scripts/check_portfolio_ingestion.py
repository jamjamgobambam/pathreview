"""Reproduction script for issue #11: portfolio URL ingestion is never wired up.

Confirms that `Profile.portfolio_url` is accepted and persisted, but no
matching `IngestedSource` row (source_type="web") is ever created for it —
demonstrating that the ingestion pipeline has no caller for portfolio URLs.
"""

import asyncio

from sqlalchemy import select

from core.database import AsyncSessionLocal
from core.logging import configure_logging, get_logger
from core.models import IngestedSource, Profile

logger = get_logger(__name__)


async def check_portfolio_ingestion() -> None:
    """Report profiles with a portfolio_url and any corresponding ingested web sources."""
    configure_logging()

    async with AsyncSessionLocal() as session:
        profiles_result = await session.execute(
            select(Profile).where(Profile.portfolio_url.isnot(None))
        )
        profiles_with_url = profiles_result.scalars().all()

        web_sources_result = await session.execute(
            select(IngestedSource).where(IngestedSource.source_type == "web")
        )
        web_sources = web_sources_result.scalars().all()

        print(f"Profiles with a portfolio_url set: {len(profiles_with_url)}")
        for profile in profiles_with_url:
            print(f"  - {profile.id}: {profile.portfolio_url}")

        print(f"\nIngestedSource rows with source_type='web': {len(web_sources)}")
        for source in web_sources:
            print(f"  - {source.id}: profile={source.profile_id} url={source.source_url}")

        if profiles_with_url and not web_sources:
            print(
                "\nReproduction confirmed: portfolio_url is accepted and stored on Profile, "
                "but no IngestedSource has ever been created for it — the ingestion "
                "pipeline is never invoked for portfolio URLs (see PLAN.md)."
            )


if __name__ == "__main__":
    asyncio.run(check_portfolio_ingestion())
