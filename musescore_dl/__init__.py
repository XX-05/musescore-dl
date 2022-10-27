import pathlib

import click
import questionary
import jmuse


def _dl_score(score: jmuse.Score, dl_path: str) -> None:
    """
    Prompts the user to decide the score format(s) (i.e. pdf or mp3) and downloads it with console output

    :param score: The Score object to download
    :param dl_path: The filepath to write the score at. A file extension should not be included in the dl_path
                    because it is automatically added depending on the format(s) selected by the user.
    """
    click.echo("Downloading " + click.style(score.title.title(), fg='blue') + " from " + click.style(score.url, fg="blue"))
    formats = questionary.checkbox("Select a format", choices=["mp3", "pdf"]).ask()

    if "pdf" in formats:
        score.download(dl_path + ".pdf")
        click.echo("Finished writing " + click.style(f"'{dl_path}.pdf'", fg='green'))

    if "mp3" in formats:
        score.download_mp3(dl_path + ".mp3")
        click.echo("Finished writing " + click.style(f"'{dl_path}.mp3'", fg='green'))


@click.group()
def cli():
    """
    Bypass MuseScore's dumb paywall to download the scores you deserve
    """
    pass


@cli.command()
@click.argument("query")
def search(query) -> None:
    """
    Search MuseScore for a score

    :param query: The term to search for scores by
    """
    results = jmuse.search_scores(query)
    # filter official scores out of the search results because they cannot currently be downloaded
    choices = [questionary.Choice(f"{r.title} (id: {r.id})", r) for r in results if not r.is_official]
    score = questionary.select("Search Results", choices=choices, qmark="").ask()

    if score is None:
        return

    dl_path = pathlib.Path(
        click.prompt("Write Directory", default="."),
        click.prompt("Name (no suffix)", default=score.title)
    )
    dl_path.parent.mkdir(exist_ok=True, parents=True)
    _dl_score(score, str(dl_path))


@cli.command()
@click.argument("url")
@click.option("--name", default=None, type=click.Path(file_okay=False, dir_okay=False))
@click.option("--dir", "out_dir", default=".", type=click.Path())
def get(url, name, out_dir) -> None:
    """
    Download a score given its url and a write path

    :param url: The url of the score
    :param name: The filename to download the score as
    :param out_dir: The directory to download the score in
    """
    result = jmuse.get_score_from_url(url)

    if name is None:
        name = f"{result.title}"
    if out_dir is not None:
        pathlib.Path(out_dir).mkdir(exist_ok=True, parents=True)

    _dl_score(result, str(pathlib.Path(out_dir, name)))
