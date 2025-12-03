import subprocess

from typing import Optional, Sequence


def copilot_query(
    prompt: str,
    timeout: Optional[int] = 150,
    reset: bool = True,
    model: Optional[str] = None,
    extra_args: Optional[Sequence[str]] = None,
) -> str:
    """
    Call the GitHub Copilot CLI and return its response as a string.
    Requirements:
      - Install github/copilot-cli and ensure `copilot` is on PATH.
      - Authenticate (e.g., `copilot auth login`) before running.
    Adjust the copilot subcommand/flags to match your installed CLI version.

    New options:
      - model: override the model name used by the CLI (default kept for backward compat).
      - extra_args: list of extra arguments/flags to pass to the `copilot` binary.
    """

    base_model = "gpt-5.1-codex-mini"
    chosen_model = model or base_model

    cmd = ["copilot", "--prompt", prompt, "--allow-all-tools", "--model", chosen_model]
    if not reset:
        cmd.append("--continue")
    if extra_args:
        cmd.extend(list(extra_args))

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"copilot CLI failed: {proc.stderr.strip()}")
    return proc.stdout.strip()
