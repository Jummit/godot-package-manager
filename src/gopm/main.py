"""The main command line interface of the package manager."""

import shutil
import sys
import tempfile

from argparse import ArgumentParser
from gopm import git
from gopm import Project, Package
from gopm.search.github import GithubSearchProvider
from gopm.search.search_provider import Result, SearchProvider
from pathlib import Path
from subprocess import CalledProcessError
from typing import List, Tuple

tmp_repos_dir = Path(tempfile.gettempdir()) / "godot_packages"
search_providers = [GithubSearchProvider()]

def show_install_help():
    """Print information on how to use the utility."""

    print("""No packages installed. Install one like this:

    > gopm install [search term]

    or

    > gopm install /path/to/git/repo.git
    """)


def download_addons(project: Project, package: Package, indent: int = 0):
    """Download addons of a project and their dependencies."""
    indent_str = '\t' * indent
    version = package.version[:8]
    print(f"{indent_str}[{package.name}] version {version} from {package.uri}")
    (addons, depedencies) = project.download_addons(package, tmp_repos_dir)
    for addon in addons:
        print(f"\t{indent_str}Addon [{addon}]")
    if len(addons) == 0:
        print(f"\t{indent_str}Package contains no addons.")
    for dependency in depedencies:
        download_addons(project, dependency, indent + 1)


def install(project: Project, search: List[str]):
    """Install a package from a path or select from a list of
    repositories matching the search.
    """
    term = " ".join(search)
    installed = project.get_installed()
    path = Path(term)
    package : Package
    if path.is_dir():
        package = Package(term, "")
        package.version = package.get_latest_version(tmp_repos_dir)
    else:
        results : List[Result] = []
        for provider in search_providers:
            results += provider.get_matches(term)
        if len(results) == 0:
            return print("No packages found")
        print("\n".join(map(
                lambda x: f"[{x[0] + 1}] {x[1].name}\n\t{x[1].description}",
                enumerate(results))))
        try:
            package_num = int(input("Package to install: "))
        except (ValueError, KeyboardInterrupt):
            return print("No package selected")
        selected = results[package_num - 1]
        package = Package(selected.url, selected.latest_version)
    if any(map(lambda x: x.name == package.name, installed)):
        return print("Package is already installed.")
    project.save_packages(installed + [package])
    download_addons(project, package)
    print(f"Installed {package.name}")


def update(project: Project):
    """Download the addons of the installed packages."""
    if len(project.get_installed()) == 0:
        show_install_help()
    else:
        for package in project.get_installed():
            download_addons(project, package)


def upgrade(project: Project):
    """Update the addons of the installed packages to the latest
    version.
    """
    if len(project.get_installed()) == 0:
        return show_install_help()
    packages = project.get_installed()
    for package in packages:
        latest = package.get_latest_version(tmp_repos_dir)
        if package.version == latest:
            print(f"{package.name} is up-to-date.")
            continue
        print(f"Upgrading {package.name} from {package.version} to {latest}")
        package.version = latest
        download_addons(project, package)
    project.save_packages(packages)


def remove(project: Project, package: str):
    """Remove a package that contains a query."""
    installed = project.get_installed()
    matches = list(filter(lambda p: package.lower() in p.name.lower(),
            installed))
    match len(matches):
        case 0:
            print(f'No package installed that contains the word "{package}"')
        case 1:
            match = matches[0]
            answer = input(f'Really remove "{match.name}"?\n[y/N] ')
            if answer and answer.lower() in {"y", "yes"}:
                installed.remove(match)
                project.save_packages(installed)
                print(f"Removed {match.name}")
        case _:
            names = ', '.join(map(lambda p: p.name, matches))
            print(f"Found multiple results, be more specific: {names}")


def list_packages(project: Project):
    """Print a list of installed packages."""
    installed = project.get_installed()
    if len(installed) == 0:
        show_install_help()
    for package in installed:
        print(f"{package.name} [{package.version}]")


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()
    update_parser = subparsers.add_parser("update", aliases=["u"],
            help=("Download all packages inside the modules file and installs" +
                 " their addons. WARNING: Existing addons with the same name" +
                 " will be moved to the trash."))
    update_parser.set_defaults(func=update)
    upgrade_parser = subparsers.add_parser("upgrade", aliases=["s"],
            help="Update all packages to the latest version")
    upgrade_parser.set_defaults(func=upgrade)
    list_parser = subparsers.add_parser("list", aliases=["l"],
            help="List the installed packages")
    list_parser.set_defaults(func=list_packages)
    install_parser = subparsers.add_parser("install", aliases=["i"],
            help="Install a package from a git URI or search and install a\
            package from Github")
    install_parser.add_argument("search",
            help="Git URI or name to search on Github", nargs="+")
    install_parser.set_defaults(func=install)
    remove_parser = subparsers.add_parser("remove", aliases=["r"],
            help="Uninstall the specified package")
    remove_parser.add_argument("package",
            help="Name to match in the modules file")
    remove_parser.set_defaults(func=remove)

    args = vars(parser.parse_args())
    try:
        func = args.pop("func")
    except KeyError:
        return parser.print_help()

    if tmp_repos_dir.exists():
        shutil.rmtree(tmp_repos_dir)
    tmp_repos_dir.mkdir()
    try:
        func(Project(Path()), **args)
    except CalledProcessError as e:
        err = e.stderr.decode("unicode_escape").strip()
        cmd = " ".join(e.cmd)
        print(f'Error running Git command "{cmd}":\n\t{err}')
    shutil.rmtree(tmp_repos_dir)


if __name__ == "__main__":
    main()
