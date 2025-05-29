import subprocess
import logging
import os
import shutil
from pathlib import Path
from typing import Optional
import secrets
import string
import json
import yaml
import importlib
import time
import requests
from jinja2 import Template
import git
import random

# Generic shell execution

def run(cmd: str, cwd: Optional[str] = None, env: Optional[dict] = None, _raise: bool = True):
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, env=env, check=_raise, capture_output=True, text=True)
        print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        if _raise:
            print(f"Command failed with exit code {e.returncode}:")
            print("--- STDOUT ---")
            print(e.stdout)
            print("--- STDERR ---")
            print(e.stderr)
            raise
        return e.stdout

def log(message: str, level: int = 0):
    logging.log(logging.INFO if level == 0 else logging.WARNING, message)

# Jinja2 templating
from jinja2 import Environment, FileSystemLoader

def get_template_env(template_dir: str):
    return Environment(loader=FileSystemLoader(template_dir))

# Config file helpers

def read_json(path: str):
    with open(path, 'r') as f:
        return json.load(f)

def write_json(path: str, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def read_yaml(path: str):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def write_yaml(path: str, data):
    with open(path, 'w') as f:
        yaml.safe_dump(data, f)

# Plugin loader utility

def load_plugin(name: str):
    return importlib.import_module(f"bench.plugins.{name}")

def random_string(length=12):
    return ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(length))

def generate_tenant_config(tenant):
    tenant_config_path = Path(f"tenants/{tenant}/config/tenant_config.yaml")
    config = {}

    if tenant_config_path.exists():
        try:
            config = read_yaml(str(tenant_config_path))
            print(f"Read existing tenant config from {tenant_config_path}")
        except Exception as e:
            print(f"Error reading tenant config {tenant_config_path}: {e}")
            config = {}

    db_name = f"{tenant}_db" # Keep this as the primary DB for the container
    db_user = f"{tenant}_user"

    db_master_name = f"{tenant}_master"
    db_transactional_name = f"{tenant}_transactional"

    # Generate new db_pass only if it doesn't exist in config
    db_pass = config.get("db_pass")
    if not db_pass:
        db_pass = random_string(16)
        print(f"Generated new database password for tenant {tenant}")
    else:
        print(f"Using existing database password for tenant {tenant}")

    # Use existing ports if available, otherwise generate
    backend_port = config.get("backend_port", 5000 + abs(hash(tenant)) % 1000)
    frontend_port = config.get("frontend_port", backend_port + 1000)
    nginx_port = config.get("nginx_port", 8000 + abs(hash(tenant)) % 1000)
    redis_pass = config.get("redis_pass", random_string(16))
    # Use tenant-specific container names in URLs
    redis_url = config.get("redis_url", f"redis://:{redis_pass}@{tenant}_redis:6379")

    # Update config dictionary with potentially new values or existing ones
    config.update({
        "db_name": db_name,
        "db_user": db_user,
        "db_pass": db_pass,
        "db_master_name": db_master_name,
        "db_transactional_name": db_transactional_name,
        "backend_port": backend_port,
        "frontend_port": frontend_port,
        "nginx_port": nginx_port,
        "backend_url": f"http://{tenant}.vsync",
        "redis_pass": redis_pass,
        "redis_url": redis_url,
        "db_server": f"{tenant}_db"  # Add tenant-specific DB server
    })

    # Save the updated config back to the file
    os.makedirs(tenant_config_path.parent, exist_ok=True)
    write_yaml(str(tenant_config_path), config)
    print(f"Saved tenant config to {tenant_config_path}")

    return config

