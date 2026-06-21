import click
import subprocess
import os

@click.group()
def cli():
    """Omnigent (Agent Top) CLI tool for managing AI Agents."""
    pass

@cli.command()
def start():
    """Start the Omnigent backend services (Docker compose & Django)."""
    click.echo("Starting Omnigent Backend Infrastructure...")
    subprocess.run(["docker-compose", "up", "-d"], cwd=os.path.join(os.path.dirname(__file__), '..'))
    click.echo("Services started. Make sure to run Django migrations if you haven't yet.")
    # Here we would normally start daphne and celery worker processes
    click.echo("Backend is up!")

@cli.command()
def top():
    """Launch the Omnigent Terminal UI."""
    from .tui.app import OmnigentApp
    app = OmnigentApp()
    app.run()

@cli.command()
@click.argument('task')
def spawn(task):
    """Spawn a new Agent with a specific task."""
    click.echo(f"Spawning agent for task: {task}")
    # Here we would normally hit the Django REST API to spawn the agent
    # e.g., requests.post('http://localhost:8000/api/agents/spawn', json={'task': task})

if __name__ == '__main__':
    cli()
