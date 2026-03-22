"""Database seeding script to create sample users and profiles."""

import asyncio
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal, init_db
from core.models import User, Profile
from core.security import hash_password
from core.logging import get_logger, configure_logging

logger = get_logger(__name__)


async def seed_database() -> None:
    """Seed the database with sample users and profiles."""
    configure_logging()

    # Initialize database tables
    logger.info("Initializing database tables...")
    await init_db()
    logger.info("Database tables created successfully")

    # Create sample users
    sample_users = [
        {
            "email": "user1@example.com",
            "password": "password1",
            "github_username": "user1-github",
            "portfolio_url": "https://user1.dev",
        },
        {
            "email": "user2@example.com",
            "password": "password2",
            "github_username": "user2-github",
            "portfolio_url": "https://user2.portfolio",
        },
        {
            "email": "user3@example.com",
            "password": "password3",
            "github_username": "user3-github",
            "portfolio_url": "https://user3.io",
        },
    ]

    async with AsyncSessionLocal() as session:
        try:
            # Check if users already exist
            logger.info("Checking for existing users...")
            existing_count = 0
            for user_data in sample_users:
                stmt = select(User).where(User.email == user_data["email"])
                result = await session.execute(stmt)
                if result.scalar_one_or_none():
                    existing_count += 1

            if existing_count == len(sample_users):
                logger.info("Sample users already exist, skipping creation")
                print("\n✓ Sample users already exist in database")
                print("\nExisting credentials:")
                for user_data in sample_users:
                    print(f"  Email: {user_data['email']}")
                    print(f"  Password: {user_data['password']}")
                    print()
                return

            logger.info("Creating sample users and profiles...")
            # Create users and profiles
            for user_data in sample_users:
                email = user_data["email"]

                # Check if user exists
                stmt = select(User).where(User.email == email)
                result = await session.execute(stmt)
                existing_user = result.scalar_one_or_none()

                if existing_user:
                    logger.info(f"User {email} already exists, skipping")
                    continue

                # Create new user
                user = User(
                    id=str(uuid4()),
                    email=email,
                    hashed_password=hash_password(user_data["password"]),
                    is_active=True,
                )
                session.add(user)
                await session.flush()

                # Create associated profile
                profile = Profile(
                    id=str(uuid4()),
                    user_id=user.id,
                    github_username=user_data.get("github_username"),
                    portfolio_url=user_data.get("portfolio_url"),
                )
                session.add(profile)

                logger.info(f"Created user {email} with profile")

            await session.commit()
            logger.info("Database seeding completed successfully")

            print("\n✓ Database seeded successfully!")
            print("\nSample user credentials:")
            for user_data in sample_users:
                print(f"  Email: {user_data['email']}")
                print(f"  Password: {user_data['password']}")
                print()

        except Exception as e:
            await session.rollback()
            logger.error("Database seeding failed", error=str(e))
            print(f"\n✗ Database seeding failed: {e}")
            raise


def main() -> None:
    """Entry point for the seeding script."""
    asyncio.run(seed_database())


if __name__ == "__main__":
    main()
