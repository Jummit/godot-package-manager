#!/usr/bin/env python
import os
import subprocess
import shutil
import sys
import requests
import json

verbose = "--verbose" in sys.argv or "-v" in sys.argv
try:
    sys.argv.remove("--verbose")
    sys.argv.remove("-v")
except ValueError:
    pass
manager_dir = os.path.dirname(__file__)
project_dir = os.path.dirname(manager_dir)

if verbose:
    def print_verbose(*args):
        for arg in args:
            print(arg)
else:   
    print_verbose = lambda *a: None

try:
    print_verbose("creating repos and addons folder")
    os.mkdir(f"{manager_dir}/repos")
    os.mkdir(f"{project_dir}/addons")
    os.mkdir(f"{project_dir}/addons/third_party")
except (FileExistsError):
    print_verbose("repos or addons folder already existed")

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


def delete_addon(addon):
    """
    Deletes an addon inside the addons folder of the project.
    """
    if os.path.islink(addon):
        print_verbose(f"deleting symlink {addon}")
        os.remove(addon)
    elif os.path.isdir(addon):
        print_verbose(f"deleting directory {addon}")
        shutil.rmtree(addon)


def download_addons(modules_file, indent=0):
    """
    Clones or updates the repositories listed in `modules_file`
    and either copies or creates symlinks to the addons of the module.
    """
    file = open(modules_file, "r")
    for dependency in file:
        if dependency.isspace():
            continue
        repo, version = dependency.strip().split(" ")
        if "/.git" in repo:
            # Get the name of a local git repo like `/path/to/repo/.git`.
            name = repo.split("/")[-2]
        else:
            # Get the name of a git url like `https://github.com/user/repo.git`
            name = repo.split("/")[-1].split(".")[-2]
        print("	" * indent + f"[{name}] version {version[:6]} from {repo}")

        if os.path.isdir(f"{manager_dir}/repos/{name}"):
            print_verbose(f"repo already cloned, pulling and checking out {version}")
            run_git_command("pull origin master", f"{manager_dir}/repos/{name}")
        else:
            print_verbose(f"cloning {repo}")
            run_git_command(f"clone {repo}", f"{manager_dir}/repos")
        run_git_command(f"checkout {version}", f"{manager_dir}/repos/{name}")

        for addon in os.listdir(f"{manager_dir}/repos/{name}/addons"):
            print("	" * indent + f"	addon [{addon}]")
            destination = f"{project_dir}/addons/third_party/{addon}"
            delete_addon(destination)
            do_copy = "--links" not in sys.argv and "-l" not in sys.argv
            if not do_copy:
                try:
                    print_verbose(f"creating symlink to {destination}")
                    os.symlink(f"{manager_dir}/repos/{name}/addons/{addon}",
                            destination, True)
                except OSError:
                    print_verbose(f"symlink failed, copying instead")
                    do_copy = True
            if do_copy:
                shutil.copytree(f"{manager_dir}/repos/{name}/addons/{addon}", destination)
                    

        submodule_file = f"{manager_dir}repos/{name}/godotmodules.txt"
        if os.path.isfile(submodule_file):
            download_addons(submodule_file, indent + 1)


def clean_addons(repos=False):
    """
    Deletes downloaded addons, and cloned repositories if `repos` is true.
    """
    for repo in os.listdir(f"{manager_dir}/repos"):
        for addon in os.listdir(f"{manager_dir}/repos/{repo}/addons"):
            delete_addon(f"{project_dir}/addons/third_party/{addon}")
            print(f"deleting {addon}")
        if repos:
            shutil.rmtree(f"{manager_dir}/repos/{repo}")
            print(f"deleting repo {repo}")


def print_repo_status():
    """
    Prints the git status of each cloned repository.
    """
    for repo in os.listdir(f"{manager_dir}/repos"):
        run_git_command("status", f"{manager_dir}/repos/{repo}", True)


def install_addon(name):
    """
    Searches for an addon on Github and installs it.
    """
    query = f"https://api.github.com/search/repositories?q={name} language:GDScript&per_page=1"
    print_verbose(query)
    text = requests.get(query).text
    items = json.loads(text).get("items")
    if len(items) == 0:
        print("no module found")
        return
    result = json.loads(text).get("items")[0]
    print_verbose(result)
    with open(f"{project_dir}/godotmodules.txt", "a") as modulesfile:
        modulesfile.write(f"{result['clone_url']} {result['default_branch']}\n")
    download_addons(f"{project_dir}/godotmodules.txt")


def remove_addon(name):
    modules = ""
    with open(f"{project_dir}/godotmodules.txt", "r") as modulesfile:
        for line in modulesfile.readlines():
            if line == "":
                continue
            print_verbose(line)
            if not name in line.lower():
                modules += line
            else:
                print_verbose(f"removed {line}")
    with open(f"{project_dir}/godotmodules.txt", "w") as modulesfile:
        modulesfile.write(modules)


mode = ""
if len(sys.argv) > 1:
    mode = sys.argv[1]

if mode == "clean":
    print("deleting addons")
    clean_addons()
elif mode == "cleanall":
    print("deleting addons and repos")
    clean_addons(True)
elif mode == "status":
    print("fetching the status of the cloned repos")
    print_repo_status()
elif mode == "update":
    print("downloading modules")
    download_addons(f"{project_dir}/godotmodules.txt")
elif mode == "install":
    if len(sys.argv) < 3:
        print("no module specified")
    else:
        name = sys.argv[2]
        print(f"installing {name}")
        install_addon(name)
elif mode == "remove":
    if len(sys.argv) < 3:
        print("no module specified")
    else:
        name = sys.argv[2]
        print(f"removing {name}")
        remove_addon(name)
else:
    print("usage: package_manager [option]")
    print("update		Download or update modules")
    print("clean		Delete downloaded modules")
    print("cleanall	Delete addons and repos")
    print("status		Show the git status of all cloned repos")
    print("install		Search and install a module from Github")
    print("remove		Uninstalls the specified module")
    print("-v / --verbose	Enable verbose logging")
    print("-l / --link	Use symbolic links to copy addons into the addons folder")
