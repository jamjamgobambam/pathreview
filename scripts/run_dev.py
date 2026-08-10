"""Start and supervise the backend and frontend development servers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def command(name: str) -> str:
    """Return an executable name that works with Windows command shims."""
    executable = f"{name}.cmd" if os.name == "nt" else name
    resolved = shutil.which(executable)
    if resolved is None:
        raise SystemExit(
            f"Required command '{name}' was not found on PATH. "
            "Install it and run 'make setup' again."
        )
    return resolved


def main() -> int:
    npm = command("npm")
    processes = [
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "api.main:app",
                "--reload",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ],
            cwd=ROOT,
        ),
        subprocess.Popen([npm, "run", "dev"], cwd=ROOT / "frontend"),
    ]

    try:
        while all(process.poll() is None for process in processes):
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    return next((process.returncode for process in processes if process.returncode), 0)


if __name__ == "__main__":
    raise SystemExit(main())
