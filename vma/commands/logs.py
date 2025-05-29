import click
from vma.utils import run

@click.command()
@click.option("--tenant", required=True, help="Tenant name")
@click.option("--app", required=False, help="App name")
def logs(tenant, app):
    """Show logs for a tenant/app."""
    if app:
        print(f"Showing logs for {tenant}/{app}")
        run(f"docker logs {tenant}_{app}", _raise=False)
    else:
        print(f"Showing logs for all {tenant} containers")
        run(f"docker logs {tenant}_frontend 2>&1 | tail -n 20", _raise=False)
        run(f"docker logs {tenant}_backend 2>&1 | tail -n 20", _raise=False)
        run(f"docker logs {tenant}_nginx 2>&1 | tail -n 20", _raise=False)

# Register in __init__.py
# Add this line to vma/commands/__init__.py:
# from vma.commands.logs import logs
# vma_command.add_command(logs)
