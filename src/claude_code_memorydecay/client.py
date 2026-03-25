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