def write_env_file(path, env_dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for k, v in env_dict.items():
            f.write(f"{k}={v}\n")

def wait_for_service(url, timeout=60):
    print(f"Waiting for {url} ...")
    for i in range(timeout):
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                print(f"Service at {url} is up!")
                return True
            else:
                print(f"Attempt {i+1}/{timeout}: Service returned status code {r.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"Attempt {i+1}/{timeout}: Connection refused")
        except Exception as e:
            print(f"Attempt {i+1}/{timeout}: {str(e)[:100]}")
        time.sleep(1)
    print(f"Service at {url} did not become healthy in {timeout} seconds.")
    return False

# This function is no longer used since we create the nginx config in add_frontend_to_compose_file
def generate_nginx_config_advanced(tenant, config, nginx_path):
    # Check if nginx_path is a directory and remove it
    if os.path.isdir(nginx_path):
        shutil.rmtree(nginx_path)
        print(f"Removed directory at {nginx_path}")
    
    nginx_template = """
server {
    listen 80;
    server_name {{ tenant }}.vsync localhost;

    location /v1/api {
        proxy_pass http://{{ tenant }}_backend:5004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://{{ tenant }}_frontend:80/;
        proxy_set_header Host $host;
    }
}
"""
    rendered = Template(nginx_template).render(
        tenant=tenant,
        backend_port=config['backend_port'],
        frontend_port=config['frontend_port']
    )
    
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(nginx_path), exist_ok=True)
    
    if os.path.exists(nginx_path):
        if os.path.isdir(nginx_path):
            shutil.rmtree(nginx_path)
        else:
            os.remove(nginx_path)

    with open(nginx_path, "w") as f:
        f.write(rendered)
    
    print(f"Nginx config written to {nginx_path}")
    return nginx_path

def add_tenant_to_hosts(tenant: str, password: Optional[str] = None, config=None):
    # Use localhost explicitly instead of 127.0.0.1 for better compatibility
    hosts_line = f"127.0.0.1 {tenant}.vsync\n"
    hosts_path = "/etc/hosts"
    try:
        # Check if already present
        with open(hosts_path, "r") as f:
            if f"{tenant}.vsync" in f.read():
                print(f"/etc/hosts already contains {tenant}.vsync")
                # Try to ping the domain to verify it's working
                try:
                    subprocess.run(f"ping -c 1 {tenant}.vsync", shell=True, capture_output=True, text=True)
                    print(f"Successfully pinged {tenant}.vsync")
                except:
                    print(f"Warning: Could not ping {tenant}.vsync")
            else:
                # Try direct write
                try:
                    with open(hosts_path, "a") as f:
                        f.write(hosts_line)
                    print(f"Added {tenant}.vsync to /etc/hosts")
                except PermissionError:
                    # Use sudo tee if not writable
                    print(f"/etc/hosts not writable, trying with sudo...")
                    if password is None:
                        password = os.environ.get("HOSTS_SUDO_PASS", "gautam")
                    cmd = f'echo "{password}" | sudo -S sh -c "echo \'{hosts_line.strip()}\' >> {hosts_path}"'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"Added {tenant}.vsync to /etc/hosts (with sudo)")
                    else:
                        print(f"Failed to add {tenant}.vsync to /etc/hosts: {result.stderr}")
    except Exception as e:
        print(f"Error updating /etc/hosts: {e}")
    
    # Print access instructions with direct URLs
    if config:
        nginx_port = config.get("nginx_port", 8000 + abs(hash(tenant)) % 1000)
        backend_port = config.get("backend_port", 5000 + abs(hash(tenant)) % 1000)
        print(f"\nAccess options:")
        print(f"1. Via domain: http://{tenant}.vsync:{nginx_port}/")
        print(f"2. Via localhost: http://localhost:{nginx_port}/")
        print(f"3. Direct backend: http://localhost:{backend_port}/v1/api")
        print(f"4. API via domain: http://{tenant}.vsync:{nginx_port}/v1/api")
        
        # Also print the exact URL to use for frontend .env BASE_URL
        print(f"\nFrontend API URL (for .env): http://{tenant}.vsync:{nginx_port}/v1/api")

