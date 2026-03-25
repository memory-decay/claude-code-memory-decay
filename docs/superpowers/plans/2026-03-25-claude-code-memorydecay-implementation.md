# Claude Code memorydecay Plugin Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code plugin that integrates memory-decay-core via CLI wrapper, SKILL.md instructions, and hooks for automatic memory decay.

**Architecture:** Python CLI (`memorydecay`) wraps HTTP API to memory-decay-core server, manages lifecycle via PID file, and exposes commands for store/search/tick/migrate. SKILL.md instructs agent when to use commands. Hooks trigger decay on PreCompact and SessionEnd.

**Tech Stack:** Python 3.10+, click, requests, pytest; memory-decay-core (FastAPI backend)

---

## File Structure

```
claude-code-memory-decay/
├── pyproject.toml                     # Package config
├── src/
│   └── claude_code_memorydecay/
│       ├── __init__.py               # Version info
│       ├── cli.py                    # Main CLI entry (click)
│       ├── client.py                 # HTTP client for memory-decay-core
│       ├── server_manager.py         # Server lifecycle (PID, start/stop)
│       └── migrator.py               # Migration from existing memories
├── tests/
│   ├── __init__.py
│   ├── test_cli.py                   # CLI command tests
│   ├── test_client.py                # HTTP client tests
│   ├── test_server_manager.py        # Server lifecycle tests
│   └── test_migrator.py              # Migration tests
├── .claude/
│   ├── skills/
│   │   └── memorydecay/
│   │       └── SKILL.md              # Agent instructions
│   └── hooks/
│       ├── pre-compact               # PreCompact hook script
│       └── session-end               # Session end hook script
└── docs/
    └── superpowers/
        ├── specs/                    # Design spec (already exists)
        └── plans/                    # This file
```

---

## Chunk 1: Project Setup and Dependencies

### Task 1: Create pyproject.toml

**Files:**
- Create: `pyproject.toml`

