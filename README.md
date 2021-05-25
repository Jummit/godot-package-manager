# Godot Package Manager

A python script to download and update addons with dependencies.

## Usage

To add the package manager to your project, either clone or add this repo into your game folder as a submodule.

To install addons, create a `godotmodules.txt` file in the root folder of your game. Each line is one module in this format:

`git-path commit-hash`

So for example:

```
git@github.com:User/module-name.git a8a52345a7abde2
git@github.com:User/module-name.git master
```

To download or update the addons, run `python2.9 package_manager.py`. Run `python2.9 package_manager.py help` for help.

Installed addons will be put in the `addons/third_party` folder.

## Creating Packages

An installable addon needs to have an `addons` folder with one or multiple folders inside, and optionally a `godotmodules.txt` file with dependencies.
