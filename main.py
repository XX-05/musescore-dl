from __future__ import annotations

import os
import random
import string
import typing

"""
{
"publisher": null,
"is_official": false,
"body": "Basically just copied it. I tried to make it playable for like an intermediate pianist. feel free to change rhythms. I also tried to make it less boring and add a swing in left hand if too hard change to regular quarter note. This is my first \"arrangement\" but I really just copied it. Hope someone enjoys it.",
"tags": [],
"is_downloadable": 1,
"is_blocked": false,
"license": "all-rights-reserved",
"instrumentation_id": 0,
"is_original": false,
"measures": 122,
"keysig": "D major, B minor",
"license_id": 9,
"license_version": "4.0",
"song_name": "the suburbs",
"artist_name": "Arcade Fire",
"complexity": 2,
"_links": {
    "self": {
    "href": "https://musescore.com/user/20720841/scores/4000056"
    }
}
}
"""

import json
import sys

import urllib.parse
import bs4

import requests


class Score:
    def __init__(self, name: str, artist: str, full_title: str, description: str, url: str) -> None:
        self._name = name
        self._artist = artist
        self._title = full_title
        self._desc = description
        self._url = url
        self._id = url.split("/")[-1]

    def __repr__(self):
        return self._title

    def get_sheet_svgs(self):
        res = requests.get(self._url)
        soup = bs4.BeautifulSoup(res.text, "lxml")
        return soup.findAll("div", attrs={"class": "vAVs3"})

    def _get_mp3_url(self, auth) -> str:
        res = requests.get(
            f"https://musescore.com/api/jmuse?id={self._id}&index=0&type=mp3&v2=1",
            headers={"Authorization": auth}
        )

        if res.status_code != 200:
            raise FileNotFoundError(res.reason)

        return res.json()["info"]["url"]

    def download_mp3(self, auth: str, path: typing.Union[str, bytes, os.PathLike]) -> None:
        """
        Downloads a synthesized version of the score as an mp3 to a given location

        :param path: The path to write the mp3 file to
        """
        mp3_url = self._get_mp3_url(auth)
        mp3 = requests.get(mp3_url)

        with open(path, "wb") as f:
            f.write(mp3.content)

    @staticmethod
    def from_json(score: dict) -> Score:
        song_name = score["song_name"]
        artist_name = score["artist_name"]
        title = score["title"].replace("[b]", "").replace("[/b]", "")
        description = score["description"]
        score_url = score["_links"]["self"]["href"]

        return Score(song_name, artist_name, title, description, score_url)


def search_scores(q: str) -> list[Score]:
    """
    Searches MuseScore for scores matching the query string

    :param q: The search query string
    :returns: A list of result Score(s)
    """
    res = requests.get(f"https://musescore.com/sheetmusic?text={urllib.parse.quote_plus(q)}")

    soup = bs4.BeautifulSoup(res.text, "lxml")
    results = soup.find("div", attrs={"class": "js-store"})["data-content"]
    scores_json = json.loads(results)["store"]["page"]["data"]["scores"]

    return [Score.from_json(result) for result in scores_json]


if __name__ == "__main__":
    results = search_scores("the suburbs")

    score = results[0]
    print(score.get_sheet_svgs())
    uuid = "".join(random.choice(string.ascii_lowercase + string.digits) for i in range(40))
    score.download_mp3("", "./the-suburbs-piano.mp3")
