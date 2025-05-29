import click
from vma.utils import run

@click.command()
@click.option("--tenant", required=True, help="Tenant name")
@click.option("--app", required=False, help="App name")
def docker_logs(tenant, app):
    """Show Docker logs for a tenant/app."""
    if app:
        print(f"Showing logs for {tenant}/{app}")
        run(f"docker logs {tenant}_{app}", _raise=False)
    else:
        print(f"Showing logs for all {tenant} containers")
        print(f"\n--- FRONTEND LOGS ---")
        run(f"docker logs {tenant}_frontend 2>&1 | tail -n 20", _raise=False)
        print(f"\n--- BACKEND LOGS ---")
        run(f"docker logs {tenant}_backend 2>&1 | tail -n 20", _raise=False)
        print(f"\n--- NGINX LOGS ---")
        run(f"docker logs {tenant}_nginx 2>&1 | tail -n 20", _raise=False)