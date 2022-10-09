#!/usr/bin/env python3
from argparse import ArgumentParser
import os
import subprocess
import shutil
import sys
import requests
import json
import tempfile
from pathlib import Path


tmp_repos_dir = Path(tempfile.gettempdir()) / "godot_packages"
if not os.path.exists(tmp_repos_dir):
    os.mkdir(tmp_repos_dir)
project_dir = Path(os.getcwd())
modules_file = project_dir / "godotmodules.txt"


def check_modules_file():
    if not modules_file.is_file():
        print("""No packages installed. Install them one like this:

    > gopm install search term

    or

    > gopm install /path/to/git/repo
    """)
        sys.exit(1)


def run_git_command(command: str, working_directory: Path, verbose: bool) -> str | None:
    """
    Runs a git command inside `working_directory`. If `verbose` is false,
    passes the --quiet option to the command.
    """
    if verbose:
        print(f"Running git {command} inside {working_directory}")
    args = command.split(" ")
    args.insert(0, "git")
    if not verbose:
        args.append("-q")
    result = subprocess.run(args, cwd=working_directory,
            stdout=subprocess.PIPE)
    if result.returncode and result.returncode != 128:
        return None
    return result.stdout.decode('UTF-8')


def update_root_packages(args, verbose):
    update_packages(verbose, Path("godotmodules.txt"))


def update_packages(verbose, file: Path = modules_file, indent: int = 0):
    """
    Clones or updates the repositories listed in `modules_file`
    and installs the addons of the module.
    """
    check_modules_file()
    with open(file) as f:
        for package in filter(lambda x: not x.isprintable(), f):
            update_package(verbose, package.strip())


def update_package(verbose, package: str, indent: int = 0):
    """
    Clones or updates the given repository.
    """
    repo, version = package.split(" ")
    if repo.endswith(".git"):
        # Get the name of a git url like `https://github.com/user/repo.git`
        name = repo.split("/")[-1].split(".")[-2]
    else:
        name = repo.split("/")[-1]
    print("	" * indent + f"[{name}] version {version[:6]} from {repo}")
    if run_git_command(f"clone {repo}", tmp_repos_dir, verbose) is None:
        return
    run_git_command(f"checkout {version}", tmp_repos_dir / name, verbose)

    for addon in os.listdir(f"{tmp_repos_dir}/{name}/addons"):
        print("	" * indent + f"	addon [{addon}]")
        destination = f"{project_dir}/addons/{addon}"
        if os.path.isdir(destination):
            shutil.rmtree(destination)
        shutil.copytree(f"{tmp_repos_dir}/{name}/addons/{addon}", destination)
    shutil.rmtree(f"{tmp_repos_dir}/{name}")
    deps = tmp_repos_dir / "godotmodules.txt"
    if deps.is_file():
        update_packages(verbose, deps, indent + 1)


def upgrade_packages(args, verbose):
    """
    Clones the repositories listed in `modules_file`
    and changes the version if there is a new commit.
    """
    check_modules_file()
    with open(modules_file) as file:
        for package in filter(lambda x: not x.isprintable(), file):
            if package.strip().isprintable():
                upgrade_package(package.strip(), verbose)


def upgrade_package(package, verbose):
    """
    Clones the given repository and puts the version in the godotmodules file.
    """
    repo = package.split()[0]
    to_upgrade = Path(f"{tmp_repos_dir}/to_upgrade")
    if run_git_command(f"clone {repo} to_upgrade", f"{tmp_repos_dir}", verbose) is None:
        return
    latest_commit = run_git_command("rev-parse HEAD", to_upgrade, verbose)[:7]
    shutil.rmtree(to_upgrade)
    print(f"Upgrading {repo} to {latest_commit}")

    modules = ""
    with open(f"{project_dir}/godotmodules.txt", "r") as modulesfile:
        for line in modulesfile.readlines():
            if package in line:
                modules += f"{repo} {latest_commit}\n"
            else:
                modules += line
    with open(f"{project_dir}/godotmodules.txt", "w") as modulesfile:
        modulesfile.write(modules)


