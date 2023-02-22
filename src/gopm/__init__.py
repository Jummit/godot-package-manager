"""Godot Package Manager.

This module can be used as a standalone command-line tool, or accessed with the
Python API.

## Examples

Install an addon:

```python
from gopm import Project
import tempfile

tmp = Path(tempfile.gettempdir()) / "godot_packages"
# Project at current working directory.
project = Project(Path())
(addons, dependencies) = project.download_addons(package, tmp)
print("Installed addons: ", addons)
print("Dependencies: ", dependencies)
```

Update addons:

```python
from gopm import Project
import tempfile

tmp = Path(tempfile.gettempdir()) / "godot_packages"
project = Project(Path())
for dep in project.get_installed():
    project.download_addons(dep, tmp)
```

Get a list of addons:

```python
from gopm import Project

installed = Project("../tetris").get_installed()
print("\n".join(map(lambda p: p.name, installed))
```
"""

from gopm.project import Project
from gopm.project import Package