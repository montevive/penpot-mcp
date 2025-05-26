"""
Cache utilities for Penpot MCP server.
"""

import time
from typing import Optional, Dict, Any

class MemoryCache:
    """In-memory cache implementation with TTL support."""
    
    def __init__(self, ttl_seconds: int = 600):
        """
        Initialize the memory cache.
        
        Args:
            ttl_seconds: Time to live in seconds (default 10 minutes)
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        
    def get(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a file from cache if it exists and is not expired.
        
        Args:
            file_id: The ID of the file to retrieve
            
        Returns:
            The cached file data or None if not found/expired
        """
        if file_id not in self._cache:
            return None
            
        cache_data = self._cache[file_id]
        
        # Check if cache is expired
        if time.time() - cache_data['timestamp'] > self.ttl_seconds:
            del self._cache[file_id]  # Remove expired cache
            return None
            
        return cache_data['data']
            
    def set(self, file_id: str, data: Dict[str, Any]) -> None:
        """
        Store a file in cache.
        
        Args:
            file_id: The ID of the file to cache
            data: The file data to cache
        """
        self._cache[file_id] = {
            'timestamp': time.time(),
            'data': data
        }
            
    def clear(self) -> None:
        """Clear all cached files."""
        self._cache.clear()
                
    def get_all_cached_files(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all valid cached files.
        
        Returns:
            Dictionary mapping file IDs to their cached data
        """
        result = {}
        current_time = time.time()
        
        # Create a list of expired keys to remove
        expired_keys = []
        
        for file_id, cache_data in self._cache.items():
            if current_time - cache_data['timestamp'] <= self.ttl_seconds:
                result[file_id] = cache_data['data']
            else:
                expired_keys.append(file_id)
                
        # Remove expired entries
        for key in expired_keys:
            del self._cache[key]
                    
        return result 