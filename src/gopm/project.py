"""A representation of the packages a Godot project has installed."""

from pathlib import Path
from gopm import git
from typing import List, Tuple
from send2trash import send2trash
import random
import shutil

class Package:
    """An installable Godot package."""

    def __init__(self, uri: str, version: str):
        "The Git URI the package can be cloned from."
        self.uri = uri
        "The Git commit of the package."
        self.version = version
        self.name = Path(uri).stem

    def get_latest_version(self, tmp: Path) -> str:
       """Clones the repositories of the package and returns the
       latest version available.
       """
       repo = tmp / self.name
       git.clone_repo(self.uri, repo)
       latest = git.get_latest_commit(repo)[:8]
       shutil.rmtree(repo)
       return latest


class Project:
    """A Godot project with a list of installed packages."""

    def __init__(self, path: Path):
        self.path = path
        self.modules_file = path / "godotmodules.txt"

    def get_installed(self) -> List[Package]:
        """Reads the modules file and lists the installed packages."""
        try:
            with open(self.modules_file) as file:
                return list(map(lambda x: Package(*x.split()),
                        filter(lambda x: x.strip() != "", file)))
        except FileNotFoundError:
            return []

    def download_addons(self, package: Package, tmp: Path
            ) -> Tuple[List[str], List[Package]]:
        """Install the addons of a package.
        
        Clones the repository of the package and copies the addons
        inside the addons folder into the project. Returns the list
        of installed addons and the dependencies of the package.
        `tmp` is the folder into which the repository will be cloned.
        
        Existing addons with the same name as installed addons will be
        moved to the trash.

        *Example:*

        ```python
        (addons, dependencies) = project.download_addons(package, Path())
        ```
        """
        repo = tmp / package.name
        git.clone_repo(package.uri, repo, package.version)
        addons = self.path / "addons"
        addons.mkdir(exist_ok=True)
        addon_names : List[str] = []
        for addon in (repo / "addons").glob("*"):
            addon_names.append(addon.stem)
            destination = addons / addon.name
            if destination.is_dir():
                send2trash(destination)
            shutil.copytree(addon, destination)
        project = Project(repo)
        sub_packages = project.get_installed()
        shutil.rmtree(repo)
        return (addon_names, sub_packages)


    def save_packages(self, packages: List[Package]):
        """Writes the package list to the godotmodules.txt file."""
        with open(self.modules_file, "w") as file:
            file.writelines(map(lambda x: f"{x.uri} {x.version}\n", packages))
