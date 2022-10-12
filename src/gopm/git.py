"""Git utilities."""

import subprocess
import urllib
from typing import List
from pathlib import Path

def clone_repo(uri: str, to: Path, version: str | None = None):
    """Clone the given repository to the given path."""
    _run_git_command(["clone", uri, str(to.absolute())])
    if version is not None:
        _run_git_command(["switch", "--detach", version], to)

def get_latest_commit(repo: Path) -> str:
    """Return the latest commit id of the main branch."""
    return _run_git_command(["rev-parse", "HEAD"], repo).strip()


def _run_git_command(args: List[str], working_directory = Path()) -> str:
    """Runs a git command inside working_directory."""
    args.insert(0, "git")
    result = subprocess.run(args, capture_output=True, cwd=working_directory,
            check=True)
    return result.stdout.decode('UTF-8')