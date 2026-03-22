"""Database seeding script to create sample users, profiles, and reviews."""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select

from core.database import AsyncSessionLocal, init_db
from core.logging import configure_logging, get_logger
from core.models import Profile, User
from core.models.review import Review
from core.security import hash_password

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

            # Create sample reviews for user1's profile
            logger.info("Creating sample reviews...")
            stmt = select(User).where(User.email == "user1@example.com")
            result = await session.execute(stmt)
            user1 = result.scalar_one_or_none()

            if user1:
                stmt = select(Profile).where(Profile.user_id == user1.id)
                result = await session.execute(stmt)
                profile1 = result.scalar_one_or_none()

                if profile1:
                    sample_reviews = [
                        Review(
                            id=str(uuid4()),
                            profile_id=profile1.id,
                            status="complete",
                            overall_score=0.74,
                            created_at=datetime.utcnow() - timedelta(days=14),
                            updated_at=datetime.utcnow() - timedelta(days=14),
                            sections=[
                                {
                                    "section_name": "Technical Skills",
                                    "content": "Your GitHub profile shows strong proficiency in Python and JavaScript. You've contributed to 12 public repos over the past year with consistent commit history. However, your projects lack README documentation — only 2 of 12 repos have a README with setup instructions, which makes it hard for recruiters to evaluate your work quickly.",
                                    "confidence": 0.82,
                                    "suggestions": [
                                        "Add a detailed README to your top 3 pinned repositories",
                                        "Include live demo links or screenshots in project descriptions",
                                        "Highlight your AI/ML coursework — it's not visible from your profile",
                                    ],
                                },
                                {
                                    "section_name": "Project Experience",
                                    "content": "Your portfolio-tracker project is the strongest entry — it has tests, a CI workflow, and a clear problem statement. The other projects are underdeveloped. Your weather app and todo list are common beginner exercises that won't differentiate you from other candidates at your level.",
                                    "confidence": 0.78,
                                    "suggestions": [
                                        "Replace generic tutorial projects with a capstone that solves a real problem",
                                        "Add impact metrics: number of users, API calls handled, performance benchmarks",
                                        "Consider contributing to an open source project to show collaboration skills",
                                    ],
                                },
                                {
                                    "section_name": "Career Positioning",
                                    "content": "Your resume emphasizes frontend skills but your GitHub activity skews backend. This mixed signal may confuse recruiters. Your LinkedIn headline says 'student' — you should update it to reflect the role you're targeting. Your portfolio site loads slowly (4.2s) and has no mobile layout.",
                                    "confidence": 0.71,
                                    "suggestions": [
                                        "Align your resume, LinkedIn, and GitHub bio around a clear target role",
                                        "Optimize your portfolio site's load time and add responsive CSS",
                                        "Add 2–3 sentences to your GitHub bio describing your specialization",
                                    ],
                                },
                            ],
                        ),
                        Review(
                            id=str(uuid4()),
                            profile_id=profile1.id,
                            status="complete",
                            overall_score=0.81,
                            created_at=datetime.utcnow() - timedelta(days=3),
                            updated_at=datetime.utcnow() - timedelta(days=3),
                            sections=[
                                {
                                    "section_name": "Technical Skills",
                                    "content": "Significant improvement since your last review. You've added READMEs to all pinned repositories with setup instructions and screenshots. Your new FastAPI project demonstrates solid backend fundamentals including authentication, database migrations, and async patterns.",
                                    "confidence": 0.88,
                                    "suggestions": [
                                        "Add type hints throughout your Python projects — currently only 40% coverage",
                                        "Your test coverage is 62% — aim for 80%+ on core business logic",
                                        "Consider adding a system design doc to your largest project",
                                    ],
                                },
                                {
                                    "section_name": "Project Experience",
                                    "content": "Your new capstone project (AI study assistant) is a strong differentiator — it integrates an LLM API, has a real user base (47 GitHub stars), and solves a genuine problem. This should be your lead project in interviews.",
                                    "confidence": 0.85,
                                    "suggestions": [
                                        "Write a brief case study blog post about the AI study assistant",
                                        "Add a 2-minute demo video to the README",
                                        "Document the architecture decisions in an ADR or design doc",
                                    ],
                                },
                                {
                                    "section_name": "Career Positioning",
                                    "content": "Your positioning is much clearer now. LinkedIn headline updated to 'Backend & AI Engineer' and your resume leads with your strongest project. Portfolio site loads in 1.8s with a responsive layout. One remaining gap: no visible contributions to external open source projects.",
                                    "confidence": 0.79,
                                    "suggestions": [
                                        "Make 2–3 meaningful open source contributions before your job search",
                                        "Add your CodePath AI 201 completion to your resume education section",
                                        "Request LinkedIn recommendations from peers who've seen your code",
                                    ],
                                },
                            ],
                        ),
                        Review(
                            id=str(uuid4()),
                            profile_id=profile1.id,
                            status="failed",
                            overall_score=None,
                            created_at=datetime.utcnow() - timedelta(hours=1),
                            updated_at=datetime.utcnow() - timedelta(hours=1),
                            sections=None,
                            error_message="GitHub API rate limit exceeded. Please try again later.",
                        ),
                    ]

                    for review in sample_reviews:
                        session.add(review)

                    await session.commit()
                    logger.info("Sample reviews created successfully")

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
