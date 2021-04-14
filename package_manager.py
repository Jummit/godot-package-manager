import os
import subprocess
import shutil
import sys

verbose = "--verbose" in sys.argv or "-v" in sys.argv
manager_dir = os.path.dirname(__file__)
project_dir = os.path.dirname(manager_dir)

if verbose:
    def print_verbose(*args):
        for arg in args:
            print(arg)
else:   
    print_verbose = lambda *a: None

def run_git_command(command, working_directory, verbose):
    """
    Runs a git command inside `working_directory`. If `verbose` is false,
    passes the --quiet option to the command.
    """
    args = command.split(" ")
    args.insert(0, "git")
    if not verbose:
        args.append("-q")
    subprocess.run(args, cwd=working_directory)


def delete_addon(addon, verbose):
    """
    Deletes an addon inside the addons folder of the project.
    """
    if os.path.islink(addon):
        print_verbose(f"deleting symlink {addon}")
        os.remove(addon)
    elif os.path.isdir(addon):
        print_verbose(f"deleting directory {addon}")
        shutil.rmtree(addon)


def download_addons(modules_file, verbose, indent=0):
    """
    Clones or updates the github repositories listed in `modules_file`
    and either copies or creates symlinks to the addons of the module.
    """
    file = open(modules_file, "r")
    for dependency in file:
        repo, version = dependency.strip().split(" ")
        name = repo.split("/")[-1].split(".")[-2]
        print("	" * indent + f"[{name}] version {version[:6]} from {repo}")

        if os.path.isdir(f"{manager_dir}/repos/{name}"):
            print_verbose(f"repo already cloned, pulling and checking out {version}")
            run_git_command("pull origin master", f"{manager_dir}/repos/{name}", verbose)
        else:
            print_verbose(f"cloning {repo}")
            run_git_command(f"clone {repo}", f"{manager_dir}/repos", verbose)
        run_git_command(f"checkout {version}", f"{manager_dir}/repos/{name}", verbose)

        for addon in os.listdir(f"{manager_dir}/repos/{name}/addons"):
            print("	" * indent + f"	addon [{addon}]")
            destination = f"{project_dir}/addons/third_party/{addon}"
            delete_addon(destination, verbose)
            try:
                print_verbose(f"creating symlink to {destination}")
                os.symlink(f"{manager_dir}/repos/{name}/addons/{addon}",
                        destination, True)
            except OSError:
                print_verbose(f"symlink failed, copying instead")
                shutil.copytree(f"{manager_dir}/repos/{name}/addons/{addon}", destination)

        submodule_file = f"{manager_dir}repos/{name}/godotmodules.txt"
        if os.path.isfile(submodule_file):
            download_addons(submodule_file, verbose, indent + 1)


def clean_addons(verbose, repos=False):
    """
    Deletes downloaded addons, and cloned repositories if `repos` is true.
    """
    for repo in os.listdir(f"{manager_dir}/repos"):
        for addon in os.listdir(f"{manager_dir}/repos/{repo}/addons"):
            delete_addon(f"{project_dir}/addons/third_party/{addon}", verbose)
            print(f"deleting {addon}")
        if repos:
            shutil.rmtree(f"{manager_dir}/repos/{repo}")
            print(f"deleting repo {repo}")

try:
    print_verbose("creating repos and addons folder")
    os.mkdir(f"{manager_dir}/repos")
    os.mkdir(f"{project_dir}/addons")
    os.mkdir(f"{project_dir}/addons/third_party")
except (FileExistsError):
    print_verbose("repos or addons folder already existed")


def print_repo_status():
    """
    Prints the git status of each cloned repository.
    """
    for repo in os.listdir("repos"):
        run_git_command("status", f"{project_dir}repos/{repo}", True)

mode = ""
if len(sys.argv) > 1:
    mode = sys.argv[1]

if mode == "clean":
    print("deleting addons")
    clean_addons(verbose)
elif mode == "cleanall":
    print("deleting addons and repos")
    clean_addons(verbose, True)
elif mode == "status":
    print("fetches the status of the cloned repos")
    print_repo_status()
elif mode == "help":
    print("package_manager [option] [[-v] [--verbose]]")
    print("update\n	Download or update modules.")
    print("clean\n	Delete downloaded addons.")
    print("cleanall\n	Delete addons and repos.")
    print("status\n	Show the git status of all cloned repos.")
    print("-v / --verbose\n	Enable verbose logging.")
else:
    print("downloading modules")
    download_addons(f"{project_dir}/godotmodules.txt", verbose)
