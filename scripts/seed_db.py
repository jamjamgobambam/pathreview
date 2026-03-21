"""Seed the development database with sample portfolio data."""

import json
import sys


def main() -> None:
    """Seed sample profiles, resumes, and reviews into the dev database."""
    print("Seeding database with sample data...")
    # TODO: Implement database seeding with sample portfolios
    # Sample users:
    #   - user1 / password1 — profile with 3 repos, resume, full review history
    #   - user2 / password2 — profile with 1 repo, resume, no reviews yet
    #   - user3 / password3 — empty profile (just created account)
    print("Database seeded successfully.")


if __name__ == "__main__":
    main()
