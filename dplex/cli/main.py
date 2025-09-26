"""Main CLI entry point"""

import click


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Dataplex CLI tool"""
    pass


@main.command()
def init():
    """Initialize new Dataplex project"""
    click.echo("Initializing Dataplex project...")


if __name__ == "__main__":
    main()
