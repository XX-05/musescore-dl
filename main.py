from __future__ import annotations

import io
import json
import os
import re
import tempfile
import urllib.parse

import bs4
import reportlab.graphics.shapes
import requests

from svglib.svglib import svg2rlg
from reportlab.pdfgen import canvas


class MuseScoreAuthenticationError(Exception):
    pass


class Score:
    def __init__(self, json_data: dict) -> None:
        """
        Creates a new Score object populated with the data from a MuseScore search result.

        :param json_data: The MuseScore search result json data
        """
        self.name = json_data["song_name"]
        self.artist = json_data["artist_name"]
        self.title = json_data["title"].replace("[b]", "").replace("[/b]", "")
        self.desc = json_data["description"]
        self.id = json_data["id"]
        self.user_id = json_data["user"]["id"]
        self.n_pages = json_data["pages_count"]

        self._auth_headers = self._get_auth_headers()

    def _get_auth_headers(self) -> dict[str]:
        """
        Retrieves the authorization header value required to make requests to MuseScore on behalf of the client

        :return: The request Authorization header value
        """
        musescore_embed_url = f"https://musescore.com/user/{self.user_id}/scores/{self.id}/embed"
        embed_content = requests.get(musescore_embed_url).content
        soup = bs4.BeautifulSoup(embed_content, "lxml")

        # This might become unreliable in the future because it would break if the script import order is changed
        # or new 40-character strings are introduced into the script. Sadly, it's all I could come up with because
        # the auth keys are hardcoded into the scripts making the api calls.
        jmuse_script_url = soup.find_all("script")[-1]["src"]
        api_keys = re.findall(r"[a-zA-Z0-9]{40}", requests.get(jmuse_script_url).text)[-2:]

        return {
            "mp3": api_keys[0],
            "sheet": api_keys[1]
        }

    def __repr__(self):
        return self.title

    @staticmethod
    def _download_file(url: str, file: io.BytesIO | tempfile.TemporaryFile, chunk_size=8192) -> None:
        """
        Downloads an online file to a given path

        :param url: The file url
        :param file: A writable file object to put the url content into
        """
        with requests.get(url, stream=True) as content:
            for chunk in content.iter_content(chunk_size):
                file.write(chunk)

    def _get_page_url(self, page: int) -> str | None:
        """
        Returns the url for a page of the score

        :param page: The page of the score to get
        :return: The url of the score page
        """
        res = requests.get(
            f"https://musescore.com/api/jmuse?id={self.id}&index={page}&type=img&v2=1",
            headers={"Authorization": self._auth_headers["sheet"]}
        )

        if res.status_code != 200:
            return None

        return res.json()["info"]["url"]

    def _get_page_svg(self, page: int) -> reportlab.graphics.shapes.Drawing:
        """
        Fetches a page of the score from its url and converts it into a reportlab Drawing

        :param page: The page number to fetch
        :return: A reportlab Drawing of the score sheet
        """
        with tempfile.NamedTemporaryFile(delete=True) as f:
            self._download_file(self._get_page_url(page), f)
            f.seek(0)

            return svg2rlg(f.name)

    def download(self, path: str | bytes | os.PathLike = None) -> None:
        """
        Downloads the full score as a pdf to a given location

        :param path: The filepath to write the score into
        """
        path = f"{self.name}.pdf" if path is None else path

        c = canvas.Canvas(path)
        for i in range(self.n_pages):
            page = self._get_page_svg(i)
            page.drawOn(c, 0, 0)
            c.showPage()

        c.save()

    def _get_mp3_url(self) -> str:
        """
        Returns the url for the rendered score audio

        :return: The audio file url
        """
        res = requests.get(
            f"https://musescore.com/api/jmuse?id={self.id}&index=0&type=mp3&v2=1",
            headers={"Authorization": self._auth_headers["mp3"]}
        )

        if res.status_code != 200:
            raise FileNotFoundError(res.reason)

        return res.json()["info"]["url"]

    def download_mp3(self, path: str | bytes | os.PathLike = None) -> None:
        """
        Downloads a synthesized version of the score as an mp3 to a given location

        :param path: The path to write the mp3 file to
        :return: The size in bytes of the downloaded mp3 file
        """
        if path is None:
            path = f"{self.name}.mp3"

        with open(path, "wb") as f:
            self._download_file(self._get_mp3_url(), f)


def search_scores(q: str) -> list[Score]:
    """
    Searches MuseScore for scores matching the query string

    :param q: The search query string
    :return: A list of result Score(s)
    """
    res = requests.get(f"https://musescore.com/sheetmusic?text={urllib.parse.quote_plus(q)}")

    soup = bs4.BeautifulSoup(res.text, "lxml")
    results = soup.find("div", attrs={"class": "js-store"})["data-content"]
    scores_json = json.loads(results)["store"]["page"]["data"]["scores"]

    return [Score(result) for result in scores_json]


if __name__ == "__main__":
    score = search_scores("four out of five")[0]
    print(f"downloading {score.title}")
    score.download()