- [ ] **Step 1: Write pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "claude-code-memorydecay"
version = "0.1.0"
description = "Claude Code plugin for human-like memory decay"
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
dependencies = [
    "click>=8.0.0",
    "requests>=2.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[project.scripts]
memorydecay = "claude_code_memorydecay.cli:main"

[tool.black]
line-length = 100

[tool.ruff]
line-length = 100
```

- [ ] **Step 2: Create directory structure**

```bash
mkdir -p src/claude_code_memorydecay
mkdir -p tests
mkdir -p .claude/skills/memorydecay
mkdir -p .claude/hooks
touch src/claude_code_memorydecay/__init__.py
touch tests/__init__.py
```

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml .claude src tests
git commit -m "chore: project setup with pyproject.toml and directory structure"
```

---

## Chunk 2: HTTP Client Module

### Task 2: Implement HTTP Client for memory-decay-core

**Files:**
- Create: `src/claude_code_memorydecay/client.py`
- Create: `tests/test_client.py`

- [ ] **Step 1: Write failing test for client.store**

```python
# tests/test_client.py
import pytest
from unittest.mock import Mock, patch
from claude_code_memorydecay.client import MemoryDecayClient


class TestMemoryDecayClient:
    def test_store_success(self):
        """Test successful memory store."""
        client = MemoryDecayClient(port=8100)
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "id": "mem-123",
            "text": "Test memory",
            "tick": 42
        }
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            result = client.store("Test memory", importance=0.8)
            
            mock_post.assert_called_once()
            assert result["id"] == "mem-123"
            assert result["text"] == "Test memory"

    def test_search_success(self):
        """Test successful memory search."""
        client = MemoryDecayClient(port=8100)
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "mem-123",
                    "text": "Test result",
                    "score": 0.95,
                    "storage_score": 0.8,
                    "retrieval_score": 0.9,
                    "category": "fact",
                    "created_tick": 10
                }
            ]
        }
        
        with patch('requests.post', return_value=mock_response):
            result = client.search("test query", top_k=5)
            
            assert len(result["results"]) == 1
            assert result["results"][0]["text"] == "Test result"

    def test_auto_tick_success(self):
        """Test auto-tick endpoint."""
        client = MemoryDecayClient(port=8100)
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "ticks_applied": 5,
            "current_tick": 47,
            "elapsed_seconds": 18000
        }
        
        with patch('requests.post', return_value=mock_response):
            result = client.auto_tick()
            
            assert result["ticks_applied"] == 5

    def test_health_check_success(self):
        """Test health check."""
        client = MemoryDecayClient(port=8100)
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "status": "healthy",
            "current_tick": 42
        }
        
        with patch('requests.get', return_value=mock_response):
            result = client.health()
            
            assert result["status"] == "healthy"
            assert result["current_tick"] == 42

    def test_store_failure_raises_exception(self):
        """Test that store failure raises exception."""
        client = MemoryDecayClient(port=8100)
        
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        
        with patch('requests.post', return_value=mock_response):
            with pytest.raises(Exception, match="Store failed"):
                client.store("Test memory")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/roach/.openclaw/workspace/claude-code-memory-decay
python -m pytest tests/test_client.py -v
```
Expected: ImportError or ModuleNotFoundError

- [ ] **Step 3: Implement MemoryDecayClient**

```python
# src/claude_code_memorydecay/client.py
"""HTTP client for memory-decay-core server."""

import requests
from typing import Optional


class MemoryDecayClient:
    """Client for interacting with memory-decay-core HTTP API."""
    
    def __init__(self, port: int = 8100, timeout: float = 30.0):
        self.base_url = f"http://127.0.0.1:{port}"
        self.timeout = timeout
    
    def health(self) -> dict:
        """Check server health."""
        response = requests.get(
            f"{self.base_url}/health",
            timeout=self.timeout
        )
        if not response.ok:
            raise Exception(f"Health check failed: {response.status_code}")
        return response.json()
    
    def store(
        self,
        text: str,
        importance: float = 0.7,
        category: str = "other",
        mtype: str = "fact",
        speaker: Optional[str] = None
    ) -> dict:
        """Store a memory."""
        payload = {
            "text": text,
            "importance": importance,
            "category": category,
            "mtype": mtype,
        }
        if speaker:
            payload["speaker"] = speaker
            
        response = requests.post(
            f"{self.base_url}/store",
            json=payload,
            timeout=self.timeout
        )
        if not response.ok:
            raise Exception(f"Store failed: {response.status_code}")
        return response.json()
    
    def store_batch(self, items: list) -> dict:
        """Store multiple memories."""
        response = requests.post(
            f"{self.base_url}/store-batch",
            json=items,
            timeout=self.timeout
        )
        if not response.ok:
            raise Exception(f"Store batch failed: {response.status_code}")
        return response.json()
    
    def search(self, query: str, top_k: int = 5) -> dict:
        """Search memories."""
        response = requests.post(
            f"{self.base_url}/search",
            json={"query": query, "top_k": top_k},
            timeout=self.timeout
        )
        if not response.ok:
            raise Exception(f"Search failed: {response.status_code}")
        return response.json()
    
    def auto_tick(self) -> dict:
        """Apply time-based decay."""
        response = requests.post(
            f"{self.base_url}/auto-tick",
            timeout=self.timeout
        )
        if not response.ok:
            raise Exception(f"Auto-tick failed: {response.status_code}")
        return response.json()
    
    def delete(self, memory_id: str) -> dict:
        """Delete a memory."""
        response = requests.delete(
            f"{self.base_url}/forget/{memory_id}",
            timeout=self.timeout
        )
        if not response.ok:
            raise Exception(f"Delete failed: {response.status_code}")
        return response.json()
    
    def stats(self) -> dict:
        """Get server stats."""
        response = requests.get(
            f"{self.base_url}/stats",
            timeout=self.timeout
        )
        if not response.ok:
            raise Exception(f"Stats failed: {response.status_code}")
        return response.json()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_client.py -v
```
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add src/claude_code_memorydecay/client.py tests/test_client.py
git commit -m "feat: add HTTP client for memory-decay-core API"
```

---

## Chunk 3: Server Manager Module

### Task 3: Implement Server Lifecycle Manager

**Files:**
- Create: `src/claude_code_memorydecay/server_manager.py`
- Create: `tests/test_server_manager.py`

- [ ] **Step 1: Write failing test for server manager**

```python
# tests/test_server_manager.py
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from claude_code_memorydecay.server_manager import ServerManager


class TestServerManager:
    def test_is_running_false_when_no_pid_file(self, tmp_path):
        """Test is_running returns False when no PID file."""
        manager = ServerManager(pid_dir=str(tmp_path), port=8100)
        assert not manager.is_running()

    def test_is_running_false_when_process_dead(self, tmp_path):
        """Test is_running returns False when process is dead."""
        manager = ServerManager(pid_dir=str(tmp_path), port=8100)
        
        # Create PID file with non-existent PID
        pid_file = tmp_path / "server.pid"
        pid_file.write_text("99999")
        
        assert not manager.is_running()

    def test_get_pid_returns_none_when_no_file(self, tmp_path):
        """Test get_pid returns None when no PID file."""
        manager = ServerManager(pid_dir=str(tmp_path), port=8100)
        assert manager.get_pid() is None

    def test_get_pid_returns_value_when_file_exists(self, tmp_path):
        """Test get_pid returns value from file."""
        manager = ServerManager(pid_dir=str(tmp_path), port=8100)
        
        pid_file = tmp_path / "server.pid"
        pid_file.write_text("12345")
        
        assert manager.get_pid() == 12345

    @patch('claude_code_memorydecay.server_manager.subprocess.Popen')
    @patch('claude_code_memorydecay.server_manager.ServerManager.wait_for_health')
    def test_start_server_success(self, mock_wait, mock_popen, tmp_path):
        """Test starting server successfully."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        mock_wait.return_value = True
        
        manager = ServerManager(
            pid_dir=str(tmp_path),
            port=8100,
            core_path="/fake/path",
            python_path="python3"
        )
        
        # Mock is_running to return False initially
        with patch.object(manager, 'is_running', return_value=False):
            manager.start()
        
        mock_popen.assert_called_once()
        mock_wait.assert_called_once()
        
        # Check PID file was written
        pid_file = tmp_path / "server.pid"
        assert pid_file.exists()
        assert pid_file.read_text().strip() == "12345"

    def test_stop_server_success(self, tmp_path):
        """Test stopping server."""
        manager = ServerManager(pid_dir=str(tmp_path), port=8100)
        
        # Create PID file
        pid_file = tmp_path / "server.pid"
        pid_file.write_text("12345")
        
        with patch('os.kill') as mock_kill:
            manager.stop()
            mock_kill.assert_called_once_with(12345, 15)  # SIGTERM
        
        # PID file should be removed
        assert not pid_file.exists()

    @patch('claude_code_memorydecay.server_manager.requests.get')
    def test_wait_for_health_success(self, mock_get, tmp_path):
        """Test wait_for_health returns True when server healthy."""
        mock_response = Mock()
        mock_response.ok = True
        mock_get.return_value = mock_response
        
        manager = ServerManager(pid_dir=str(tmp_path), port=8100)
        result = manager.wait_for_health(timeout_ms=1000)
        
        assert result is True

    @patch('claude_code_memorydecay.server_manager.requests.get')
    def test_wait_for_health_timeout(self, mock_get, tmp_path):
        """Test wait_for_health returns False on timeout."""
        mock_get.side_effect = Exception("Connection refused")
        
        manager = ServerManager(pid_dir=str(tmp_path), port=8100)
        result = manager.wait_for_health(timeout_ms=100)
        
        assert result is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_server_manager.py -v
```

- [ ] **Step 3: Implement ServerManager**

```python
# src/claude_code_memorydecay/server_manager.py
"""Server lifecycle management for memory-decay-core."""

import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Optional

import requests


class ServerManager:
    """Manages memory-decay-core server lifecycle."""
    
    def __init__(
        self,
        pid_dir: str = "~/.memorydecay",
        port: int = 8100,
        core_path: Optional[str] = None,
        python_path: str = "python3",
        db_path: str = "~/.memorydecay/memories.db",
        embedding_provider: str = "local"
    ):
        self.pid_dir = Path(pid_dir).expanduser()
        self.pid_file = self.pid_dir / "server.pid"
        self.port = port
        self.core_path = core_path
        self.python_path = python_path
        self.db_path = Path(db_path).expanduser()
        self.embedding_provider = embedding_provider
        
        # Ensure directory exists
        self.pid_dir.mkdir(parents=True, exist_ok=True)
    
    def get_pid(self) -> Optional[int]:
        """Get PID from file if it exists."""
        if not self.pid_file.exists():
            return None
        
        try:
            pid = int(self.pid_file.read_text().strip())
            return pid
        except (ValueError, IOError):
            return None
    
    def is_running(self) -> bool:
        """Check if server is running by checking PID and health."""
        pid = self.get_pid()
        if pid is None:
            return False
        
        # Check if process exists
        try:
            os.kill(pid, 0)  # Signal 0 checks if process exists
        except (OSError, ProcessLookupError):
            # Process doesn't exist, clean up stale PID file
            self._remove_pid_file()
            return False
        
        # Also check health endpoint
        try:
            response = requests.get(
                f"http://127.0.0.1:{self.port}/health",
                timeout=2.0
            )
            return response.ok
        except requests.RequestException:
            return False
    
    def start(self) -> bool:
        """Start the server if not already running."""
        if self.is_running():
            return True
        
        if not self.core_path:
            raise ValueError("core_path is required to start server")
        
        # Ensure DB directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build command
        args = [
            self.python_path,
            "-m", "memory_decay.server",
            "--host", "127.0.0.1",
            "--port", str(self.port),
            "--db-path", str(self.db_path),
            "--embedding-provider", self.embedding_provider,
        ]
        
        # Start server process
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{self.core_path}/src"
        
        process = subprocess.Popen(
            args,
            cwd=self.core_path,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True  # Detach from parent
        )
        
        # Write PID file
        self.pid_file.write_text(str(process.pid))
        
        # Wait for server to be healthy
        if not self.wait_for_health():
            # Clean up if failed
            self.stop()
            raise Exception("Server failed to start within timeout")
        
        return True
    
    def stop(self) -> bool:
        """Stop the server if running."""
        pid = self.get_pid()
        if pid is None:
            return True
        
        try:
            os.kill(pid, signal.SIGTERM)
            # Wait for process to terminate
            time.sleep(0.5)
            try:
                os.kill(pid, 0)
                # Still running, force kill
                os.kill(pid, signal.SIGKILL)
            except (OSError, ProcessLookupError):
                pass  # Already stopped
        except (OSError, ProcessLookupError):
            pass  # Process already gone
        finally:
            self._remove_pid_file()
        
        return True
    
    def wait_for_health(self, timeout_ms: int = 15000) -> bool:
        """Wait for server to become healthy."""
        start = time.time()
        while (time.time() - start) * 1000 < timeout_ms:
            try:
                response = requests.get(
                    f"http://127.0.0.1:{self.port}/health",
                    timeout=1.0
                )
                if response.ok:
                    return True
            except requests.RequestException:
                pass
            time.sleep(0.5)
        return False
    
    def _remove_pid_file(self):
        """Remove PID file if it exists."""
        try:
            self.pid_file.unlink(missing_ok=True)
        except IOError:
            pass
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_server_manager.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/claude_code_memorydecay/server_manager.py tests/test_server_manager.py
git commit -m "feat: add server lifecycle manager with PID file tracking"
```

---

## Chunk 4: CLI Implementation

### Task 4: Implement Main CLI with Click

**Files:**
- Create: `src/claude_code_memorydecay/cli.py`
- Create: `tests/test_cli.py`
- Create: `src/claude_code_memorydecay/__init__.py`

- [ ] **Step 1: Write __init__.py**

```python
# src/claude_code_memorydecay/__init__.py
"""Claude Code memorydecay plugin."""

__version__ = "0.1.0"
```

- [ ] **Step 2: Write failing test for CLI**

```python
# tests/test_cli.py
import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch
from claude_code_memorydecay.cli import cli


class TestCli:
    def test_server_start_already_running(self):
        """Test server start when already running."""
        runner = CliRunner()
        
        with patch('claude_code_memorydecay.cli.ServerManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager.is_running.return_value = True
            mock_manager_class.return_value = mock_manager
            
            result = runner.invoke(cli, ['server', 'start'])
            
            assert result.exit_code == 0
            assert "already running" in result.output

    def test_server_stop_not_running(self):
        """Test server stop when not running."""
        runner = CliRunner()
        
        with patch('claude_code_memorydecay.cli.ServerManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager.is_running.return_value = False
            mock_manager_class.return_value = mock_manager
            
            result = runner.invoke(cli, ['server', 'stop'])
            
            assert result.exit_code == 0
            assert "not running" in result.output

    def test_search_success(self):
        """Test search command."""
        runner = CliRunner()
        
        mock_result = {
            "results": [
                {
                    "id": "mem-1",
                    "text": "Test memory",
                    "score": 0.95,
                    "storage_score": 0.8,
                    "category": "fact"
                }
            ]
        }
        
        with patch('claude_code_memorydecay.cli.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client.search.return_value = mock_result
            mock_get_client.return_value = mock_client
            
            result = runner.invoke(cli, ['search', 'test query'])
            
            assert result.exit_code == 0
            assert "Test memory" in result.output

    def test_store_success(self):
        """Test store command."""
        runner = CliRunner()
        
        with patch('claude_code_memorydecay.cli.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client.store.return_value = {"id": "mem-123", "text": "Test"}
            mock_get_client.return_value = mock_client
            
            result = runner.invoke(cli, [
                'store', 'Test memory',
                '--importance', '0.8',
                '--category', 'fact'
            ])
            
            assert result.exit_code == 0
            assert "Stored" in result.output

    def test_tick_success(self):
        """Test tick command."""
        runner = CliRunner()
        
        with patch('claude_code_memorydecay.cli.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client.auto_tick.return_value = {
                "ticks_applied": 5,
                "current_tick": 42
            }
            mock_get_client.return_value = mock_client
            
            result = runner.invoke(cli, ['tick'])
            
            assert result.exit_code == 0
            assert "Applied" in result.output
```

- [ ] **Step 3: Run test to verify it fails**

```bash
python -m pytest tests/test_cli.py -v
```

- [ ] **Step 4: Implement CLI**

```python
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


def get_server_manager() -> ServerManager:
    """Get configured server manager."""
    port = int(os.environ.get("MEMORYDECAY_PORT", "8100"))
    db_path = os.environ.get("MEMORYDECAY_DB_PATH", "~/.memorydecay/memories.db")
    python_path = os.environ.get("MEMORYDECAY_PYTHON", "python3")
    core_path = find_core_path()
    
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
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/test_cli.py -v
```

- [ ] **Step 6: Commit**

```bash
git add src/claude_code_memorydecay/__init__.py src/claude_code_memorydecay/cli.py tests/test_cli.py
git commit -m "feat: implement CLI with server, search, store, tick, migrate commands"
```

---

## Chunk 5: Migration Tool

### Task 5: Implement Migration from Existing Memories

**Files:**
- Create: `src/claude_code_memorydecay/migrator.py`
- Create: `tests/test_migrator.py`

- [ ] **Step 1: Write failing test for migrator**

```python
# tests/test_migrator.py
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from claude_code_memorydecay.migrator import migrate_memories, parse_markdown_file


class TestMigrator:
    def test_parse_markdown_file_with_headers(self, tmp_path):
        """Test parsing markdown file with headers."""
        md_file = tmp_path / "memory.md"
        md_file.write_text("""# Section 1
This is content for section 1.

# Section 2
This is content for section 2.
More content here.
""")
        
        chunks = parse_markdown_file(md_file)
        
        assert len(chunks) == 2
        assert "Section 1" in chunks[0]
        assert "section 1" in chunks[0]
        assert "Section 2" in chunks[1]

    def test_parse_markdown_file_no_headers(self, tmp_path):
        """Test parsing markdown file without headers."""
        md_file = tmp_path / "memory.md"
        md_file.write_text("This is just plain content without headers.")
        
        chunks = parse_markdown_file(md_file)
        
        assert len(chunks) == 1
        assert "plain content" in chunks[0]

    def test_migrate_memories_with_files(self, tmp_path):
        """Test migrating from directory with files."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        
        # Create test files
        (memory_dir / "2024-01-15.md").write_text("# Daily log\nSomething happened today.")
        (memory_dir / "MEMORY.md").write_text("# Important fact\nThis is important.")
        
        mock_client = Mock()
        mock_client.store.return_value = {"id": "mem-1"}
        
        count = migrate_memories(mock_client, memory_dir)
        
        assert count == 2
        assert mock_client.store.call_count == 2

    def test_migrate_skips_short_content(self, tmp_path):
        """Test that very short content is skipped."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        
        (memory_dir / "short.md").write_text("Hi")  # Too short
        
        mock_client = Mock()
        
        count = migrate_memories(mock_client, memory_dir)
        
        assert count == 0
        mock_client.store.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_migrator.py -v
```

- [ ] **Step 3: Implement Migrator**

```python
# src/claude_code_memorydecay/migrator.py
"""Migration tool for existing Claude Code memories."""

import re
from pathlib import Path
from typing import List

from .client import MemoryDecayClient


def parse_markdown_file(file_path: Path) -> List[str]:
    """Parse a markdown file into chunks.
    
    Splits by headers (# ## ###) if present, otherwise returns whole file.
    """
    content = file_path.read_text(encoding='utf-8')
    
    # If no headers, return whole content as single chunk
    if not re.search(r'^#{1,6}\s', content, re.MULTILINE):
        return [content.strip()]
    
    # Split by headers
    chunks = []
    current_chunk = []
    current_header = None
    
    for line in content.split('\n'):
        header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        
        if header_match:
            # Save previous chunk if exists
            if current_chunk:
                chunk_text = '\n'.join(current_chunk).strip()
                if chunk_text:
                    chunks.append(chunk_text)
            
            # Start new chunk with header
            current_header = header_match.group(2)
            current_chunk = [line]
        else:
            if current_chunk:
                current_chunk.append(line)
    
    # Don't forget the last chunk
    if current_chunk:
        chunk_text = '\n'.join(current_chunk).strip()
        if chunk_text:
            chunks.append(chunk_text)
    
    return chunks


def determine_importance(file_path: Path) -> float:
    """Determine importance based on file type."""
    filename = file_path.name.lower()
    
    # User-created MEMORY.md - high importance
    if filename == 'memory.md':
        return 0.8
    
    # Date-based logs - lower importance
    if re.match(r'^\d{4}-\d{2}-\d{2}.*\.md$', filename):
        return 0.4
    
    # Everything else - medium
    return 0.5


def determine_category(file_path: Path) -> str:
    """Determine category based on content hints."""
    filename = file_path.name.lower()
    
    if 'preference' in filename or 'user' in filename:
        return 'preference'
    elif 'decision' in filename:
        return 'decision'
    elif re.match(r'^\d{4}-\d{2}-\d{2}', filename):
        return 'episode'
    else:
        return 'fact'


def migrate_memories(client: MemoryDecayClient, from_path: Path) -> int:
    """Migrate memories from files to memory-decay-core.
    
    Args:
        client: MemoryDecayClient instance
        from_path: Path to directory or file containing memories
        
    Returns:
        Number of memories migrated
    """
    count = 0
    
    if from_path.is_file():
        files = [from_path]
    else:
        files = list(from_path.glob('*.md'))
    
    for file_path in files:
        try:
            chunks = parse_markdown_file(file_path)
            importance = determine_importance(file_path)
            category = determine_category(file_path)
            
            for chunk in chunks:
                # Skip very short chunks
                if len(chunk) < 50:
                    continue
                
                # Split long chunks
                if len(chunk) > 1000:
                    sub_chunks = _split_long_chunk(chunk)
                else:
                    sub_chunks = [chunk]
                
                for sub_chunk in sub_chunks:
                    try:
                        client.store(
                            text=sub_chunk,
                            importance=importance,
                            category=category,
                            mtype='episode' if category == 'episode' else 'fact'
                        )
                        count += 1
                    except Exception as e:
                        print(f"Warning: Failed to store chunk from {file_path}: {e}")
                        continue
                        
        except Exception as e:
            print(f"Warning: Failed to process {file_path}: {e}")
            continue
    
    return count


def _split_long_chunk(chunk: str, max_length: int = 1000) -> List[str]:
    """Split a long chunk into smaller pieces."""
    chunks = []
    paragraphs = chunk.split('\n\n')
    
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_length:
            if current:
                current += '\n\n'
            current += para
        else:
            if current:
                chunks.append(current)
            current = para
    
    if current:
        chunks.append(current)
    
    return chunks if chunks else [chunk[:max_length]]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_migrator.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/claude_code_memorydecay/migrator.py tests/test_migrator.py
git commit -m "feat: add migration tool for existing Claude Code memories"
```

---

## Chunk 6: SKILL.md

### Task 6: Create Agent Instructions

**Files:**
- Create: `.claude/skills/memorydecay/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: memorydecay
description: Human-like memory with decay for Claude Code
---

# Memory System (memorydecay)

You have access to a human-like memory system that decays naturally over time. Important memories persist longer; trivial ones fade away.

## Session Start

At the start of each session, the memory system is automatically available. No action needed - the server starts on first use.

## Commands

Use these commands to interact with your memory:

```bash
# Search for relevant memories
memorydecay search "your query here" [--top-k 5]

# Store an important memory
memorydecay store "memory content" [--importance 0.8] [--category fact]

# Apply time-based decay (called automatically by hooks)
memorydecay tick

# Check server status
memorydecay server status

# Migrate existing memories from files
memorydecay migrate [--from ~/.claude/memory]
```

## When to Store Memories

Proactively store information that will be useful later:

- **Facts** (importance: 0.8): API decisions, architectural patterns, domain knowledge
- **Preferences** (importance: 0.8): User likes/dislikes, style preferences, settings
- **Decisions** (importance: 0.8): Why something was done a certain way, tradeoffs considered
- **Episodes** (importance: 0.5): What was worked on, context for future reference

Store BEFORE context gets too long - don't wait until compaction.

## When to Search Memories

Always search before:
- Answering questions that might have been discussed before
- Making decisions that might have prior context
- Starting work on a topic that might have history

## Freshness Indicators

Search results include freshness:
- **FRESH** (>0.7): Recently recalled or high importance - reliable
- **NORMAL** (0.3-0.7): Moderate decay - probably accurate but verify if critical
- **STALE** (<0.3): Heavily decayed - may be outdated, use with caution

## Automatic Decay

Memories naturally fade over time based on:
- **Importance**: Higher = slower decay
- **Recalls**: Each recall strengthens the memory (testing effect)
- **Time**: Decay applies automatically via hooks on PreCompact and SessionEnd

You don't need to manually manage decay - the system handles it.

## Migration (One-Time)

If you have existing memories in `~/.claude/memory/` or `MEMORY.md`:

```bash
memorydecay migrate --from ~/.claude/memory
```

This imports them with appropriate importance levels based on file type.

## Best Practices

1. **Search first, then decide**: Always check if relevant context exists
2. **Store proactively**: Don't wait to be asked - if something seems worth remembering, store it
3. **Be specific**: Clear, concise memories are more retrievable
4. **Respect freshness**: Stale memories might be outdated - verify before relying on them
5. **Use categories**: Helps with future retrieval and organization

## Troubleshooting

If `memorydecay` commands fail:
1. Check server status: `memorydecay server status`
2. Start manually if needed: `memorydecay server start`
3. Verify memory-decay-core is available at `MEMORYDECAY_CORE_PATH`
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/memorydecay/SKILL.md
git commit -m "docs: add SKILL.md with agent instructions for memory system"
```

---

## Chunk 7: Hooks

### Task 7: Create Hook Scripts

**Files:**
- Create: `.claude/hooks/pre-compact`
- Create: `.claude/hooks/session-end`

- [ ] **Step 1: Write pre-compact hook**

```bash
#!/bin/bash
# PreCompact hook - apply time-based decay before context compression

# Only run if memorydecay is available
if command -v memorydecay &> /dev/null; then
    # Apply decay silently - don't pollute context
    memorydecay tick &> /dev/null || true
fi

# Always exit successfully - don't block compaction
exit 0
```

- [ ] **Step 2: Write session-end hook**

```bash
#!/bin/bash
# Session end hook - apply time-based decay on session end

# Only run if memorydecay is available
if command -v memorydecay &> /dev/null; then
    # Apply decay
    memorydecay tick &> /dev/null || true
fi

# Always exit successfully
exit 0
```

- [ ] **Step 3: Make hooks executable**

```bash
chmod +x .claude/hooks/pre-compact
chmod +x .claude/hooks/session-end
```

- [ ] **Step 4: Commit**

```bash
git add .claude/hooks/pre-compact .claude/hooks/session-end
git commit -m "feat: add PreCompact and SessionEnd hooks for automatic decay"
```

---

## Chunk 8: Installation and Documentation

### Task 8: Create README and Installation Script

**Files:**
- Create: `README.md`
- Create: `install.sh`

- [ ] **Step 1: Write README.md**

```markdown
# Claude Code memorydecay

Human-like memory decay for Claude Code. Important things stick, noise fades.

## Features

- **Decay-aware search**: Retrieve memories ranked by relevance and freshness
- **Automatic lifecycle**: Server starts/stops automatically
- **Shared database**: Works alongside OpenClaw plugin using same memory store
- **Migration tool**: Import existing Claude Code memories
- **Hook integration**: Automatic decay on context compaction and session end

## Installation

### Prerequisites

- Python 3.10+
- [memory-decay-core](https://github.com/memory-decay/memory-decay-core) cloned locally

### Install

```bash
# Clone this repository
git clone <repo-url>
cd claude-code-memorydecay

# Install in editable mode
pip install -e .

# Or install dependencies only
pip install click requests
```

### Configure Claude Code

1. Copy/link skills to your Claude Code directory:
```bash
mkdir -p ~/.claude/skills
cp -r .claude/skills/memorydecay ~/.claude/skills/
```

2. Copy hooks:
```bash
mkdir -p ~/.claude/hooks
cp .claude/hooks/pre-compact ~/.claude/hooks/
cp .claude/hooks/session-end ~/.claude/hooks/
chmod +x ~/.claude/hooks/*
```

3. Set environment variables (optional):
```bash
export MEMORYDECAY_CORE_PATH=/path/to/memory-decay-core
export MEMORYDECAY_DB_PATH=~/.memorydecay/memories.db
export MEMORYDECAY_PORT=8100
```

### Shared Database with OpenClaw

To share the same database with OpenClaw:

1. Update your OpenClaw config (`~/.openclaw/openclaw.json`):
```json
{
  "plugins": {
    "entries": {
      "memory-decay": {
        "enabled": true,
        "config": {
          "dbPath": "~/.memorydecay/memories.db",
          "serverPort": 8100
        }
      }
    }
  }
}
```

2. Both plugins now use the same database at `~/.memorydecay/memories.db`

## Usage

### Search memories
```bash
memorydecay search "API design decisions"
```

### Store a memory
```bash
memorydecay store "User prefers dark mode" --importance 0.8 --category preference
```

### Check status
```bash
memorydecay server status
```

### Migrate existing memories
```bash
memorydecay migrate --from ~/.claude/memory
```

## How It Works

1. **SKILL.md** instructs the agent to use `memorydecay` commands
2. **CLI** wraps HTTP calls to memory-decay-core server
3. **Server Manager** handles PID file and lifecycle
4. **Hooks** trigger automatic decay at key moments
5. **Shared database** with OpenClaw ensures consistency

## Architecture

```
Claude Code Agent
    ↓ (reads SKILL.md)
    ↓ (runs commands)
memorydecay CLI
    ↓ (HTTP)
memory-decay-core (shared with OpenClaw)
    ↓
SQLite + Vector DB (~/.memorydecay/memories.db)
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Format code
black src tests
ruff check src tests
```

## License

MIT
```

- [ ] **Step 2: Write install.sh**

```bash
#!/bin/bash
set -e

echo "Installing Claude Code memorydecay plugin..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Install package
echo "Installing package..."
pip install -e .

# Create directories
mkdir -p ~/.claude/skills
mkdir -p ~/.claude/hooks
mkdir -p ~/.memorydecay

# Copy skills
echo "Installing skills..."
cp -r .claude/skills/memorydecay ~/.claude/skills/

# Copy hooks
echo "Installing hooks..."
cp .claude/hooks/pre-compact ~/.claude/hooks/
cp .claude/hooks/session-end ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-compact
chmod +x ~/.claude/hooks/session-end

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Set MEMORYDECAY_CORE_PATH environment variable to your memory-decay-core directory"
echo "2. Run 'memorydecay server start' to verify installation"
echo "3. Run 'memorydecay migrate --from ~/.claude/memory' to import existing memories"
```

- [ ] **Step 3: Make install.sh executable**

```bash
chmod +x install.sh
```

- [ ] **Step 4: Commit**

```bash
git add README.md install.sh
git commit -m "docs: add README and installation script"
```

---

## Chunk 9: Final Integration and Testing

### Task 9: Run All Tests and Verify

- [ ] **Step 1: Install package in development mode**

```bash
cd /home/roach/.openclaw/workspace/claude-code-memory-decay
pip install -e ".[dev]"
```

- [ ] **Step 2: Run all tests**

```bash
pytest tests/ -v --tb=short
```
Expected: All tests pass

- [ ] **Step 3: Verify CLI is available**

```bash
memorydecay --version
memorydecay --help
```
Expected: Version and help displayed

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final integration and test setup" || echo "Nothing to commit"
```

---

## Summary

This plan implements a complete Claude Code plugin with:

1. **CLI** (`memorydecay`) - wraps HTTP API with automatic server lifecycle
2. **SKILL.md** - agent instructions for using memory system
3. **Hooks** - automatic decay on PreCompact and SessionEnd
4. **Migration** - import existing Claude Code memories
5. **Shared database** - works alongside OpenClaw plugin

All tasks use TDD approach with tests written first, then implementation.
