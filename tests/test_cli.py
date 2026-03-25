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