def clone_project_repo(repo_url, branch, dest_path):
    """Clone a Git repository to the specified destination path."""
    tenant_dir = dest_path.parent
    target_path = dest_path
    
    print(f"Cloning {repo_url} (branch {branch}) into {target_path} ...")
    try:
        # Make sure parent directory exists
        tenant_dir.mkdir(parents=True, exist_ok=True)
        
        # If target directory exists but is not empty, remove it first
        if target_path.exists():
            if any(target_path.iterdir()):
                print(f"Target directory {target_path} exists and is not empty. Removing it first.")
                shutil.rmtree(target_path)
            else:
                target_path.rmdir()
        
        # Clone directly into the target folder name
        git.Repo.clone_from(repo_url, str(target_path), branch=branch)
    except git.GitCommandError as e:
        print(f"Git clone failed: {e.stderr}")
        raise

    # If .gitmodules exists in the cloned repo, update submodules
    if (target_path / ".gitmodules").exists():
        print("Initializing git submodules ...")
        run("git submodule update --init --recursive", cwd=str(target_path))
        print("Submodules initialized.")

    return target_path

def generate_base_compose_file(tenant, config, backend_project_path):
    # Generate compose file with infra (DB, Redis) and backend service
    backend_dir = backend_project_path # This is the path to the backend folder inside the tenant dir
    compose = {
        "version": "3.8",
        "services": {
            f"{tenant}_db": {
                "image": "postgres:15",
                "container_name": f"{tenant}_db",
                "environment": {
                    "POSTGRES_DB": config["db_master_name"],
                    "POSTGRES_USER": config["db_user"],
                    "POSTGRES_PASSWORD": config["db_pass"]
                },
                "volumes": [f"{tenant}_db_data:/var/lib/postgresql/data"],
                "networks": [tenant],
                "healthcheck": { # Add healthcheck for PostgreSQL
                    "test": ["CMD-SHELL", "bash -c 'PGUSER=$POSTGRES_USER pg_isready'"],
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 5,
                    "start_period": "10s"
                }
            },
            f"{tenant}_redis": {
                "image": "redis:7",
                "container_name": f"{tenant}_redis",
                "environment": {
                    "REDIS_PASSWORD": config["redis_pass"]
                },
                "volumes": [f"{tenant}_redis_data:/var/lib/redis/data"],
                "networks": [tenant]
            },
            f"{tenant}_backend": {
                "build": str(backend_dir.relative_to(backend_dir.parent)), # Build context is relative to the directory containing the compose file (tenant dir)
                "container_name": f"{tenant}_backend",
                "env_file": str((backend_dir / ".env").relative_to(backend_dir.parent)), # env_file is relative to the directory containing the compose file (tenant dir)
                "ports": [f"{config['backend_port']}:5004"], # Map host port to internal port 5004
                "depends_on": {
                    f"{tenant}_db": {
                        "condition": "service_healthy"
                    },
                    f"{tenant}_redis": {
                        "condition": "service_started" # Redis doesn't need a healthcheck for this purpose
                    }
                },
                "networks": [tenant],
                "extra_hosts": [f"{tenant}.vsync:127.0.0.1"],
                "command": f"sh -c 'sleep 15 && npm run deploy'", # Add delay to ensure DB is ready
                "environment": {
                    "NODE_ENV": "development",
                    "DB_SERVER": f"{tenant}_db"
                }
            }
        },
        "volumes": {
            f"{tenant}_db_data": {},
            f"{tenant}_redis_data": {},
            f"{tenant}_nginx_config": { # Define volume for nginx.conf
                "driver": "local"
            }
        },
        "networks": {
            tenant: {}
        }
    }
    # Compose file is placed in the tenant directory
    compose_path = backend_project_path.parent / "docker-compose.yml"
    with open(compose_path, "w") as f:
        yaml.safe_dump(compose, f, sort_keys=False)
    print(f"docker-compose.yml written to {compose_path}")
    return compose_path

