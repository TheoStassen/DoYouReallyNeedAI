import subprocess

from typing import Optional


def copilot_query(prompt: str, timeout: Optional[int] = 150, reset: bool = True) -> str:
    """
    Call the GitHub Copilot CLI and return its response as a string.
    Requirements:
      - Install github/copilot-cli and ensure `copilot` is on PATH.
      - Authenticate (e.g., `copilot auth login`) before running.
    Adjust the copilot subcommand/flags to match your installed CLI version.
    """

    cmd = ["copilot", "--prompt", prompt, "--allow-all-tools", "--model", "claude-haiku-4.5"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"copilot CLI failed: {proc.stderr.strip()}")
    return proc.stdout.strip()
