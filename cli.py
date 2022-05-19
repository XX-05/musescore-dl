import pathlib

import click
import musescoredl


@click.group()
def cli():
    pass


@cli.command()
@click.argument("query")
def search(query):
    print(musescoredl.search_scores(query))


@cli.command()
@click.argument("url")
@click.option("--name", default=None, type=click.Path(file_okay=False, dir_okay=False))
@click.option("--dir", "out_dir", default="scores", type=click.Path())
def score(url, name, out_dir):
    result = musescoredl.Score.from_url(url)
    click.echo("Downloading " + click.style(f"{result.name.title()} by {result.artist}", fg='blue'))

    if name is None:
        name = f"{result.name}.pdf"
    if out_dir is not None:
        pathlib.Path(out_dir).mkdir(exist_ok=True, parents=True)

    dl_path = result.download(str(pathlib.Path(out_dir, name)))
    click.echo("Finished writing " + click.style(f"'{dl_path}'", fg='green'))


if __name__ == "__main__":
    cli()
