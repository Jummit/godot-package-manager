"""Git utilities."""

import subprocess
import urllib
from pathlib import Path

def clone_repo(uri: str, to: Path, version: str | None = None):
    """Clone the given repository to the given path."""
    _run_git_command(f"clone {uri}", to)
    if version is not None:
        _run_git_command(f"checkout {version}", to / Path(uri).stem)


def get_latest_commit(repo: Path) -> str:
    """Return the latest commit id of the main branch."""
    return _run_git_command("rev-parse HEAD", repo)


def _run_git_command(command: str, working_directory: Path) -> str:
    """Runs a git command inside working_directory."""
    args = command.split(" ")
    args.insert(0, "git")
    result = subprocess.run(args, capture_output=True, cwd=working_directory, check=True)
    return result.stdout.decode('UTF-8')