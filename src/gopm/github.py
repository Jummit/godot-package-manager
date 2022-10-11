"""Search provider using Github's API."""

import requests
import json
from typing import List
from gopm.search_provider import SearchProvider, Result

class GithubResult(Result):
    def __init__(self, content: dict):
        super().__init__(content["full_name"], content["description"], "master", content["clone_url"])
        self.commits_url = content["commits_url"].replace('{/sha}', "")

    @property
    def latest_version(self) -> str:
        return requests.get(self.commits_url).json()[0].get("sha")[:7]

    @latest_version.setter
    def latest_version(self, value) -> None:
        self._latest_version = value


class GithubSearchProvider(SearchProvider):
    def __init__(self):
        pass
    
    def get_matches(self, term: str) -> List[Result]:
        query = f"https://api.github.com/search/repositories?q=\
    {term} language:GDScript&per_page=10"
        text = requests.get(query).text
        items = json.loads(text).get("items")
        return list(map(GithubResult, items))
