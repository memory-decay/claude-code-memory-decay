# src/claude_code_memorydecay/cli.py
"""CLI for Claude Code memorydecay plugin."""

import os
import sys
from pathlib import Path
from typing import Optional

import click

from .client import MemoryDecayClient
from .server_manager import ServerManager


def find_core_path() -> Optional[str]:
    """Auto-detect memory-decay-core path."""
    # 1. Check environment variable
    if env_path := os.environ.get("MEMORYDECAY_CORE_PATH"):
        if Path(env_path).exists():
            return env_path
    
    # 2. Check sibling directory (same parent as this project)
    sibling = Path(__file__).parent.parent.parent.parent / "memory-decay-core"
    if sibling.exists():
        return str(sibling)
    
    # 3. Check if installed as package
    try:
        import subprocess
        result = subprocess.run(
            ["pip", "show", "memory-decay-core"],
            capture_output=True,
            text=True
        )
        for line in result.stdout.split("\n"):
            if line.startswith("Location:"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    
    return None


def _find_python(core_path: Optional[str]) -> str:
    """Find the right Python for the server. Prefer the core venv over system python."""
    if env_python := os.environ.get("MEMORYDECAY_PYTHON"):
        return env_python
    if core_path:
        venv_python = Path(core_path) / ".venv" / "bin" / "python"
        if venv_python.exists():
            return str(venv_python)
    return "python3"


def get_server_manager() -> ServerManager:
    """Get configured server manager."""
    port = int(os.environ.get("MEMORYDECAY_PORT", "8100"))
    db_path = os.environ.get("MEMORYDECAY_DB_PATH", "~/.memorydecay/memories.db")
    core_path = find_core_path()
    python_path = _find_python(core_path)
    
    return ServerManager(
        port=port,
        core_path=core_path,
        python_path=python_path,
        db_path=db_path
    )


def get_client() -> MemoryDecayClient:
    """Get configured client, ensuring server is running."""
    port = int(os.environ.get("MEMORYDECAY_PORT", "8100"))
    
    # Check if server is running, try to start if not
    manager = get_server_manager()
    if not manager.is_running():
        if manager.core_path:
            click.echo("Starting memory-decay server...", err=True)
            manager.start()
        else:
            raise click.ClickException(
                "Server not running and could not find memory-decay-core. "
                "Set MEMORYDECAY_CORE_PATH environment variable."
            )
    
    return MemoryDecayClient(port=port)


@click.group()
@click.version_option(version=__import__('claude_code_memorydecay').__version__)
def cli():
    """Claude Code memorydecay - human-like memory for AI agents."""
    pass


@cli.group()
def server():
    """Server management commands."""
    pass


@server.command()
def start():
    """Start the memory-decay server."""
    manager = get_server_manager()
    
    if manager.is_running():
        pid = manager.get_pid()
        click.echo(f"Server already running (PID: {pid})")
        return
    
    if not manager.core_path:
        raise click.ClickException(
            "Could not find memory-decay-core. "
            "Set MEMORYDECAY_CORE_PATH environment variable."
        )
    
    try:
        manager.start()
        pid = manager.get_pid()
        click.echo(f"Server started (PID: {pid})")
    except Exception as e:
        raise click.ClickException(f"Failed to start server: {e}")


@server.command()
def stop():
    """Stop the memory-decay server."""
    manager = get_server_manager()
    
    if not manager.is_running():
        click.echo("Server not running")
        return
    
    manager.stop()
    click.echo("Server stopped")


@server.command()
def status():
    """Check server status."""
    manager = get_server_manager()
    
    if manager.is_running():
        pid = manager.get_pid()
        try:
            client = MemoryDecayClient(port=manager.port)
            health = client.health()
            click.echo(f"Server running (PID: {pid})")
            click.echo(f"Tick: {health.get('current_tick', 'unknown')}")
        except Exception as e:
            click.echo(f"Server running (PID: {pid}) but health check failed: {e}")
    else:
        click.echo("Server not running")


@cli.command()
@click.argument('query')
@click.option('--top-k', default=5, help='Number of results to return')
def search(query: str, top_k: int):
    """Search memories."""
    try:
        client = get_client()
        result = client.search(query, top_k=top_k)
        
        if not result.get('results'):
            click.echo("No memories found")
            return
        
        for item in result['results']:
            freshness = _get_freshness(item.get('storage_score', 0))
            click.echo(f"\n[{freshness}] {item['text']}")
            click.echo(f"  Score: {item.get('score', 0):.2f} | "
                      f"Category: {item.get('category', 'unknown')}")
    except Exception as e:
        raise click.ClickException(f"Search failed: {e}")


def _get_freshness(storage_score: float) -> str:
    """Convert storage score to freshness indicator."""
    if storage_score > 0.7:
        return "FRESH"
    elif storage_score > 0.3:
        return "NORMAL"
    else:
        return "STALE"


@cli.command()
@click.argument('text')
@click.option('--importance', default=0.7, type=float, help='Importance 0.0-1.0')
@click.option('--category', default='fact', help='Category: fact, episode, preference, decision')
@click.option('--mtype', default='fact', help='Type: fact or episode')
def store(text: str, importance: float, category: str, mtype: str):
    """Store a memory."""
    try:
        client = get_client()
        result = client.store(
            text=text,
            importance=importance,
            category=category,
            mtype=mtype
        )
        click.echo(f"Stored memory {result['id']}")
    except Exception as e:
        raise click.ClickException(f"Store failed: {e}")


@cli.command()
def tick():
    """Apply time-based decay (auto-tick)."""
    try:
        client = get_client()
        result = client.auto_tick()
        click.echo(f"Applied {result['ticks_applied']} tick(s), "
                  f"current tick: {result['current_tick']}")
    except Exception as e:
        raise click.ClickException(f"Tick failed: {e}")


@cli.command()
@click.option('--from', 'from_path', default='~/.claude/memory',
              help='Path to existing memories to migrate')
def migrate(from_path: str):
    """Migrate existing memories from files."""
    from .migrator import migrate_memories
    
    from_path = Path(from_path).expanduser()
    if not from_path.exists():
        raise click.ClickException(f"Path does not exist: {from_path}")
    
    try:
        client = get_client()
        count = migrate_memories(client, from_path)
        click.echo(f"Migrated {count} memories")
    except Exception as e:
        raise click.ClickException(f"Migration failed: {e}")


def main():
    """Entry point."""
    cli()


if __name__ == '__main__':
    main()
