import click
import requests

@click.command()
@click.argument("username")
def list_github_repos(username):
    """List all public repositories for a GitHub user."""
    url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(url)
    
    if response.status_code == 200:
        repos = response.json()
        click.echo(f"Found {len(repos)} repositories for {username}:")
        for repo in repos:
            click.echo(f"- {repo['name']}: {repo['html_url']}")
    else:
        click.echo(f"Error: {response.status_code} - {response.text}")