def add_frontend_to_compose_file(tenant, config, frontend_project_path, compose_path):
    # Add frontend service to an existing compose file
    frontend_dir = frontend_project_path # This is the path to the frontend folder inside the tenant dir
    try:
        compose_data = read_yaml(str(compose_path))
    except FileNotFoundError:
        print(f"Error: docker-compose.yml not found at {compose_path}. Cannot add frontend service.")
        return

    compose_data["services"][f"{tenant}_frontend"] = {
        "build": str(frontend_dir.relative_to(frontend_dir.parent)), # Build context relative to the directory containing the compose file (tenant dir)
        "container_name": f"{tenant}_frontend",
        "env_file": str((frontend_dir / ".env").relative_to(frontend_dir.parent)), # env_file relative to the directory containing the compose file (tenant dir)
        "ports": [f"{config['frontend_port']}:3001"],
        "depends_on": [f"{tenant}_backend"],
        "networks": [tenant],
        "extra_hosts": [f"{tenant}.vsync:127.0.0.1"],
        "command": "npm start",
        "environment": {
            "PORT": "3001"
        }
    }

    # Add Nginx service with dynamic port based on tenant
    nginx_port = config.get("nginx_port", 8000 + abs(hash(tenant)) % 1000)
    
    # Check if nginx.conf is a directory and remove it if it is
    nginx_conf_path = f"tenants/{tenant}/nginx.conf"
    if os.path.isdir(nginx_conf_path):
        shutil.rmtree(nginx_conf_path)
        print(f"Removed directory at {nginx_conf_path}")
    
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(nginx_conf_path), exist_ok=True)
    
    # Create the nginx config file with port 3001 for frontend
    with open(nginx_conf_path, "w") as f:
        f.write(f"""
server {{
    listen 80;
    server_name {tenant}.vsync localhost;

    location /v1/api {{
        proxy_pass http://{tenant}_backend:5004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }}

    location / {{
        proxy_pass http://{tenant}_frontend:3001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }}
}}
""")
    print(f"Created nginx config at {nginx_conf_path}")
    
    # Use absolute path for volume mount
    nginx_conf_abs_path = os.path.abspath(nginx_conf_path)
    
    compose_data["services"][f"{tenant}_nginx"] = {
        "image": "nginx:latest",
        "container_name": f"{tenant}_nginx",
        "volumes": [
            f"{nginx_conf_abs_path}:/etc/nginx/conf.d/default.conf:ro"
        ],
        "ports": [f"{nginx_port}:80"], # Use dynamic port to avoid conflicts
        "depends_on": [f"{tenant}_backend", f"{tenant}_frontend"],
        "networks": [tenant],
        "extra_hosts": [f"{tenant}.vsync:127.0.0.1"],
        "restart": "on-failure"
    }

    # Ensure the network is defined if it wasn't already (should be there from backend deploy)
    if tenant not in compose_data["networks"]:
        compose_data["networks"][tenant] = {}

    # Add nginx.conf volume definition
    if "volumes" not in compose_data:
        compose_data["volumes"] = {}
    compose_data["volumes"][f"{tenant}_nginx_config"] = {
        "driver": "local"
    }

    write_yaml(str(compose_path), compose_data)
    print(f"Added {tenant}_frontend and {tenant}_nginx services and volumes to {compose_path}")

def create_infrastructure(tenant, compose_path):
    print(f"Bringing up infrastructure containers (DB, Redis) for tenant {tenant}...")
    run(f"docker-compose -f {compose_path} up -d {tenant}_db {tenant}_redis", cwd=str(compose_path.parent))
    print(f"Infrastructure containers started for tenant {tenant}.")

def setup_and_start_backend(tenant, vsync_project_path, backend_path):
    backend_dir = vsync_project_path / backend_path
    if not backend_dir.exists():
        print(f"Backend directory not found at {backend_dir}. Skipping backend setup.")
        return

    print(f"Setting up and starting backend for tenant {tenant} in {backend_dir}...")

    # Auto-install npm dependencies
    print(f"Installing npm dependencies in {backend_dir} ...")
    run("npm install", cwd=str(backend_dir))

    # Build backend (if applicable)
    # This part might need to be dynamic based on plugin system later
    # For now, assuming nodejs plugin handles build if script exists
    pkg = os.path.join(backend_dir, "package.json")
    if os.path.exists(pkg):
        try:
            import json
            with open(pkg) as f:
                data = json.load(f)
            if "build" in data.get("scripts", {}):
                print(f"[nodejs] Running build script in {backend_dir}")
                run("npm run build", cwd=str(backend_dir))
        except Exception as e:
            print(f"Error during backend build: {e}")
            # Decide if this should be a fatal error or just a warning

    # Start backend container
    compose_path = vsync_project_path.parent / "docker-compose.yml"
    print(f"Starting backend container {tenant}_backend...")
    run(f"docker-compose -f {compose_path} up -d --no-deps {tenant}_backend", cwd=str(compose_path.parent))
    print(f"Backend container {tenant}_backend started.")

