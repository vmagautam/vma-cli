import click
from vma.commands import vma_command

def cli():
    """Entrypoint for the universal deployment CLI."""
    vma_command()

if __name__ == "__main__":
    cli()