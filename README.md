<div align="center">

![Logo](resources/logo.png)

## VMA CLI
**Multi-Tenant Deployment CLI**

[![Python version](https://img.shields.io/badge/python-%3E=_3.8-green.svg)](https://www.python.org/downloads/)
![Platform Compatibility](https://img.shields.io/badge/platform-linux%20%7C%20macos-blue)

</div>

## VMA CLI

VMA CLI is a command-line utility that helps you deploy and manage multi-tenant applications with ease. It provides a simple interface for deploying backend and frontend services, managing Docker containers, and handling tenant-specific configurations.

## Key features

VMA CLI helps you set up and manage your multi-tenant applications with ease. Here are some of the key features:
- Deploying backend and frontend applications for multiple tenants
- Managing Docker containers for each tenant
- Configuring Nginx for proper routing
- Managing tenant-specific environment variables
- Viewing logs for tenant services
- Listing GitHub repositories

## Installation

### Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- Git

### Installation from GitHub

```sh
git clone git@github.com:vmagautam/vma-cli.git
cd vma-cli
pip install -e .
```

## Basic Usage

**Note:** All VMA CLI commands can be run from any directory.

* Deploy a backend application for a tenant:

  ```sh
  $ vma deploy-backend --tenant [tenant-name] --backend-repo-url [repo-url] --backend-branch [branch]
  ```

* Deploy a frontend application for a tenant:

  ```sh
  $ vma deploy-frontend --tenant [tenant-name] --frontend-repo-url [repo-url] --frontend-branch [branch]
  ```

* View logs for a tenant:

  ```sh
  $ vma logs --tenant [tenant-name]
  ```

* View logs for a specific service:

  ```sh
  $ vma logs --tenant [tenant-name] --app [backend|frontend|nginx]
  ```

* List GitHub repositories:

  ```sh
  $ vma list-github-repos [username]
  ```

* Show VMA CLI help:

  ```sh
  $ vma --help
  ```

## Commands

Here's a list of available commands:

```
Commands:
  add-tenant
  deploy             Deploy an app from a git repository.
  deploy-backend     Deploy the backend application for a tenant.
  deploy-frontend    Deploy the frontend application for a tenant.
  list-github-repos  List all public repositories for a GitHub user.
  list-plugins-cmd   List available plugins.
  logs               Show logs for a tenant/app.
  remove-tenant
  start              Start all apps for a tenant.
  stop               Stop all apps for a tenant.
```

## Tenant Management

VMA CLI creates a structured directory for each tenant under the `tenants/` directory. Each tenant has its own:

- Backend application
- Frontend application
- Nginx configuration
- Docker Compose file
- Environment variables

The system uses Docker containers to isolate each tenant's services while allowing them to communicate through a shared network.

## Environment Configuration

For backend applications, VMA CLI automatically configures:
- Database connections (PostgreSQL)
- Redis connections
- API endpoints
- Session management

For frontend applications, it sets up:
- API base URLs
- Environment-specific configurations
- Port mappings

## Development

To contribute and develop on the VMA CLI tool, clone this repo and create an editable install:

```sh
git clone https://github.com/vmagautam/vma-cli.git
cd vma-cli
pip install -e .
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.