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
