"""Git utilities."""

import subprocess
import urllib
from typing import List
from pathlib import Path

def clone_repo(uri: str, to: Path, version: str | None = None):
    """Clone the given repository to the given path.

    When passed, version will be switched to in a detached HEAD state.
    """
    _run_git_command(["clone", uri, str(to.absolute())])
    if version is not None:
        _run_git_command(["switch", "--detach", version], to)


def get_latest_commit(repo: Path) -> str:
    """Return the hash of the current commit of the main branch."""
    return _run_git_command(["rev-parse", "HEAD"], repo).strip()


def _run_git_command(args: List[str], working_directory = Path()) -> str:
    """Run a Git command inside working_directory.

    Returns the content of stdout after running the command.
    """
    args.insert(0, "git")
    result = subprocess.run(args, capture_output=True, cwd=working_directory,
            check=True)
    return result.stdout.decode('UTF-8')