"""Classes for searching package databases."""

from typing import List

class Result:
    """A single result from a search."""

    def __init__(self, name: str, description: str, latest_version: str,
            url: str):
        self.name = name
        "The name of the repo."
        self.description = description
        self.url = url
        "The Git URI to clone the repo."
        self.latest_version = latest_version
        "The commit hash of the latest commit."

    @property
    def latest_version(self) -> str:
        return self._latest_version

    @latest_version.setter
    def latest_version(self, value) -> None:
        self._latest_version = value

class SearchProvider:
    """A singleton which allows searching a forge for Godot addons."""

    def __init__(self):
        raise NotImplementedError

    def get_matches(self, term: str) -> List[Result]:
        """Make a web request to retrieve a list of addons matching a
        search query.
        """
        raise NotImplementedError

