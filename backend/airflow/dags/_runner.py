from __future__ import annotations

import json
import subprocess
from pathlib import Path

BACKEND_DIR = Path("/opt/fuelsight/backend")


def run_pipeline_command(*command_parts: str) -> dict:
    process = subprocess.run(
        ["uv", "run", "python", "-m", "app.scripts.pipeline_runner", *command_parts],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
        check=False,
    )

    if process.returncode != 0:
        stderr = process.stderr.strip()
        stdout = process.stdout.strip()
        detail = stderr or stdout or f"uv run exited with code {process.returncode}"
        raise RuntimeError(detail)

    stdout_lines = [line.strip() for line in process.stdout.splitlines() if line.strip()]
    if not stdout_lines:
        return {"status": "ok"}

    for line in reversed(stdout_lines):
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
            return payload.get("result", payload)
        except json.JSONDecodeError:
            continue

    return {"status": "ok", "raw_output": process.stdout.strip()}
