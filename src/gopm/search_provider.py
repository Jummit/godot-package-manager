from typing import List

class Result:
    def __init__(self, name: str, description: str, latest_version: str, url: str):
        self.name = name
        self.description = description
        self.url = url
        self.latest_version = latest_version

    @property
    def latest_version(self) -> str:
        return self._latest_version

    @latest_version.setter
    def latest_version(self, value) -> None:
        self._latest_version = value

class SearchProvider:
    def __init__(self):
        raise NotImplementedError

    def get_matches(self, term: str) -> List[Result]:
        raise NotImplementedError