def setup_and_start_frontend(tenant, vsync_project_path, frontend_path):
    frontend_dir = vsync_project_path / frontend_path
    if not frontend_dir.exists():
        print(f"Frontend directory not found at {frontend_dir}. Skipping frontend setup.")
        return

    print(f"Setting up and starting frontend for tenant {tenant} in {frontend_dir}...")

    # Auto-install npm dependencies
    print(f"Installing npm dependencies in {frontend_dir} ...")
    run("npm install", cwd=str(frontend_dir))

    # Build frontend (if applicable)
    # This part might need to be dynamic based on plugin system later
    # For now, assuming nodejs/react plugin handles build if script exists
    pkg = os.path.join(frontend_dir, "package.json")
    if os.path.exists(pkg):
        try:
            import json
            with open(pkg) as f:
                data = json.load(f)
            if "build" in data.get("scripts", {}):
                print(f"[nodejs/react] Running build script in {frontend_dir}")
                run("npm run build", cwd=str(frontend_dir))
        except Exception as e:
            print(f"Error during frontend build: {e}")
            # Decide if this should be a fatal error or just a warning

    # Start frontend container
    compose_path = vsync_project_path.parent / "docker-compose.yml"
    print(f"Starting frontend container {tenant}_frontend...")
    run(f"docker-compose -f {compose_path} up -d --no-deps {tenant}_frontend", cwd=str(compose_path.parent))
    print(f"Frontend container {tenant}_frontend started.")

def setup_tenant(tenant):
    # This function seems to be the old hardcoded one. Keep it for now or remove if not used.
    config = generate_tenant_config(tenant)
    os.makedirs(f"tenants/{tenant}/vendor_portal_backend", exist_ok=True)
    os.makedirs(f"tenants/{tenant}/vsync_frontend", exist_ok=True)
    setup_tenant_envs(tenant, config)
    generate_docker_compose(tenant, config)
    generate_nginx_config(tenant, config)
    print(f"Tenant {tenant} setup complete.")
    print(f"DB: {config['db_name']} User: {config['db_user']} Pass: {config['db_pass']}")
    print(f"Backend: http://{tenant}.vsync  Frontend: http://{tenant}.vsync")
    print(f"Run: docker-compose -f tenants/{tenant}/docker-compose.yml up -d")
    print(f"Nginx config: tenants/{tenant}/nginx.conf")

def setup_tenant_envs(tenant, config):
    # This function also seems to be part of the old hardcoded setup. Keep or remove.
    # Backend .env
    backend_env = {
        "DB_NAME": config["db_name"],
        "DB_USER": config["db_user"],
        "DB_PASS": config["db_pass"],
        "DB_HOST": "db",
        "DB_PORT": "5432",
        "REDIS_URL": config["redis_url"],
        "DB_SERVER": "postgres"
    }
    write_env_file(f"tenants/{tenant}/vendor_portal_backend/.env", backend_env)

    # Frontend .env
    frontend_env = {
        "REACT_APP_BACKEND_URL": f"http://{tenant}.vsync/api"
    }
    write_env_file(f"tenants/{tenant}/vsync_frontend/.env", frontend_env)

