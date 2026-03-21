"""Seed GitHub issues from the issues manifest JSON file.

Usage:
    python scripts/seed_issues.py --manifest scripts/issues_manifest.json --repo codepath-ai201/pathreview

Requires:
    gh (GitHub CLI) installed and authenticated
"""

import argparse
import json
import subprocess
import sys
import time


def create_issue(repo: str, issue: dict) -> None:
    """Create a single GitHub issue via the gh CLI."""
    labels = ",".join(issue["labels"])
    files_section = "\n".join(f"- `{f}`" for f in issue["files"])

    body = f"""{issue['body']}

**Relevant files:**
{files_section}

**Estimated effort:** {issue['effort']}
"""

    cmd = [
        "gh", "issue", "create",
        "--repo", repo,
        "--title", issue["title"],
        "--body", body,
        "--label", labels,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  Created: [{issue['id']}] {issue['title']}")
    else:
        print(f"  FAILED:  [{issue['id']}] {result.stderr.strip()}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed GitHub issues from manifest")
    parser.add_argument("--manifest", required=True, help="Path to issues_manifest.json")
    parser.add_argument("--repo", required=True, help="GitHub repo (org/name)")
    parser.add_argument("--dry-run", action="store_true", help="Print issues without creating them")
    args = parser.parse_args()

    with open(args.manifest) as f:
        issues = json.load(f)

    print(f"Seeding {len(issues)} issues into {args.repo}...")
    for issue in issues:
        if args.dry_run:
            print(f"  [DRY RUN] [{issue['id']}] {issue['title']}")
        else:
            create_issue(args.repo, issue)
            time.sleep(1)  # Rate limit: avoid hitting GitHub API limits

    print(f"Done. {len(issues)} issues {'would be' if args.dry_run else ''} created.")


if __name__ == "__main__":
    main()
