"""Protocol-level tests run the MCP client harness as an actual stdio subprocess."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_stdio_client_harness():
    completed = subprocess.run(
        [sys.executable, "scripts/test_client.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stdout + "\n" + completed.stderr
    assert "All MCP end-to-end checks passed." in completed.stdout