def generate_docker_compose(tenant, config):
    # This function also seems to be part of the old hardcoded setup. Keep or remove.
    import yaml
    compose = {
        "version": "3.8",
        "services": {
            f"{tenant}_db": {
                "image": "postgres:15",
                "container_name": f"{tenant}_db",
                "environment": {
                    "POSTGRES_DB": config["db_master_name"],
                    "POSTGRES_USER": config["db_user"],
                    "POSTGRES_PASSWORD": config["db_pass"]
                },
                "volumes": [f"{tenant}_db_data:/var/lib/postgresql/data"],
                "networks": [tenant],
                "healthcheck": { # Add healthcheck for PostgreSQL
                    "test": ["CMD-SHELL", "bash -c 'PGUSER=$POSTGRES_USER pg_isready'"],
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 5,
                    "start_period": "10s"
                }
            },
            f"{tenant}_redis": {
                "image": "redis:7",
                "container_name": f"{tenant}_redis",
                "environment": {
                    "REDIS_PASSWORD": config["redis_pass"]
                },
                "volumes": [f"{tenant}_redis_data:/var/lib/redis/data"],
                "networks": [tenant]
            },
            f"{tenant}_backend": {
                "build": "./vendor_portal_backend",
                "container_name": f"{tenant}_backend",
                "env_file": f"./vendor_portal_backend/.env",
                "ports": [f"{config['backend_port']}:3000"],
                "depends_on": [f"{tenant}_db", f"{tenant}_redis"],
                "networks": [tenant]
            },
            f"{tenant}_frontend": {
                "build": "./vsync_frontend",
                "container_name": f"{tenant}_frontend",
                "env_file": f"./vsync_frontend/.env",
                "ports": [f"{config['frontend_port']}:80"],
                "depends_on": [f"{tenant}_backend"],
                "networks": [tenant]
            }
        },
        "volumes": {
            f"{tenant}_db_data": {},
            f"{tenant}_redis_data": {}
        },
        "networks": {
            tenant: {}
        }
    }
    os.makedirs(f"tenants/{tenant}", exist_ok=True)
    with open(f"tenants/{tenant}/docker-compose.yml", "w") as f:
        yaml.safe_dump(compose, f, sort_keys=False)

def generate_nginx_conf(tenant, tenant_port):
    nginx_conf_path = f"tenants/{tenant}/nginx.conf"
    os.makedirs(os.path.dirname(nginx_conf_path), exist_ok=True)

    nginx_conf_content = f"""
server {{
    listen 80;
    server_name localhost;

    location / {{
        proxy_pass http://{tenant}_frontend:{tenant_port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }}
}}
"""
    with open(nginx_conf_path, "w") as f:
        f.write(nginx_conf_content.strip())

# Renamed to avoid recursive call issues
def clone_repo(repo_url: str, branch: str, dest_path: Path):
    """Clone a Git repository."""
    from git import Repo
    log(f"Cloning repository {repo_url} into {dest_path}", level=0)
    
    # Make sure parent directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # If destination exists but is not empty, remove it first
    if dest_path.exists():
        if any(dest_path.iterdir()):
            log(f"Destination {dest_path} exists and is not empty. Removing it first.", level=1)
            shutil.rmtree(dest_path)
        else:
            dest_path.rmdir()
            
    Repo.clone_from(repo_url, dest_path, branch=branch)
    return dest_path

def setup_and_start_backend(tenant: str, app_path: Path):
    """Setup and start backend container for a tenant."""
    compose_file = Path("tenants") / tenant / "docker-compose.yml"
    log(f"Setting up backend for tenant {tenant}", level=0)
    # Generate Docker Compose file
    compose_content = f"""
    version: '3.8'
    services:
      backend:
        build: {app_path}
        ports:
          - "{random.randint(3000, 4000)}:3000"
        environment:
          - NODE_ENV=production
    """
    write_yaml(compose_file, yaml.safe_load(compose_content))
    # Start container
    run(f"docker-compose -f {compose_file} up -d")

def generate_nginx_config_advanced(tenant: str):
    """Generate Nginx configuration for a tenant."""
    nginx_file = Path("tenants") / tenant / "nginx.conf"
    log(f"Generating Nginx configuration for tenant {tenant}", level=0)
    nginx_content = f"""
    server {{
        listen 80;
        server_name {tenant}.example.com;

        location / {{
            proxy_pass http://localhost:{random.randint(3000, 4000)};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }}
    }}
    """
    nginx_file.write_text(nginx_content)
    run(f"docker exec nginx-container nginx -s reload")

# Remove the monolithic setup_tenant_structure_agnostic
# def setup_tenant_structure_agnostic(tenant, vsync_project_path, backend_path, frontend_path):
#     ...
