"""Main CLI entry point"""

import click


@click.group()
@click.version_option(version="0.1.0")
def main():
    """dplex CLI tool"""
    pass


@main.command()
def init():
    """Initialize new dplex project"""
    click.echo("Initializing dplex project...")


if __name__ == "__main__":
    main()
