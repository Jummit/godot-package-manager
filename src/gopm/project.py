"""A representation of the packages a Godot project has installed."""

from pathlib import Path
from io import StringIO, TextIOBase
from gopm import git
from typing import List, Tuple
import shutil
import sys

class Package:
    """An installable Godot package."""

    def __init__(self, uri: str, version: str):
        "The Git URI the package can be cloned from."
        self.uri = uri
        "The Git commit of the package."
        self.version = version
        self.name = Path(uri).stem

class Project:
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

    def update_package(self, package: Package, tmp: Path, out = sys.stdout):
        """Clones or updates the given repository."""
        out.write(f"[{package.name}] version {package.version[:8]} from {package.uri}\n")
        target = tmp / package.name
        git.clone_repo(package.uri, tmp, package.version)

        target_addons = target / "addons"
        addons = self.path / "addons"
        addons.mkdir(exist_ok=True)
        for addon in target_addons.glob("*"):
            out.write(f"	Addon [{addon.stem}]\n")
            destination = addons / addon.name
            if destination.is_dir():
                shutil.rmtree(destination)
            shutil.copytree(addon, destination)
        project = Project(target)
        for package in project.get_installed():
            output = StringIO()
            self.update_package(package, tmp, output)
            out.write(output.read().replace("\n", "\n\t"))
        shutil.rmtree(target)

    def get_latest_version(self, tmp: Path, package: Package) -> str:
        """Clones the repositories of the package
        and returns the latest version available.
        """
        tmp.mkdir(parents=True, exist_ok=True)
        into = git.clone_repo(package.uri, tmp, package.version)
        latest = git.get_latest_commit(into)[:8]
        shutil.rmtree(into)
        if latest is None:
            return package.version
        return latest

    def install_package(self, package: Package):
        """Adds a package to the godotmodules file."""
        self.save_packages(self.get_installed() + [package])

    def save_packages(self, packages: List[Package]):
        with open(self.modules_file, "w") as file:
            file.writelines(list(map(lambda x: f"{x.uri} {x.version}\n",
                    packages)))
