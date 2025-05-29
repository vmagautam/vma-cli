"""
Universal Multi-Tenant Deployment CLI
- Uses plugin system in vma/core/plugins.py
- Supports deploy/start/stop/logs/add-tenant/remove-tenant
- Plugins: nodejs, python, react, docker, etc.
"""
import click
import os
import shutil
from pathlib import Path
import git
import random

from vma.core.plugins import get_plugin_for_path, list_plugins
from vma.commands.github import list_github_repos
from vma.utils import (
    generate_tenant_config,
    generate_base_compose_file,
    add_frontend_to_compose_file,
    create_infrastructure,
    clone_project_repo,
    setup_and_start_backend,
    setup_and_start_frontend,
    wait_for_service,
    add_tenant_to_hosts,
    write_env_file,
    generate_nginx_config_advanced,
    run,
    read_yaml,
    write_yaml,
    random_string
)

@click.group()
def vma_command():
    """VMA Multi-Tenant Deployment CLI"""
    pass

@vma_command.command()
@click.argument("repo_url")
@click.option("--tenant", required=True, help="Tenant name")
@click.option("--branch", required=True, help="Git branch to clone")
def deploy(repo_url, tenant, branch):
    """Deploy an app from a git repository."""
    from vma.utils import log
    tenant_dir = Path("tenants") / tenant
    tenant_dir.mkdir(parents=True, exist_ok=True)
    app_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    app_path = tenant_dir / app_name
    if app_path.exists():
        log(f"App {app_name} already exists for tenant {tenant}", level=1)
        return
    log(f"Cloning {repo_url} (branch {branch}) to {app_path}")
    git.Repo.clone_from(repo_url, str(app_path), branch=branch)
    plugin = get_plugin_for_path(str(app_path))
    if not plugin:
        log("No suitable plugin found for this app type.", level=1)
        return
    log(f"Detected app type: {plugin.__name__}")
    plugin.install(str(app_path), {})
    plugin.build(str(app_path), {})
    plugin.start(str(app_path), {})
    log(f"App {app_name} deployed for tenant {tenant}")

@vma_command.command()
@click.option("--tenant", required=True, help="Tenant name")
def start(tenant):
    """Start all apps for a tenant."""
    from pathlib import Path
    from vma.utils import log
    tenant_dir = Path("tenants") / tenant
    if not tenant_dir.exists():
        log(f"Tenant {tenant} does not exist.", level=1)
        return
    for app_path in tenant_dir.iterdir():
        plugin = get_plugin_for_path(str(app_path))
        if plugin:
            log(f"Starting {app_path.name} with {plugin.__name__}")
            plugin.start(str(app_path), {})
        else:
            log(f"No plugin for {app_path.name}", level=1)

@vma_command.command()
@click.option("--tenant", required=True, help="Tenant name")
def stop(tenant):
    """Stop all apps for a tenant."""
    from pathlib import Path
    from vma.utils import log
    tenant_dir = Path("tenants") / tenant
    if not tenant_dir.exists():
        log(f"Tenant {tenant} does not exist.", level=1)
        return
    for app_path in tenant_dir.iterdir():
        plugin = get_plugin_for_path(str(app_path))
        if plugin:
            log(f"Stopping {app_path.name} with {plugin.__name__}")
            plugin.stop(str(app_path), {})
        else:
            log(f"No plugin for {app_path.name}", level=1)

@vma_command.command()
@click.option("--tenant", required=True, help="Tenant name")
@click.option("--app", required=False, help="App name")
def logs(tenant, app):
    """Show logs for a tenant/app."""
    from pathlib import Path
    
    tenant_dir = Path("tenants") / tenant
    if not tenant_dir.exists():
        print(f"Tenant {tenant} does not exist.")
        return
        
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

@vma_command.command()
def list_plugins_cmd():
    """List available plugins."""
    for name in list_plugins():
        click.echo(name)
        
# Register the GitHub repos command
vma_command.add_command(list_github_repos)

@vma_command.command()
@click.argument("tenant")
def add_tenant(tenant):
    from pathlib import Path
    from vma.utils import log
    tenant_dir = Path("tenants") / tenant
    if tenant_dir.exists():
        log(f"Tenant {tenant} already exists.", level=1)
        return
    (tenant_dir / "apps").mkdir(parents=True)
    (tenant_dir / "config").mkdir(parents=True)
    log(f"Tenant {tenant} created.")

@vma_command.command()
@click.argument("tenant")
def remove_tenant(tenant):
    from pathlib import Path
    import shutil
    from vma.utils import log
    tenant_dir = Path("tenants") / tenant
    if not tenant_dir.exists():
        log(f"Tenant {tenant} does not exist.", level=1)
        return
    shutil.rmtree(tenant_dir)
    log(f"Tenant {tenant} removed.")

