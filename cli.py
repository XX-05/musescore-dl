import pathlib

import click
import questionary
import musescoredl


def _dl_score(score: musescoredl.Score, dl_path: str, dl_type: str):
    click.echo("Downloading " + click.style(f"{score.name.title()} by {score.artist}", fg='blue'))

    match dl_type:
        case "pdf":
            dl_path = dl_path + ".pdf"
            score.download(dl_path)
        case "mp3":
            dl_path = dl_path + ".mp3"
            score.download_mp3(dl_path)

    click.echo("Finished writing " + click.style(f"'{dl_path}'", fg='green'))


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if not ctx.invoked_subcommand:
        return


@cli.command()
@click.argument("query")
def search(query):
    results = musescoredl.search_scores(query)
    choices = [questionary.Choice(r.title, r) for r in results]
    score = questionary.select("Search Results", choices=choices).ask()

    dl_path = pathlib.Path(
        click.prompt("Write Directory", default="."),
        click.prompt("Name", default=f"{score.title}.pdf").split(".")[0]
    )
    dl_path.parent.mkdir(exist_ok=True, parents=True)

    formats = questionary.checkbox("Select a format", choices=["mp3", "pdf"]).ask()
    for method in formats:
        _dl_score(score, str(dl_path), method)


@cli.command()
@click.argument("url")
@click.option("--name", default=None, type=click.Path(file_okay=False, dir_okay=False))
@click.option("--dir", "out_dir", default=".", type=click.Path())
def get(url, name, out_dir):
    result = musescoredl.Score.from_url(url)
    if name is None:
        name = f"{result.name}.pdf"
    if out_dir is not None:
        pathlib.Path(out_dir).mkdir(exist_ok=True, parents=True)

    _dl_score(result, str(pathlib.Path(out_dir, name)))


if __name__ == "__main__":
    cli()
