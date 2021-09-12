#!/usr/bin/env python3.9
import os
import subprocess
import shutil
import sys
import requests
import json
import tempfile

verbose = "--verbose" in sys.argv or "-v" in sys.argv
try:
    sys.argv.remove("--verbose")
    sys.argv.remove("-v")
except ValueError:
    pass
project_dir = os.getcwd()
tmp_repos_dir = os.path.join(tempfile.gettempdir(), "godot_packages")

if verbose:
    def print_verbose(*args):
        for arg in args:
            print(arg)
else:   
    print_verbose = lambda *a: None

def run_git_command(command, working_directory):
    """
    Runs a git command inside `working_directory`. If `verbose` is false,
    passes the --quiet option to the command.
    """
    args = command.split(" ")
    args.insert(0, "git")
    if not verbose:
        args.append("-q")
    subprocess.run(args, cwd=working_directory)


def update_packages(modules_file, indent=0):
    """
    Clones or updates the repositories listed in `modules_file`
    and installs the addons of the module.
    """
    try:
        with open(modules_file, "r") as file:
            for package in file:
                update_package(package)
    except FileNotFoundError:
        print("no packages installed")


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
    print_verbose(f"cloning {repo}")
    if os.path.isdir(f"{tmp_repos_dir}/{name}"):
            shutil.rmtree(f"{tmp_repos_dir}/{name}")
    run_git_command(f"clone {repo}", f"{tmp_repos_dir}")
    run_git_command(f"checkout {version}", f"{tmp_repos_dir}/{name}")

    for addon in os.listdir(f"{tmp_repos_dir}/{name}/addons"):
        print("	" * indent + f"	addon [{addon}]")
        destination = f"{project_dir}/addons/third_party/{addon}"
        if os.path.isdir(destination):
            shutil.rmtree(destination)
        shutil.copytree(f"{tmp_repos_dir}/{name}/addons/{addon}", destination)
    shutil.rmtree(f"{tmp_repos_dir}/{name}")
    
    submodule_file = f"{tmp_repos_dir}/{name}/godotmodules.txt"
    if os.path.isfile(submodule_file):
        update_packages(submodule_file, indent + 1)


def install_package(name):
    """
    Adds a package to the godotmodules file.
    """
    open(f"{project_dir}/godotmodules.txt", 'a').close()
    with open(f"{project_dir}/godotmodules.txt", "r+") as modulesfile:
        if any((name in line) for line in modulesfile):
            print("already installed")
            return
        else:
            print(f"installed {name}")
            modulesfile.write(name + "\n")


def browse_github(name):
    """
    Searches Github for packages and asks the user which one to install.
    """
    query = f"https://api.github.com/search/repositories?q={name} language:GDScript&per_page=10"
    print_verbose(query)
    text = requests.get(query).text
    items = json.loads(text).get("items")
    if len(items) == 0:
        print("no modules found")
        return
    for result_num in range(len(items)):
        result = items[result_num]
        print(f"[{result_num + 1}] {result['full_name']}")
        print(f"    {result['description']}")
    try:
        package_num = int(input("Package to install [1]: "))
    except ValueError:
        package_num = 1
    selected = items[package_num - 1]
    dependency = f"{selected['clone_url']} {selected['default_branch']}"
    install_package(dependency)


def remove_package(addon):
    """
    Removes a package from the godotmodules file.
    """
    modules = ""
    try:
        with open(f"{project_dir}/godotmodules.txt", "r") as modulesfile:
            for line in modulesfile.readlines():
                if line == "":
                    continue
                if not addon in line.lower():
                    modules += line
                    continue
                print_verbose(f"removed {line}")
                repo, version = line.strip().split(" ")
                if "/.git" in repo:
                    # Get the name of a local git repo like `/path/to/repo/.git`.
                    name = repo.split("/")[-2]
                else:
                    # Get the name of a git url like `https://github.com/user/repo.git`
                    name = repo.split("/")[-1].split(".")[-2]
                print_verbose(f"cloning {repo} into {tmp_repos_dir}")
                run_git_command(f"clone {repo}", f"{tmp_repos_dir}")
                run_git_command(f"checkout {version}", f"{tmp_repos_dir}/{name}")
                for addon in os.listdir(f"{tmp_repos_dir}/{name}/addons"):
                    shutil.rmtree(f"{project_dir}/addons/third_party/{addon}")
                    print(f"removed [{addon}]")
                shutil.rmtree(f"{tmp_repos_dir}/{name}")
        with open(f"{project_dir}/godotmodules.txt", "w") as modulesfile:
            modulesfile.write(modules)
    except FileNotFoundError:
        print("no packages installed")

MODES = {
    "update": ["-u", "--update"],
    "install": ["-i", "--install"],
    "remove": ["-r", "--remove"],
    "help": ["-h", "--help"],
}
mode = "help"
for possible_mode in MODES:
    for flag in MODES[possible_mode]:
        if flag in sys.argv:
            mode = possible_mode
            break
package = ""
for arg in sys.argv[1:]:
    # TODO: Support file names with - in their name.
    if not "-" in arg:
        package += arg + " "

if mode != "help":
    try:
        print_verbose("creating addons folder")
        os.mkdir(f"{project_dir}/addons")
        os.mkdir(f"{project_dir}/addons/third_party")
    except (FileExistsError):
        print_verbose("addons folder already existed")

if mode in ["install", "remove"] and not package:
    print("no package specified")
    exit()

if mode == "update":
    update_packages(f"{project_dir}/godotmodules.txt")
elif mode == "install":
    if package.endswith(".git"):
        install_package(package)
    else:
        browse_github(package)
    update_packages(f"{project_dir}/godotmodules.txt")
elif mode == "remove":
    remove_package(package)
elif mode == "help":
    print("Usage: gopm {-u|-i|-r} [-v] <package> ...")
    print("-u / --update    Update all packages")
    print("-i / --install   Install a package from a git URI or search and install a package from Github")
    print("-r / --remove    Uninstall the specified package")
    print("-v / --verbose   Enable verbose logging")
    print("-h / --help      Show this help message")