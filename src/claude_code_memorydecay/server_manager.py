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
        embedding_provider: Optional[str] = None,
        embedding_model: Optional[str] = None,
        embedding_api_key: Optional[str] = None,
        embedding_dim: Optional[int] = None,
    ):
        self.pid_dir = Path(pid_dir).expanduser()
        self.pid_file = self.pid_dir / "server.pid"
        self.port = port
        self.core_path = core_path
        self.python_path = python_path
        self.db_path = Path(db_path).expanduser()
        self.embedding_provider = embedding_provider or "local"
        self.embedding_model = embedding_model
        self.embedding_api_key = embedding_api_key
        self.embedding_dim = embedding_dim
        
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
        except Exception:
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
        
        if self.embedding_model:
            args.extend(["--embedding-model", self.embedding_model])
        
        if self.embedding_api_key:
            args.extend(["--embedding-api-key", self.embedding_api_key])
        
        if self.embedding_dim:
            args.extend(["--embedding-dim", str(self.embedding_dim)])
        
        # Start server process
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{self.core_path}/src"

        self.log_file = self.pid_dir / "server.log"
        log_fh = open(self.log_file, "a")

        process = subprocess.Popen(
            args,
            cwd=self.core_path,
            env=env,
            stdout=log_fh,
            stderr=log_fh,
            start_new_session=True  # Detach from parent
        )

        log_fh.close()  # Parent doesn't need the fd; child inherited it

        # Write PID file
        self.pid_file.write_text(str(process.pid))

        # Wait for server to be healthy
        if not self.wait_for_health():
            # Read last lines of log for error context
            error_context = ""
            try:
                log_content = self.log_file.read_text()
                lines = log_content.strip().splitlines()
                last_lines = lines[-20:] if len(lines) > 20 else lines
                error_context = "\n".join(last_lines)
            except Exception:
                pass

            self.stop()
            msg = "Server failed to start within timeout."
            if error_context:
                msg += f"\n\nServer log ({self.log_file}):\n{error_context}"
            else:
                msg += f"\nCheck {self.log_file} for details."
            raise Exception(msg)
        
        return True
    
    def stop(self) -> bool:
        """Stop the server if running."""
        pid = self.get_pid()
        if pid is None:
            return True
        
        try:
            os.kill(pid, signal.SIGTERM)
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
            except Exception:
                pass
            time.sleep(0.05)  # Short sleep for faster tests
        return False
    
    def _remove_pid_file(self):
        """Remove PID file if it exists."""
        try:
            self.pid_file.unlink(missing_ok=True)
        except IOError:
            pass
