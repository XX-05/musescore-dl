from __future__ import annotations

import json
import os
import re
import typing
import urllib.parse

import bs4
import requests


class Score:
    def __init__(self, json_data: dict) -> None:
        """
        Creates a new Score object populated with the data from a MuseScore search result.

        :param json_data: The MuseScore search result json data
        """
        self._name = json_data["song_name"]
        self._artist = json_data["artist_name"]
        self._title = json_data["title"].replace("[b]", "").replace("[/b]", "")
        self._desc = json_data["description"]
        self._id = json_data["id"]
        self._n_pages = json_data["pages_count"]

    def __repr__(self):
        return self._title

    @staticmethod
    def _get_auth_header(mp3=False):
        """
        Retrieves the authorization header value required to make requests to MuseScore on behalf of the client

        :return: The 'Authorization' request header value
        """
        url = "https://musescore.com/static/public/build/musescore_es6/jmuse_embed.153b5b4b18e48ffaf666b76cd33f6de4.js"
        res = requests.get(url).text
        return re.findall(r"[a-zA-Z0-9]{40}", res)[-(1 + mp3)]  # Just awful

    def _get_sheet_url(self, auth: str, page: int):
        res = requests.get(
            f"https://musescore.com/api/jmuse?id={self._id}&index={page}&type=img&v2=1",
            headers={"Authorization": auth}
        )

        return res.json()

    def get_sheet_svgs(self):
        auth = self._get_auth_header()
        sheet_urls = [self._get_sheet_url(auth, i) for i in range(self._n_pages)]

        return sheet_urls

    def _get_mp3_url(self, auth: str) -> str:
        res = requests.get(
            f"https://musescore.com/api/jmuse?id={self._id}&index=0&type=mp3&v2=1",
            headers={"Authorization": auth}
        )

        if res.status_code != 200:
            raise FileNotFoundError(res.reason)

        return res.json()["info"]["url"]

    def download_mp3(self, path: typing.Union[str, bytes, os.PathLike]) -> None:
        """
        Downloads a synthesized version of the score as an mp3 to a given location

        :param path: The path to write the mp3 file to
        """
        mp3_url = self._get_mp3_url(self._get_auth_header(mp3=True))
        mp3 = requests.get(mp3_url)

        with open(path, "wb") as f:
            f.write(mp3.content)


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

    return [Score(result) for result in scores_json]


if __name__ == "__main__":
    results = search_scores("the suburbs arcade fire")

    score = results[0]
    sheets = score.get_sheet_svgs()
    print(sheets, len(sheets))
    # score.download_mp3("./45.mp3")
