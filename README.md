# Godot Package Manager

A python script to download and update git-based packages and their dependencies.

## Usage

Run `gopm.py` in the game directory. See `gopm -h` to show the help:

**Usage: gopm {-u|-i|-r} [-v] <package> ...**

`-u / --update` Update all packages

`-s / --upgrade` Upgrade all packages to the latest version

`-i / --install` Install a package from a git 
URI or search and install a package from Github

`-r / --remove` Uninstall the specified package

`-v / --verbose` Enable verbose logging

`-h / --help` Show this help message

Installed addons will be put in the `addons` folder.

## Creating Packages

An installable package needs to have an `addons` folder with one or multiple folders inside, and optionally a `godotmodules.txt` file with dependencies.
