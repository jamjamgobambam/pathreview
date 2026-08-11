import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def terminate_process(proc: subprocess.Popen[Any]) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        proc.terminate()
    else:
        os.killpg(proc.pid, signal.SIGTERM)  # type: ignore[attr-defined]
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            proc.kill()
        else:
            os.killpg(proc.pid, signal.SIGKILL)  # type: ignore[attr-defined]
        proc.wait(timeout=5)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "api.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]
    frontend_cmd = ["npm.cmd", "run", "dev"] if os.name == "nt" else ["npm", "run", "dev"]

    print("Starting backend and frontend dev servers...")

    backend = subprocess.Popen(
        backend_cmd,
        cwd=repo_root,
        stdout=None,
        stderr=None,
        stdin=None,
        start_new_session=os.name != "nt",
    )
    frontend = subprocess.Popen(
        frontend_cmd,
        cwd=repo_root / "frontend",
        stdout=None,
        stderr=None,
        stdin=None,
        start_new_session=os.name != "nt",
    )

    try:
        while True:
            backend.poll()
            frontend.poll()
            if backend.returncode is not None and frontend.returncode is not None:
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping dev servers...")
    finally:
        if backend.poll() is None:
            terminate_process(backend)
        if frontend.poll() is None:
            terminate_process(frontend)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
