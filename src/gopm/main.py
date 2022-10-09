from argparse import ArgumentParser
import shutil
import sys
import tempfile
from distutils.util import strtobool
from typing import List
from pathlib import Path
from gopm.search_provider import Result
from gopm.project import Project, Package
from gopm import git, github


tmp_repos_dir = Path(tempfile.gettempdir()) / "godot_packages"
if tmp_repos_dir.exists():
    shutil.rmtree(tmp_repos_dir)
tmp_repos_dir.mkdir()


search_providers = [github.GithubSearchProvider()]

def show_install_help():
    print("""No packages installed. Install them one like this:

    > gopm install search term

    or

    > gopm install /path/to/git/repo
    """)


def install(project: Project, search: List[str]):
    term = " ".join(search)
    installed = project.get_installed()
    path = Path(term)
    if path.is_dir():
        target = tmp_repos_dir / path.stem
        git.clone_repo(term, target)
        latest = git.get_latest_commit(target)
        if latest:
            project.save_packages(installed + [Package(term, latest)])
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
            print("No package selected")
            return
        selected = results[package_num - 1]
        package = Package(selected.url, selected.latest_version)
        project.save_packages(installed + [package])
        print(f"Installed {package.name}")
    project.update_packages(tmp_repos_dir)


def update(project: Project):
    if len(project.get_installed()) == 0:
        show_install_help()
    else:
        project.update_packages(tmp_repos_dir, sys.stdout)


def upgrade(project: Project):
    if len(project.get_installed()) == 0:
        show_install_help()
    else:
        project.upgrade_packages(tmp_repos_dir, sys.stdout)


def remove(project: Project, package: str):
    installed = project.get_installed()
    matches = list(filter(lambda p: package.lower() in p.name.lower(), installed))
    match len(matches):
        case 0:
            print(f"No package installed that contains the word {package}")
        case 1:
            match = matches[0]
            answer = input(f"Really remove {match.name}?\n[y/N]")
            if answer and strtobool(answer):
                installed.remove(match)
                project.save_packages(installed)
                print(f"Removed {match.name}")
        case _:
            print(f"Found multiple results, be more specific: {', '.join(map(lambda p: p.name, matches))}")


def list_packages(project: Project):
    installed = project.get_installed()
    if len(installed) == 0:
        show_install_help()
    for package in installed:
        print(f"{package.name} [{package.version}]")


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()
    update_parser = subparsers.add_parser("update", aliases=["u"],
            help="Download all packages inside the modules file")
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
        func(Project(Path()), **args)
        shutil.rmtree(tmp_repos_dir)
    except KeyError:
        parser.print_help()


if __name__ == "__main__":
    main()
