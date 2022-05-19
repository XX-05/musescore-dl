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
@click.option("--path", default=None, type=click.Path(file_okay=False))
def score(url, path=None):
    print(url, path)


if __name__ == "__main__":
    cli()
