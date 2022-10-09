from pathlib import Path
from io import StringIO, TextIOBase
from gopm import git
from typing import List
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

    def update_packages(self, tmp: Path, out = sys.stdout):
        """Clones or updates the repositories listed in `modules_file`
        and installs the addons of the module.
        """
        for package in self.get_installed():
            self.update_package(package, out, tmp)

    def update_package(self, package: Package, out: StringIO, tmp: Path):
        """Clones or updates the given repository."""
        out.write(f"[{package.name}] version {package.version[:6]} from {package.uri}\n")
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
            self.update_package(package, output, tmp)
            out.write(output.read().replace("\n", "\n\t"))
        shutil.rmtree(target)

    def upgrade_packages(self, tmp: Path, out = sys.stdout):
        """Clones the repositories listed in `modules_file`
        and changes the version if there is a new commit.
        """
        to_upgrade = tmp / "to_upgrade"
        to_upgrade.mkdir()
        for package in self.get_installed():
            git.clone_repo(package.uri, to_upgrade, package.version)
            latest = git.get_latest_commit(to_upgrade / package.name)[:10]
            if latest is None:
                continue
            shutil.rmtree(to_upgrade)
            out.write(f"Upgrading {package.name} to {latest}\n")
            package.version = latest

    def install_package(self, package: Package):
        """Adds a package to the godotmodules file."""
        self.save_packages(self.get_installed() + [package])

    def save_packages(self, packages: List[Package]):
        with open(self.modules_file, "w") as file:
            file.writelines(list(map(lambda x: f"{x.uri} {x.version}\n", packages)))
