"""Regenerate the prompt template snapshot.

Computes a hash for every version of every template in
``rag.generator.prompt_templates.PROMPT_TEMPLATES`` and writes them to
``tests/unit/snapshots/prompt_templates.json``.

The resulting file maps each template name to a dict of version -> hash, e.g.::

    {
      "skills_feedback": { "v1": "3f2a..." },
      "projects_feedback": { "v1": "9b1c..." }
    }

Run this after intentionally changing a template (and bumping its version) to
record the new snapshot::

    python scripts/update_prompt_snapshot.py
"""

import json
from pathlib import Path

from rag.generator.prompt_templates import PROMPT_TEMPLATES, snapshot_hashes

# tests/unit/snapshots/prompt_templates.json, resolved relative to this file so
# the script works regardless of the current working directory.
SNAPSHOT_PATH = (
    Path(__file__).resolve().parent.parent
    / "tests"
    / "unit"
    / "snapshots"
    / "prompt_templates.json"
)


def build_snapshot() -> dict:
    """Compute the hash of every template version.

    Returns:
        Mapping of template name -> {version: hash}.
    """
    snapshot: dict = {}
    for name, versions in PROMPT_TEMPLATES.items():
        snapshot[name] = {
            version: snapshot_hashes(template_text) for version, template_text in versions.items()
        }
    return snapshot


def write_snapshot(snapshot: dict, path: Path = SNAPSHOT_PATH) -> None:
    """Write the snapshot to disk as pretty-printed JSON.

    Args:
        snapshot: Mapping of template name -> {version: hash}.
        path: Destination file for the JSON snapshot. Defaults to
            ``SNAPSHOT_PATH``.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, sort_keys=True)
        f.write("\n")


def main() -> None:
    """Build the snapshot and write it to ``SNAPSHOT_PATH``.

    Intended as the script entry point; prints a summary of how many
    templates were written.
    """
    snapshot = build_snapshot()
    write_snapshot(snapshot)
    print(f"Wrote snapshot for {len(snapshot)} templates to {SNAPSHOT_PATH}")


if __name__ == "__main__":
    main()
