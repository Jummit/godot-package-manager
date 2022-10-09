# Godot Package Manager

A python script to download and update git-based packages and their dependencies.


## Installation

```bash
git clone git@github.com:Jummit/godot-package-manager.git
pip install godot-package-manager
```

## Usage

Run `gopm.py` in the game directory. Use `gopm -h` to show the usage:

**Usage: gopm [COMMAND] [-v] <package> ...**

`u / update` Update all packages

`s / upgrade` Upgrade all packages to the latest version

`i / install` Install a package from a git 
URI or search and install a package from Github

`r / remove` Uninstall the specified package

`-v / --verbose` Enable verbose logging

`-h / --help` Show this help message

Installed addons will be put in the `addons` folder.

Note that you still need to enable some plugins in the project settings.

## Creating Packages

An installable package needs to have an `addons` folder with one or multiple folders inside, and optionally a `godotmodules.txt` file with dependencies.