def install_package(package):
    """
    Adds a package to the godotmodules file.
    """
    open(f"{project_dir}/godotmodules.txt", 'a').close()
    with open(f"{project_dir}/godotmodules.txt", "r+") as modulesfile:
        if any((package in line) for line in modulesfile):
            print("Already installed")
            return
        else:
            print(f"Installed {package}")
            modulesfile.write(package + " master\n")


def browse_github(name, verbose):
    """
    Searches Github for packages and asks the user which one to install.
    """
    query = f"https://api.github.com/search/repositories?q=\
{name} language:GDScript&per_page=10"
    if verbose:
        print("query: " + query)
    text = requests.get(query).text
    items = json.loads(text).get("items")
    if len(items) == 0:
        print("No packages found")
        return
    for result_num in range(len(items)):
        result = items[result_num]
        print(f"[{result_num + 1}] {result['full_name']}")
        print(f"    {result['description']}")
    try:
        package_num = int(input("Package to install: "))
    except ValueError:
        print("No package selected")
        return
    selected = items[package_num - 1]
    commits_url = selected.get("commits_url").replace('{/sha}', "")
    last_commit = requests.get(commits_url).json()[0].get("sha")[:7]
    dependency = f"{selected['clone_url']} {last_commit}"
    if verbose:
        print(dependency)
    install_package(dependency)


def remove_package(addon, verbose):
    """
    Removes a package from the godotmodules file.
    """
    modules = ""
    if not os.path.isfile(f"{project_dir}/godotmodules.txt"):
        return print("No packages installed")
    with open(f"{project_dir}/godotmodules.txt", "r") as modulesfile:
        for line in modulesfile.readlines():
            if line == "":
                continue
            if not addon.strip().lower() in line.lower():
                modules += line
                continue
            if verbose:
                print(f"Removed {line}")
            repo, version = line.strip().split(" ")
            if "/.git" in repo:
                # Get the name of a local git repo like `/path/to/repo/.git`.
                name = repo.split("/")[-2]
            else:
                # Get the name of a git url like
                # `https://github.com/user/repo.git`.
                name = repo.split("/")[-1].split(".")[-2]
            if verbose:
                print(f"Cloning {repo} into {tmp_repos_dir}")
            run_git_command(f"clone {repo}", f"{tmp_repos_dir}", verbose)
            run_git_command(f"checkout {version}", f"{tmp_repos_dir}/{name}",
                            verbose)
            for addon in os.listdir(f"{tmp_repos_dir}/{name}/addons"):
                shutil.rmtree(f"{project_dir}/addons/{addon}")
                print(f"Removed [{addon}]")
            shutil.rmtree(f"{tmp_repos_dir}/{name}")
    with open(f"{project_dir}/godotmodules.txt", "w") as modulesfile:
        modulesfile.write(modules)


def install(args, verbose):
    if os.path.exists(args.package):
        install_package(args.package)
    else:
        browse_github(args.package, verbose)
    update_packages(verbose)


def main():
    parser = ArgumentParser()
    parser.add_argument("-v", "--verbose", action='store_true',
                        help='Enable verbose logging')
    subparsers = parser.add_subparsers()
    update_parser = subparsers.add_parser("update", aliases=["u"], help="\
            Download all packages")
    update_parser.set_defaults(func=update_root_packages)
    upgrade_parser = subparsers.add_parser("upgrade", aliases=["s"], help="\
            Upgrade all packages to the latest version")
    upgrade_parser.set_defaults(func=upgrade_packages)
    install_parser = subparsers.add_parser("install", aliases=["i"], help="\
            Install a package from a git URI or search and install a package\
            from Github")
    install_parser.add_argument("package", help="\
            Git URI or name to search on Github")
    install_parser.set_defaults(func=install)
    remove_parser = subparsers.add_parser("remove", aliases=["r"], help="\
            Uninstall the specified package")
    remove_parser.add_argument("package", help="\
            Name to match in the modules file")
    remove_parser.set_defaults(func=remove_package)
    args = parser.parse_args()

    if "func" in args:
        args.func(args, args.verbose)
        shutil.rmtree(tmp_repos_dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
