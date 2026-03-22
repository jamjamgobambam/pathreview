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

            # Create sample reviews for all users
            logger.info("Creating sample reviews...")

            # --- user1: two complete reviews showing improvement + one failed ---
            stmt = select(User).where(User.email == "user1@example.com")
            result = await session.execute(stmt)
            user1 = result.scalar_one_or_none()

            if user1:
                stmt = select(Profile).where(Profile.user_id == user1.id)
                result = await session.execute(stmt)
                profile1 = result.scalar_one_or_none()

                if profile1:
                    reviews_user1 = [
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
                    for review in reviews_user1:
                        session.add(review)
                    logger.info("Created reviews for user1")

            # --- user2: one complete review, earlier in career, lower score ---
            stmt = select(User).where(User.email == "user2@example.com")
            result = await session.execute(stmt)
            user2 = result.scalar_one_or_none()

            if user2:
                stmt = select(Profile).where(Profile.user_id == user2.id)
                result = await session.execute(stmt)
                profile2 = result.scalar_one_or_none()

                if profile2:
                    reviews_user2 = [
                        Review(
                            id=str(uuid4()),
                            profile_id=profile2.id,
                            status="complete",
                            overall_score=0.58,
                            created_at=datetime.utcnow() - timedelta(days=7),
                            updated_at=datetime.utcnow() - timedelta(days=7),
                            sections=[
                                {
                                    "section_name": "Technical Skills",
                                    "content": "Your profile shows 4 public repositories, all created within the last 6 months. The code quality is inconsistent — some files have no comments, variable names like 'x' and 'temp2' appear frequently, and two repos have no commits after the initial push. Recruiters will interpret abandoned repos as a red flag.",
                                    "confidence": 0.76,
                                    "suggestions": [
                                        "Archive or delete repos you don't plan to maintain",
                                        "Refactor your most recent project to use meaningful variable and function names",
                                        "Add at least one project that uses an external API or database",
                                    ],
                                },
                                {
                                    "section_name": "Project Experience",
                                    "content": "None of your current projects demonstrate end-to-end thinking — they're all isolated scripts or single-page experiments. There's no evidence of user-facing work, data persistence, or deployment. This makes it difficult to evaluate your readiness for a junior role.",
                                    "confidence": 0.81,
                                    "suggestions": [
                                        "Build and deploy one full-stack project, even something simple like a personal blog",
                                        "Add a live URL or screenshot to at least one project README",
                                        "Include a brief write-up of what problem each project solves and why you built it",
                                    ],
                                },
                                {
                                    "section_name": "Career Positioning",
                                    "content": "Your GitHub bio is empty and your portfolio URL returns a 404. There's no LinkedIn link and no resume attached to any application materials we could find. You're essentially invisible to recruiters who search for candidates online.",
                                    "confidence": 0.69,
                                    "suggestions": [
                                        "Fill in your GitHub bio with your name, target role, and one standout skill",
                                        "Fix or replace your portfolio URL — even a simple GitHub Pages site is better than a 404",
                                        "Create a LinkedIn profile and connect it to your GitHub",
                                    ],
                                },
                            ],
                        ),
                    ]
                    for review in reviews_user2:
                        session.add(review)
                    logger.info("Created reviews for user2")

            # --- user3: two complete reviews, strong candidate, high scores ---
            stmt = select(User).where(User.email == "user3@example.com")
            result = await session.execute(stmt)
            user3 = result.scalar_one_or_none()

            if user3:
                stmt = select(Profile).where(Profile.user_id == user3.id)
                result = await session.execute(stmt)
                profile3 = result.scalar_one_or_none()

                if profile3:
                    reviews_user3 = [
                        Review(
                            id=str(uuid4()),
                            profile_id=profile3.id,
                            status="complete",
                            overall_score=0.87,
                            created_at=datetime.utcnow() - timedelta(days=21),
                            updated_at=datetime.utcnow() - timedelta(days=21),
                            sections=[
                                {
                                    "section_name": "Technical Skills",
                                    "content": "Strong technical foundation across your 23 public repositories. Your most recent projects show consistent use of type hints, docstrings, and test suites. Your open source contributions to two mid-size Python libraries demonstrate you can navigate unfamiliar codebases and communicate through PRs.",
                                    "confidence": 0.91,
                                    "suggestions": [
                                        "Add CI/CD badges to your top repos to surface your automation practices",
                                        "Your Go projects lack test coverage — add at least unit tests for core logic",
                                        "Consider publishing a small Python package to PyPI to demonstrate end-to-end ownership",
                                    ],
                                },
                                {
                                    "section_name": "Project Experience",
                                    "content": "Your distributed task queue project is technically impressive and well-documented. The load testing results you included in the README are a strong differentiator — most candidates at your level don't benchmark their work. Two other projects have clear problem statements and measurable outcomes.",
                                    "confidence": 0.89,
                                    "suggestions": [
                                        "Write a technical blog post about the architecture decisions in your task queue project",
                                        "Your ML project README buries the results — move the accuracy metrics to the top",
                                        "Add a comparison table showing your approach vs. existing solutions",
                                    ],
                                },
                                {
                                    "section_name": "Career Positioning",
                                    "content": "You're well-positioned for mid-level backend or platform engineering roles. Your online presence is cohesive: GitHub, LinkedIn, and portfolio all tell the same story. The main gap is visibility — your blog hasn't been updated in 8 months and you have no recent conference talks or community contributions.",
                                    "confidence": 0.84,
                                    "suggestions": [
                                        "Publish one technical article per month — even short ones build SEO and credibility",
                                        "Submit a talk proposal to a local Python or backend engineering meetup",
                                        "Ask two former collaborators for LinkedIn recommendations focused on technical depth",
                                    ],
                                },
                            ],
                        ),
                        Review(
                            id=str(uuid4()),
                            profile_id=profile3.id,
                            status="complete",
                            overall_score=0.91,
                            created_at=datetime.utcnow() - timedelta(days=2),
                            updated_at=datetime.utcnow() - timedelta(days=2),
                            sections=[
                                {
                                    "section_name": "Technical Skills",
                                    "content": "Excellent progress. Your new Rust project shows you're actively expanding beyond your Python comfort zone, and the README quality has improved across all repos. Your CI/CD pipelines now run on all active projects, including matrix testing across Python 3.10–3.12.",
                                    "confidence": 0.93,
                                    "suggestions": [
                                        "Add property-based tests with Hypothesis to your core libraries",
                                        "Document your local dev setup in a CONTRIBUTING.md — you're ready to receive outside contributors",
                                        "Pin your dependency versions more tightly in production-facing projects",
                                    ],
                                },
                                {
                                    "section_name": "Project Experience",
                                    "content": "Your PyPI package now has 340 downloads/month — that's a meaningful signal to include on your resume. The blog post you published about the task queue project has 2,100 views and is ranking for several relevant search terms. Your project portfolio now clearly demonstrates scope, ownership, and impact.",
                                    "confidence": 0.92,
                                    "suggestions": [
                                        "Add a 'Featured Work' section to your portfolio site with 3 curated projects",
                                        "Cross-post your technical articles to dev.to or Hashnode for wider reach",
                                        "Update your resume to quantify the PyPI package impact",
                                    ],
                                },
                                {
                                    "section_name": "Career Positioning",
                                    "content": "You're a strong candidate for senior backend or staff-track roles at growth-stage companies. Your public work speaks for itself. The remaining opportunity is to make your job search intent clearer — it's not obvious from your profile that you're open to opportunities.",
                                    "confidence": 0.88,
                                    "suggestions": [
                                        "Set your LinkedIn to 'Open to Work' (visible to recruiters only if preferred)",
                                        "Add a brief 'currently interested in' note to your GitHub bio",
                                        "Reach out directly to 3–5 companies whose engineering blogs you follow",
                                    ],
                                },
                            ],
                        ),
                    ]
                    for review in reviews_user3:
                        session.add(review)
                    logger.info("Created reviews for user3")

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
