import pathlib

import click
import questionary
import jmuse


def _dl_score(score: jmuse.Score, dl_path: str):
    click.echo("Downloading " + click.style(f"{score.name.title()} by {score.artist}", fg='blue'))
    formats = questionary.checkbox("Select a format", choices=["mp3", "pdf"]).ask()

    if "pdf" in formats:
        score.download(dl_path + ".pdf")
        click.echo("Finished writing " + click.style(f"'{dl_path}.pdf'", fg='green'))

    if "mp3" in formats:
        score.download_mp3(dl_path + ".mp3")
        click.echo("Finished writing " + click.style(f"'{dl_path}.mp3'", fg='green'))


@click.group()
def cli():
    pass


@cli.command()
@click.argument("query")
def search(query):
    results = jmuse.search_scores(query)
    choices = [questionary.Choice(r.title, r) for r in results]
    score = questionary.select("Search Results", choices=choices).ask()

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
def get(url, name, out_dir):
    result = jmuse.get_score_from_url(url)

    if name is None:
        name = f"{result.name}"
    if out_dir is not None:
        pathlib.Path(out_dir).mkdir(exist_ok=True, parents=True)

    _dl_score(result, str(pathlib.Path(out_dir, name)))


if __name__ == "__main__":
    cli()
