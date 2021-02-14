import os
import subprocess
import shutil
import sys

verbose = "--verbose" in sys.argv or "-v" in sys.argv

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

        if os.path.isdir(f"repos/{name}"):
            print_verbose(f"repo already cloned, pulling and checking out {version}")
            run_git_command("pull origin master", f"repos/{name}", verbose)
        else:
            print_verbose(f"cloning {repo}")
            run_git_command(f"clone {repo}", "repos", verbose)
        run_git_command(f"checkout {version}", f"repos/{name}", verbose)

        for addon in os.listdir(f"repos/{name}/addons"):
            print("	" * indent + f"	addon [{addon}]")
            destination = f"../addons/{addon}"
            delete_addon(destination, verbose)
            try:
                print_verbose(f"creating symlink to {destination}")
                os.symlink(f"{os.getcwd()}/repos/{name}/addons/{addon}",
                        destination, True)
            except OSError:
                print_verbose(f"symlink failed, copying instead")
                shutil.copytree(f"repos/{name}/addons/{addon}", destination)

        submodule_file = f"repos/{name}/godotmodules.txt"
        if os.path.isfile(submodule_file):
            download_addons(submodule_file, verbose, indent + 1)


def clean_addons(verbose, repos=False):
    """
    Deletes downloaded addons, and cloned repositories if `repos` is true.
    """
    for repo in os.listdir("repos"):
        for addon in os.listdir(f"repos/{repo}/addons"):
            delete_addon(f"../addons/{addon}", verbose)
            print(f"deleting {addon}")
        if repos:
            shutil.rmtree(f"repos/{repo}")
            print(f"deleting repo {repo}")

try:
    print_verbose("creating repos and addons folder")
    os.mkdir("repos")
    os.mkdir("../addons")
except (FileExistsError):
    print_verbose("repos or addons folder already existed")


def print_repo_status():
    """
    Prints the git status of each cloned repository.
    """
    for repo in os.listdir("repos"):
        run_git_command("status", f"repos/{repo}", True)

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
    print("update:	download or update modules")
    print("clean:	delete downloaded addons")
    print("cleanall:	delete addons and repos")
    print("-v / --verbose:	enable verbose logging")
else:
    print("downloading modules")
    download_addons("../godotmodules.txt", verbose)
