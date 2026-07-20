"""
Generate baseline hashes for prompt_templates snapshot tests.

Run this to (re)create tests/unit/prompt_template_snapshots.py:

    python -m tests.unit.generate_prompt_snapshots

Only run this when you're intentionally accepting new/changed template
content. If you're changing prompt behavior for an existing template,
bump its version key (v1 -> v2) in PROMPT_TEMPLATES first, so the old
v1 hash stays as a record of what shipped before.
"""
import hashlib
from pathlib import Path

from rag.generator.prompt_templates import PROMPT_TEMPLATES


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def main():
    lines = [
        '"""',
        "Snapshot hashes for prompt templates.",
        "",
        "Regenerate with: python -m tests.unit.generate_prompt_snapshots",
        "",
        "Only regenerate when you've intentionally added/changed a version key.",
        'If a hash here changes for an EXISTING version (e.g. "v1" -> new hash)',
        "without a new version key being added, that's the exact thing this",
        "snapshot system exists to catch — don't just silently regenerate it.",
        '"""',
        "",
        "TEMPLATE_SNAPSHOTS = {",
    ]
    for name in sorted(PROMPT_TEMPLATES.keys()):
        lines.append(f'    "{name}": {{')
        for version in sorted(PROMPT_TEMPLATES[name].keys()):
            h = compute_hash(PROMPT_TEMPLATES[name][version])
            lines.append(f'        "{version}": "{h}",')
        lines.append("    },")
    lines.append("}")
    lines.append("")

    out_path = Path(__file__).parent / "prompt_template_snapshots.py"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()