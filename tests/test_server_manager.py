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