@vma_command.command()
@click.option("--tenant", required=True, help="Tenant name")
@click.option("--backend-repo-url", required=True, help="Git URL of the backend repository")
@click.option("--backend-branch", required=True, help="Git branch of the backend repository")
def deploy_backend(tenant, backend_repo_url, backend_branch):
    """
    Deploy the backend application for a tenant.
    Generates config, creates infrastructure (DB, Redis), clones backend repo,
    generates compose file, writes backend .env, starts infrastructure and backend,
    adds to /etc/hosts, and runs backend health checks.
    """
    print(f"Deploying backend for tenant {tenant}...")

    # Ensure tenant directory exists
    tenant_dir = Path(f"tenants/{tenant}")
    tenant_dir.mkdir(parents=True, exist_ok=True)
    print(f"Ensured tenant directory exists: {tenant_dir}")

    # Generate tenant config (will reuse existing if tenant dir exists)
    config = generate_tenant_config(tenant)
    print(f"Generated tenant config: {config}")

    # Clone the backend repo into a 'backend' subfolder
    backend_project_path = clone_project_repo(backend_repo_url, backend_branch, Path(f"tenants/{tenant}/backend"))
    print(f"Cloned backend repo to: {backend_project_path}")

    # Generate base compose file including infra and backend
    compose_path = generate_base_compose_file(tenant, config, backend_project_path)
    print(f"Generated base compose file at: {compose_path}")

    # 6. Write backend .env (using write_env_file directly)
    backend_env = {
        "PORT": "5004", # Fixed based on application logs
        # SMTP related keys omitted as they cannot be auto-generated/handled securely
        "EMAIL": f"no-reply@{tenant}.vsync", # Use tenant-specific email format
        # PASSWORD and SERVICE omitted
        "SESSION_SECRET": random_string(32), # Auto-generated
        "SESSION_COOKIE_NAME": "vmaTechLabs", # Fixed value from user
        "SESSION_MAX_AGE": "3600000", # Fixed value from user
        "REDIS_URL": f"redis://:{config['redis_pass']}@{tenant}_redis:6379", # Use tenant-specific Redis URL
        "DB_PORT": "5432", # Fixed value from user
        "DB_POOL_MIN": "0", # Fixed value from user
        "DB_POOL_MAX": "100", # Fixed value from user
        "DB_USERNAME": config["db_user"], # Generated tenant user
        "DB_SERVER": f"{tenant}_db", # Use tenant-specific DB container name
        "DB_PASSWORD": config["db_pass"], # Generated tenant password
        "DB_DATABASE_MASTER": config["db_master_name"], # Generated tenant master database name
        "DB_DATABASE_TRANSACTIONAL": config["db_transactional_name"], # Generated tenant transactional database name
        "CONFIRM_DELETION": "true", # Fixed value from user
        "NODE_ENV": "development", # Add NODE_ENV
        "NODE_ENV_DEV": "development", # Fixed value from user
        "NODE_ENV_DEV2": "developmentDB2",
        "NODE_ENV_TRIGGER": "trigger"
    }
    write_env_file(str(backend_project_path / ".env"), backend_env)
    print(f"Written backend .env to {backend_project_path / '.env'}")

    # Create infrastructure (DB, Redis) and start backend
    # Use a single compose up command targeting the services
    print(f"Stopping infrastructure and backend containers for tenant {tenant}...")
    # Use a shorter timeout for stopping
    run(f"docker-compose -f {compose_path.name} stop -t 5 {tenant}_db {tenant}_redis {tenant}_backend", cwd=str(compose_path.parent), _raise=False)
    print(f"Starting infrastructure containers for tenant {tenant}...")
    run(f"docker-compose -f {compose_path.name} up -d {tenant}_db {tenant}_redis", cwd=str(compose_path.parent))
    
    # Create the transactional database
    print(f"Creating transactional database {config['db_transactional_name']}...")
    run(f"docker exec {tenant}_db psql -U {config['db_user']} -d {config['db_master_name']} -c \"CREATE DATABASE {config['db_transactional_name']} OWNER {config['db_user']};\"", _raise=False)
    
    # Start the backend container
    print(f"Starting backend container for tenant {tenant}...")
    run(f"docker-compose -f {compose_path.name} up -d {tenant}_backend", cwd=str(compose_path.parent))

    # Add to /etc/hosts
    add_tenant_to_hosts(tenant, config=config)

    # Run backend health checks
    # Use the exposed host port for health check for now, before Nginx is up
    # Need to retrieve the actual exposed port from docker-compose config
    # For simplicity for now, let's assume a known pattern or ask user to check docker ps
    # Or, we can wait for the Nginx container to be up later in deploy-frontend
    # Let's stick to the http://{tenant}.vsync/api/health check, but note it requires Nginx
    backend_url = f"http://{tenant}.vsync/api/health"
    print("Running backend health checks...")
    wait_for_service(backend_url)
    print("Backend health checks completed.")

    print(f"Backend deployment for tenant {tenant} completed.")

