#!/usr/bin/env python3
import os
import subprocess
import shutil
import sys
import requests
import json
import tempfile

verbose = "--verbose" in sys.argv or "-v" in sys.argv
if verbose:
    def print_verbose(*args):
        for arg in args:
            print(arg)
else:   
    print_verbose = lambda *a: None

tmp_repos_dir = os.path.join(tempfile.gettempdir(), "godot_packages")
if not os.path.exists(tmp_repos_dir):
    os.mkdir(tmp_repos_dir)
project_dir = os.getcwd()

def run_git_command(command, working_directory):
    """
    Runs a git command inside `working_directory`. If `verbose` is false,
    passes the --quiet option to the command.
    """
    print_verbose("Running git " + command + " inside " + working_directory)
    args = command.split(" ")
    args.insert(0, "git")
    if not verbose:
        args.append("-q")
    return subprocess.run(
            args, cwd=working_directory, stdout=subprocess.PIPE).stdout


def update_packages(modules_file, indent=0):
    """
    Clones or updates the repositories listed in `modules_file`
    and installs the addons of the module.
    """
    with open(modules_file, "r") as file:
        for package in file:
            update_package(package)


def update_package(package, indent=0):
    """
    Clones or updates the given repository.
    """
    if package.isspace():
        return
    repo, version = package.strip().split(" ")
    if "/.git" in repo:
        # Get the name of a local git repo like `/path/to/repo/.git`.
        name = repo.split("/")[-2]
    else:
        # Get the name of a git url like `https://github.com/user/repo.git`
        name = repo.split("/")[-1].split(".")[-2]
    print("	" * indent + f"[{name}] version {version[:6]} from {repo}")
    run_git_command(f"clone {repo}", f"{tmp_repos_dir}")
    run_git_command(f"checkout {version}", f"{tmp_repos_dir}/{name}")

    for addon in os.listdir(f"{tmp_repos_dir}/{name}/addons"):
        print("	" * indent + f"	addon [{addon}]")
        destination = f"{project_dir}/addons/{addon}"
        if os.path.isdir(destination):
            shutil.rmtree(destination)
        shutil.copytree(f"{tmp_repos_dir}/{name}/addons/{addon}", destination)
    shutil.rmtree(f"{tmp_repos_dir}/{name}")
    
    submodule_file = f"{tmp_repos_dir}/{name}/godotmodules.txt"
    if os.path.isfile(submodule_file):
        update_packages(submodule_file, indent + 1)


def upgrade_packages(modules_file, indent=0):
    """
    Clones the repositories listed in `modules_file`
    and changes the version if there is a new commit.
    """
    with open(modules_file, "r") as file:
        for package in file:
            if package:
                upgrade_package(package)


def upgrade_package(package):
    """
    Clones the given repository and puts the version in the godotmodules file.
    """
    repo = package.split()[0]
    run_git_command(f"clone {repo} to_upgrade", f"{tmp_repos_dir}")
    latest_commit = run_git_command("rev-parse HEAD",
            f"{tmp_repos_dir}/to_upgrade").decode('UTF-8')[:7]
    shutil.rmtree(f"{tmp_repos_dir}/to_upgrade")
    print(f"Upgrading {repo} to {latest_commit}")
    
    modules = ""
    with open(f"{project_dir}/godotmodules.txt", "r") as modulesfile:
        for line in modulesfile.readlines():
            if package.strip() in line:
                modules += f"{repo} {latest_commit}\n"
            else:
                modules += line
    with open(f"{project_dir}/godotmodules.txt", "w") as modulesfile:
        modulesfile.write(modules)


def install_package(name):
    """
    Adds a package to the godotmodules file.
    """
    open(f"{project_dir}/godotmodules.txt", 'a').close()
    with open(f"{project_dir}/godotmodules.txt", "r+") as modulesfile:
        if any((name in line) for line in modulesfile):
            print("Already installed")
            return
        else:
            print(f"Installed {name}")
            modulesfile.write(name + "\n")


def browse_github(name):
    """
    Searches Github for packages and asks the user which one to install.
    """
    query = f"https://api.github.com/search/repositories?q={name} language:GDScript&per_page=10"
    print_verbose("query: " + query)
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
    last_commit = requests.get(selected.get("commits_url").replace('{/sha}', "")).json()[0].get("sha")[:7]
    dependency = f"{selected['clone_url']} {last_commit}"
    print_verbose(dependency)
    install_package(dependency)


def remove_package(addon):
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
            print_verbose(f"Removed {line}")
            repo, version = line.strip().split(" ")
            if "/.git" in repo:
                # Get the name of a local git repo like `/path/to/repo/.git`.
                name = repo.split("/")[-2]
            else:
                # Get the name of a git url like `https://github.com/user/repo.git`
                name = repo.split("/")[-1].split(".")[-2]
            print_verbose(f"Cloning {repo} into {tmp_repos_dir}")
            run_git_command(f"clone {repo}", f"{tmp_repos_dir}")
            run_git_command(f"checkout {version}", f"{tmp_repos_dir}/{name}")
            for addon in os.listdir(f"{tmp_repos_dir}/{name}/addons"):
                shutil.rmtree(f"{project_dir}/addons/{addon}")
                print(f"Removed [{addon}]")
            shutil.rmtree(f"{tmp_repos_dir}/{name}")
    with open(f"{project_dir}/godotmodules.txt", "w") as modulesfile:
        modulesfile.write(modules)


def show_help():
    """Shows the command line usage of the program."""
    print("Usage: gopm [COMMAND] [-v] <package> ...")
    print("u / update         Download all packages")
    print("s / upgrade        Upgrade all packages to the latest version")
    print("i / install        Install a package from a git URI or search and install a package from Github")
    print("r / remove         Uninstall the specified package")
    print("-v / --verbose        Enable verbose logging")
    print("-h / --help           Show this help message")

MODES = {
    "update": ["u", "update"],
    "upgrade": ["s", "upgrade"],
    "install": ["i", "install"],
    "remove": ["r", "remove"],
    "help": ["-h", "--help"],
}

def main():
    mode = "help"
    for possible_mode in MODES:
        for flag in MODES[possible_mode]:
            if flag in sys.argv:
                mode = possible_mode
                break
    package = ""
    allflags = ["-v", "--verbose"]
    for flags in MODES.values():
        allflags += flags
    for arg in sys.argv[1:]:
        if not arg in allflags:
            package += arg + " "

    if mode in ["install", "remove"] and not package:
        return print("No package specified")

    modules_file = f"{project_dir}/godotmodules.txt"
    if mode in ["update", "upgrade", "remove"] and not os.path.isfile(modules_file):
        return print("No packages installed")

    if mode == "update":
        update_packages(modules_file)
    elif mode == "upgrade":
        upgrade_packages(modules_file)
    elif mode == "install":
        if package.endswith(".git"):
            install_package(package)
        else:
            browse_github(package)
        update_packages(modules_file)
    elif mode == "remove":
        remove_package(package)
    elif mode == "help":
        show_help()

    os.rmdir(tmp_repos_dir)

if __name__ == "__main__":
    main()
