# Godot Package Manager

A python script to download and update packages with dependencies.

## Usage

To add the package manager to your project, either clone or add this repo into your game folder as a submodule.

To install modules, create a `godotmodules.txt` file in the root folder of your game. Each line is one module in this format:

`git-path commit-hash`

So for example:

```
git@github.com:User/module-name.git a8a52345a7abde2`
git@github.com:User/module-name.git master`
```

To download or update the modules, run `python package_manager.py` inside the package manager directory. Run `python package_manager.py help` for help.

## Creating Modules

A module needs to have an `addons` folder with one or multiple addons inside, and optionally a `godotmodules.txt` file with dependencies.
