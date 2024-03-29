from __future__ import annotations

import io
import json
import re
import typing

import bs4
import reportlab.graphics.shapes
import reportlab.lib.pagesizes
import reportlab.pdfgen.canvas
import requests
import svglib.svglib


_AUTH_HEADERS = None


def _get_js_store_scores(html: str, multiple=True) -> dict | list:
    """
    Returns the information contained in the 'js-store' tag of a MuseScore page

    :param html: The html content of the page containing the 'js-store'
    :return: The information contained in the js-store tag
    """
    soup = bs4.BeautifulSoup(html, "lxml")
    js_store = soup.find("div", attrs={"class": "js-store"})["data-content"]
    store_data = json.loads(js_store)["store"]["page"]["data"]

    return store_data["scores"] if multiple else store_data["score"]


class Score:
    """
    A MuseScore score.
    The Score object provides functionality to download the score itself as well as MuseScore's render of it.
    """

    def __init__(self, json_data: dict) -> None:
        """
        Creates a new Score object populated with the data from a MuseScore search result.

        :param json_data: The MuseScore search result json data
        """
        self.title = json_data["title"].replace("[b]", "").replace("[/b]", "")
        self.desc = json_data["description"]
        self.id = json_data["id"]
        self.user_id = json_data["user"]["id"]
        self.n_pages = json_data["pages_count"]
        self.url = json_data["url"]
        self.is_official = json_data["is_official"]

        # Auth headers are cached
        # as they are not unique to individual scores and are expensive to retrieve.
        global _AUTH_HEADERS
        if _AUTH_HEADERS is None:
            _AUTH_HEADERS = self._get_auth_headers()
        
        self._auth_headers = _AUTH_HEADERS

    def _get_auth_headers(self) -> dict[str]:
        """
        Retrieves the authorization header value required to make requests to MuseScore on behalf of the client

        :return: The request Authorization header value
        """
        musescore_embed_url = f"https://musescore.com/user/{self.user_id}/scores/{self.id}/embed"
        embed_content = requests.get(musescore_embed_url).content
        soup = bs4.BeautifulSoup(embed_content, "lxml")

        # This could break in the future if the script import order is changed or new 40-character strings are
        #  introduced into the script. However, since the auth keys are hardcoded into the script making the api calls,
        #  this seems to be the best solution.
        jmuse_script_url = soup.find_all("script")[-1]["src"]
        jmuse_script = requests.get(jmuse_script_url)
        api_keys = re.findall(r"[a-zA-Z0-9]{40}", jmuse_script.text)[-2:]

        return {"mp3": api_keys[0], "sheet": api_keys[1]}

    def __repr__(self):
        return self.title

    @staticmethod
    def _download_file(url: str, file: typing.IO, chunk_size: int = 8192) -> None:
        """
        Copies a file from a given URL into an IO stream

        :param url: The file url
        :param file: A writable IO stream to copy the content into
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
            f"https://musescore.com/api/jmuse",
            headers={"Authorization": self._auth_headers["sheet"]},
            params={
                "id": self.id,
                "index": page,
                "type": "img",
                "v2": 1
            }
        )

        if res.status_code != 200:
            return None

        return res.json()["info"]["url"]

    def _get_page_svg(self, page: int) -> reportlab.graphics.shapes.Drawing | None:
        """
        Fetches a page of the score from its url and converts it into a reportlab Drawing

        :param page: The page number to fetch
        :return: A reportlab Drawing of the score sheet
        """
        buffer = io.BytesIO()
        page_url = self._get_page_url(page)

        if page_url is None:
            return None

        self._download_file(page_url, buffer)
        buffer.seek(0)
        return svglib.svglib.svg2rlg(buffer)

    def download(self, file: str | bytes | io.IOBase):
        """
        Downloads the full score as a pdf

        :param file: A filepath or IO stream to write the score in
        """
        page_size = reportlab.lib.pagesizes.A4
        canvas = reportlab.pdfgen.canvas.Canvas(file, pagesize=page_size)
        canvas.setTitle(self.title)

        for i in range(self.n_pages):
            page = self._get_page_svg(i)
            # For some reason, the page url wasn't returned by the jmuse api call
            if page is None:
                continue
            # fix svg sizing issues by resizing the score to fit the page
            page.scale(page_size[0] / page.width, page_size[1] / page.height)
            page.drawOn(canvas, 0, 0)
            canvas.showPage()

        canvas.save()

    def _get_mp3_url(self) -> str:
        """
        Returns the url for the rendered score audio

        :return: The audio file url
        """
        res = requests.get(
            f"https://musescore.com/api/jmuse",
            headers={"Authorization": self._auth_headers["mp3"]},
            params={
                "id": self.id,
                "index": 0,
                "type": "mp3",
                "v2": 1
            }
        )

        if res.status_code != 200:  # Sometimes MuseScore does not have a render available for a given score
            raise FileNotFoundError(res.reason)

        return res.json()["info"]["url"]

    def download_mp3(self, file: str | bytes | io.IOBase = None) -> None:
        """
        Downloads a synthesized version of the score as an mp3 to a given location

        :param file: The filepath or IO stream to write the mp3 file to
        """
        if file is None:
            file = open(f"{self.title}.mp3", "wb")
        elif not isinstance(file, io.IOBase):
            file = open(file, "wb")

        self._download_file(self._get_mp3_url(), file)


def search_scores(q: str) -> list[Score]:
    """
    Searches MuseScore for scores matching the query string

    :param q: The search query string
    :return: A list of result Score(s)
    """
    res = requests.get("https://musescore.com/sheetmusic", params={"text": q})
    scores_json = _get_js_store_scores(res.text)

    return [Score(result) for result in scores_json]


def get_score_from_url(url: str):
    """
    Creates a new Score object from its url populated with its MuseScore listing information

    :param url: The url of the score
    :return: A new Score object containing its MuseScore information
    """
    res = requests.get(url)
    score_data = _get_js_store_scores(res.text, multiple=False)

    return Score(score_data)
