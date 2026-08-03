"""Fixtures scoped to integration tests only."""

import pytest_asyncio


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_pool_after_each_test():
    """Prevent connections from leaking across test event loops.

    core.database.engine/AsyncSessionLocal and core.redis_client.redis_client
    are module-level singletons whose connection pools cache real connections
    bound to whichever event loop first used them. pytest-asyncio gives each
    test function its own event loop by default, so without disposing these
    pools here, the next test's loop tries to reuse a connection tied to the
    previous (now closed) loop -- asyncpg raises "attached to a different
    loop" immediately, while redis-py instead hangs trying to read a response
    that will never arrive on the dead loop's socket.

    The imports are deliberately inside the fixture body, not at module level.
    conftest.py files (unlike regular test modules) can be imported by pytest
    during its early "initial conftest" scan, which runs before
    pytest_configure -- if these imports were at module level, they could
    construct core.config's settings singleton (and the engine/client built
    from it) using the default/unset env, before tests/conftest.py's
    pytest_configure hook ever sets DATABASE_URL/REDIS_URL to point at the
    ephemeral containers. Keeping the imports here guarantees they only
    happen once an actual test runs, which is always after configure.
    """
    from core.database import engine
    from core.redis_client import redis_client

    yield
    await engine.dispose()
    await redis_client.aclose()
