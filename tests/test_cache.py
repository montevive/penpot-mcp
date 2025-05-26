"""
Tests for the memory caching functionality.
"""

import time
import pytest
from penpot_mcp.utils.cache import MemoryCache

@pytest.fixture
def memory_cache():
    """Create a MemoryCache instance with a short TTL for testing."""
    return MemoryCache(ttl_seconds=2)

def test_cache_set_get(memory_cache):
    """Test setting and getting a file from cache."""
    test_data = {"test": "data"}
    file_id = "test123"
    
    # Set data in cache
    memory_cache.set(file_id, test_data)
    
    # Get data from cache
    cached_data = memory_cache.get(file_id)
    assert cached_data == test_data

def test_cache_expiration(memory_cache):
    """Test that cached files expire after TTL."""
    test_data = {"test": "data"}
    file_id = "test123"
    
    # Set data in cache
    memory_cache.set(file_id, test_data)
    
    # Data should be available immediately
    assert memory_cache.get(file_id) == test_data
    
    # Wait for cache to expire
    time.sleep(3)
    
    # Data should be expired
    assert memory_cache.get(file_id) is None

def test_cache_clear(memory_cache):
    """Test clearing the cache."""
    test_data = {"test": "data"}
    file_id = "test123"
    
    # Set data in cache
    memory_cache.set(file_id, test_data)
    
    # Verify data is cached
    assert memory_cache.get(file_id) == test_data
    
    # Clear cache
    memory_cache.clear()
    
    # Verify data is gone
    assert memory_cache.get(file_id) is None

def test_get_all_cached_files(memory_cache):
    """Test getting all cached files."""
    test_data1 = {"test": "data1"}
    test_data2 = {"test": "data2"}
    
    # Set multiple files in cache
    memory_cache.set("file1", test_data1)
    memory_cache.set("file2", test_data2)
    
    # Get all cached files
    all_files = memory_cache.get_all_cached_files()
    
    # Verify all files are present
    assert len(all_files) == 2
    assert all_files["file1"] == test_data1
    assert all_files["file2"] == test_data2
    
    # Wait for cache to expire
    time.sleep(3)
    
    # Verify expired files are removed
    all_files = memory_cache.get_all_cached_files()
    assert len(all_files) == 0

def test_cache_nonexistent_file(memory_cache):
    """Test getting a nonexistent file from cache."""
    assert memory_cache.get("nonexistent") is None 