@vma_command.command()
@click.option("--tenant", required=True, help="Tenant name")
@click.option("--frontend-repo-url", required=True, help="Git URL of the frontend repository")
@click.option("--frontend-branch", required=True, help="Git branch of the frontend repository")
def deploy_frontend(tenant, frontend_repo_url, frontend_branch):
    """
    Deploy the frontend application for a tenant.
    Clones frontend repo, updates compose file, writes frontend .env,
    starts frontend container, generates Nginx config, and runs frontend health checks.
    Assumes infrastructure and backend are already deployed via deploy-backend.
    """
    print(f"Deploying frontend for tenant {tenant}...")

    # Ensure tenant directory exists and compose file exists
    tenant_dir = Path(f"tenants/{tenant}")
    if not tenant_dir.exists():
        print(f"Tenant directory {tenant_dir} does not exist. Please run deploy-backend first.")
        return

    compose_path = tenant_dir / "docker-compose.yml"
    if not compose_path.exists():
        print(f"docker-compose.yml not found at {compose_path}. Please run deploy-backend first.")
        return

    # Generate tenant config (to get ports, etc.)
    config = generate_tenant_config(tenant)

    # Clone the frontend repo into a 'frontend' subfolder
    frontend_project_path = clone_project_repo(frontend_repo_url, frontend_branch, Path(f"tenants/{tenant}/frontend"))
    print(f"Cloned frontend repo to: {frontend_project_path}")

    # Update compose file to include frontend service
    add_frontend_to_compose_file(tenant, config, frontend_project_path, compose_path)
    print(f"Updated compose file at: {compose_path}")

    # Write frontend .env with the correct API URL using the domain name
    nginx_port = config.get("nginx_port", 8000 + abs(hash(tenant)) % 1000)
    frontend_env = {
        "BASE_URL": f"http://{tenant}.vsync:{nginx_port}/v1/api",
        "REACT_APP_BASE_URL": f"http://{tenant}.vsync:{nginx_port}/v1/api"  # Include both variable names for compatibility
    }
    write_env_file(str(frontend_project_path / ".env"), frontend_env)
    print(f"Written frontend .env to {frontend_project_path / '.env'} with API URL: {frontend_env['BASE_URL']}")

    # This section is removed as it's duplicated below

    # Start containers one by one to better isolate issues
    print(f"Starting frontend container...")
    run(f"docker-compose -f {compose_path.name} up -d {tenant}_frontend", cwd=str(compose_path.parent))
    print(f"Frontend container started.")

    # Start nginx container separately
    print(f"Starting nginx container...")
    run(f"docker-compose -f {compose_path.name} up -d {tenant}_nginx", cwd=str(compose_path.parent))
    print(f"Nginx container started.")

    # Check container status
    print("Checking container status...")
    run(f"docker ps | grep {tenant}", cwd=str(compose_path.parent), _raise=False)

    # Run frontend health checks with the correct port
    nginx_port = config.get("nginx_port", 8000 + abs(hash(tenant)) % 1000)

    # Check if containers are running
    print("Checking container status...")
    run(f"docker ps | grep {tenant}", cwd=str(compose_path.parent), _raise=False)

    # Try direct backend access first
    backend_port = config.get("backend_port", 5000 + abs(hash(tenant)) % 1000)
    backend_url = f"http://localhost:{backend_port}/v1/api"
    print(f"Checking direct backend access at {backend_url}...")
    backend_ok = wait_for_service(backend_url)

    # Then try through nginx
    frontend_url = f"http://{tenant}.vsync:{nginx_port}/"
    api_url = f"http://{tenant}.vsync:{nginx_port}/v1/api"
    print(f"Running frontend health checks at {frontend_url}...")
    frontend_ok = wait_for_service(frontend_url)
    print(f"Running API health checks at {api_url}...")
    api_ok = wait_for_service(api_url)

    print("Health checks completed.")

    # Print access information with multiple options
    print(f"\nAccess your application at:")
    print(f"Frontend via domain: http://{tenant}.vsync:{nginx_port}/")
    print(f"Frontend via localhost: http://localhost:{nginx_port}/")
    print(f"API via domain: http://{tenant}.vsync:{nginx_port}/v1/api")
    print(f"API via localhost: http://localhost:{nginx_port}/v1/api")
    print(f"Direct backend API: http://localhost:{backend_port}/v1/api")

    print(f"Frontend deployment for tenant {tenant} completed.")
