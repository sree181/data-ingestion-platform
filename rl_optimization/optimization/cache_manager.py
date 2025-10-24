"""
Cache Manager
High-performance caching system for RL training data and model artifacts
"""

import os
import pickle
import hashlib
import time
import threading
from typing import Any, Dict, List, Optional, Union, Callable
from pathlib import Path
import structlog
from datetime import datetime, timedelta
import json
import numpy as np

logger = structlog.get_logger(__name__)

class CacheEntry:
    """Individual cache entry with metadata"""
    
    def __init__(self, key: str, value: Any, ttl: Optional[float] = None):
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.access_count = 0
        self.ttl = ttl  # Time to live in seconds
        self.size_bytes = self._calculate_size()
    
    def _calculate_size(self) -> int:
        """Calculate approximate size in bytes"""
        try:
            return len(pickle.dumps(self.value))
        except Exception:
            return 0
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def access(self):
        """Record access to this entry"""
        self.last_accessed = time.time()
        self.access_count += 1
    
    def get_age(self) -> float:
        """Get age in seconds"""
        return time.time() - self.created_at
    
    def get_idle_time(self) -> float:
        """Get idle time in seconds"""
        return time.time() - self.last_accessed

class CacheManager:
    """
    High-performance caching system
    - LRU eviction policy
    - TTL support
    - Memory and disk caching
    - Thread-safe operations
    - Cache statistics and monitoring
    """
    
    def __init__(
        self,
        max_memory_size: int = 100 * 1024 * 1024,  # 100MB
        max_disk_size: int = 1024 * 1024 * 1024,   # 1GB
        cache_dir: str = "cache",
        enable_disk_cache: bool = True,
        compression_level: int = 6
    ):
        """
        Initialize cache manager
        
        Args:
            max_memory_size: Maximum memory cache size in bytes
            max_disk_size: Maximum disk cache size in bytes
            cache_dir: Directory for disk cache
            enable_disk_cache: Whether to enable disk caching
            compression_level: Compression level for disk cache (1-9)
        """
        self.max_memory_size = max_memory_size
        self.max_disk_size = max_disk_size
        self.cache_dir = Path(cache_dir)
        self.enable_disk_cache = enable_disk_cache
        self.compression_level = compression_level
        
        # Create cache directory
        if self.enable_disk_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory cache
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.current_memory_size = 0
        
        # Disk cache metadata
        self.disk_cache_metadata: Dict[str, Dict[str, Any]] = {}
        self.current_disk_size = 0
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'disk_writes': 0,
            'disk_reads': 0,
            'compression_savings': 0
        }
        
        # Load existing disk cache metadata
        self._load_disk_metadata()
        
        logger.info("CacheManager initialized", 
                   max_memory_size=max_memory_size,
                   max_disk_size=max_disk_size,
                   cache_dir=str(cache_dir),
                   enable_disk_cache=enable_disk_cache)
    
    def _load_disk_metadata(self):
        """Load disk cache metadata from file"""
        try:
            metadata_file = self.cache_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    self.disk_cache_metadata = json.load(f)
                    self.current_disk_size = sum(
                        entry.get('size_bytes', 0) 
                        for entry in self.disk_cache_metadata.values()
                    )
                logger.info("Loaded disk cache metadata", 
                           entries=len(self.disk_cache_metadata))
        except Exception as e:
            logger.error(f"Failed to load disk cache metadata: {e}")
            self.disk_cache_metadata = {}
    
    def _save_disk_metadata(self):
        """Save disk cache metadata to file"""
        try:
            metadata_file = self.cache_dir / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(self.disk_cache_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save disk cache metadata: {e}")
    
    def _generate_key(self, key: Union[str, Any]) -> str:
        """Generate cache key from input"""
        if isinstance(key, str):
            return key
        
        try:
            # Use hash of serialized object
            key_str = str(key)
            return hashlib.md5(key_str.encode()).hexdigest()
        except Exception:
            return str(hash(key))
    
    def _get_disk_path(self, key: str) -> Path:
        """Get disk path for cache entry"""
        return self.cache_dir / f"{key}.cache"
    
    def get(self, key: Union[str, Any], default: Any = None) -> Any:
        """
        Get value from cache
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        cache_key = self._generate_key(key)
        
        with self.lock:
            # Try memory cache first
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                if not entry.is_expired():
                    entry.access()
                    self.stats['hits'] += 1
                    logger.debug("Cache hit (memory)", key=cache_key)
                    return entry.value
                else:
                    # Remove expired entry
                    del self.memory_cache[cache_key]
                    self.current_memory_size -= entry.size_bytes
            
            # Try disk cache
            if self.enable_disk_cache and cache_key in self.disk_cache_metadata:
                try:
                    disk_path = self._get_disk_path(cache_key)
                    if disk_path.exists():
                        with open(disk_path, 'rb') as f:
                            value = pickle.load(f)
                        
                        # Check TTL
                        metadata = self.disk_cache_metadata[cache_key]
                        if metadata.get('ttl') is None or \
                           time.time() - metadata['created_at'] < metadata['ttl']:
                            
                            # Move to memory cache if there's space
                            self._add_to_memory_cache(cache_key, value, metadata.get('ttl'))
                            
                            self.stats['hits'] += 1
                            self.stats['disk_reads'] += 1
                            logger.debug("Cache hit (disk)", key=cache_key)
                            return value
                        else:
                            # Remove expired disk entry
                            self._remove_disk_entry(cache_key)
                
                except Exception as e:
                    logger.error(f"Failed to read from disk cache: {e}")
                    self._remove_disk_entry(cache_key)
            
            self.stats['misses'] += 1
            logger.debug("Cache miss", key=cache_key)
            return default
    
    def put(self, key: Union[str, Any], value: Any, ttl: Optional[float] = None) -> bool:
        """
        Put value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successfully cached
        """
        cache_key = self._generate_key(key)
        
        with self.lock:
            try:
                # Add to memory cache
                success = self._add_to_memory_cache(cache_key, value, ttl)
                
                # Also add to disk cache if enabled
                if self.enable_disk_cache:
                    self._add_to_disk_cache(cache_key, value, ttl)
                
                return success
                
            except Exception as e:
                logger.error(f"Failed to cache value: {e}")
                return False
    
    def _add_to_memory_cache(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Add entry to memory cache"""
        try:
            entry = CacheEntry(key, value, ttl)
            
            # Check if we need to evict
            while (self.current_memory_size + entry.size_bytes > self.max_memory_size and 
                   self.memory_cache):
                self._evict_lru_entry()
            
            # Add entry
            if key in self.memory_cache:
                old_entry = self.memory_cache[key]
                self.current_memory_size -= old_entry.size_bytes
            
            self.memory_cache[key] = entry
            self.current_memory_size += entry.size_bytes
            
            logger.debug("Added to memory cache", key=key, size=entry.size_bytes)
            return True
            
        except Exception as e:
            logger.error(f"Failed to add to memory cache: {e}")
            return False
    
    def _add_to_disk_cache(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Add entry to disk cache"""
        try:
            # Check disk space
            while (self.current_disk_size > self.max_disk_size and 
                   self.disk_cache_metadata):
                self._evict_oldest_disk_entry()
            
            # Serialize and save
            disk_path = self._get_disk_path(key)
            with open(disk_path, 'wb') as f:
                pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Update metadata
            file_size = disk_path.stat().st_size
            self.disk_cache_metadata[key] = {
                'created_at': time.time(),
                'size_bytes': file_size,
                'ttl': ttl
            }
            self.current_disk_size += file_size
            
            # Save metadata
            self._save_disk_metadata()
            
            self.stats['disk_writes'] += 1
            logger.debug("Added to disk cache", key=key, size=file_size)
            return True
            
        except Exception as e:
            logger.error(f"Failed to add to disk cache: {e}")
            return False
    
    def _evict_lru_entry(self):
        """Evict least recently used entry from memory cache"""
        if not self.memory_cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self.memory_cache.keys(),
            key=lambda k: self.memory_cache[k].last_accessed
        )
        
        entry = self.memory_cache[lru_key]
        del self.memory_cache[lru_key]
        self.current_memory_size -= entry.size_bytes
        self.stats['evictions'] += 1
        
        logger.debug("Evicted LRU entry", key=lru_key, size=entry.size_bytes)
    
    def _evict_oldest_disk_entry(self):
        """Evict oldest entry from disk cache"""
        if not self.disk_cache_metadata:
            return
        
        # Find oldest entry
        oldest_key = min(
            self.disk_cache_metadata.keys(),
            key=lambda k: self.disk_cache_metadata[k]['created_at']
        )
        
        self._remove_disk_entry(oldest_key)
    
    def _remove_disk_entry(self, key: str):
        """Remove entry from disk cache"""
        try:
            if key in self.disk_cache_metadata:
                metadata = self.disk_cache_metadata[key]
                self.current_disk_size -= metadata.get('size_bytes', 0)
                
                # Remove file
                disk_path = self._get_disk_path(key)
                if disk_path.exists():
                    disk_path.unlink()
                
                # Remove metadata
                del self.disk_cache_metadata[key]
                self._save_disk_metadata()
                
                logger.debug("Removed disk entry", key=key)
                
        except Exception as e:
            logger.error(f"Failed to remove disk entry: {e}")
    
    def delete(self, key: Union[str, Any]) -> bool:
        """Delete entry from cache"""
        cache_key = self._generate_key(key)
        
        with self.lock:
            deleted = False
            
            # Remove from memory cache
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                del self.memory_cache[cache_key]
                self.current_memory_size -= entry.size_bytes
                deleted = True
            
            # Remove from disk cache
            if cache_key in self.disk_cache_metadata:
                self._remove_disk_entry(cache_key)
                deleted = True
            
            return deleted
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            # Clear memory cache
            self.memory_cache.clear()
            self.current_memory_size = 0
            
            # Clear disk cache
            if self.enable_disk_cache:
                for key in list(self.disk_cache_metadata.keys()):
                    self._remove_disk_entry(key)
                self.disk_cache_metadata.clear()
                self.current_disk_size = 0
            
            logger.info("Cache cleared")
    
    def cleanup_expired(self):
        """Remove expired entries"""
        with self.lock:
            # Clean memory cache
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                entry = self.memory_cache[key]
                del self.memory_cache[key]
                self.current_memory_size -= entry.size_bytes
            
            # Clean disk cache
            if self.enable_disk_cache:
                current_time = time.time()
                expired_disk_keys = [
                    key for key, metadata in self.disk_cache_metadata.items()
                    if metadata.get('ttl') is not None and
                       current_time - metadata['created_at'] > metadata['ttl']
                ]
                
                for key in expired_disk_keys:
                    self._remove_disk_entry(key)
            
            logger.info("Cleaned up expired entries", 
                       memory_expired=len(expired_keys),
                       disk_expired=len(expired_disk_keys) if self.enable_disk_cache else 0)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0.0
            
            return {
                'memory_cache': {
                    'entries': len(self.memory_cache),
                    'size_bytes': self.current_memory_size,
                    'max_size_bytes': self.max_memory_size,
                    'utilization': self.current_memory_size / self.max_memory_size
                },
                'disk_cache': {
                    'entries': len(self.disk_cache_metadata),
                    'size_bytes': self.current_disk_size,
                    'max_size_bytes': self.max_disk_size,
                    'utilization': self.current_disk_size / self.max_disk_size
                } if self.enable_disk_cache else None,
                'performance': {
                    'hits': self.stats['hits'],
                    'misses': self.stats['misses'],
                    'hit_rate': hit_rate,
                    'evictions': self.stats['evictions'],
                    'disk_writes': self.stats['disk_writes'],
                    'disk_reads': self.stats['disk_reads']
                }
            }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get detailed memory usage information"""
        with self.lock:
            entries_by_size = sorted(
                [(key, entry.size_bytes) for key, entry in self.memory_cache.items()],
                key=lambda x: x[1],
                reverse=True
            )
            
            return {
                'total_entries': len(self.memory_cache),
                'total_size_bytes': self.current_memory_size,
                'largest_entries': entries_by_size[:10],
                'average_entry_size': self.current_memory_size / len(self.memory_cache) if self.memory_cache else 0
            }

# Global cache instance
_global_cache: Optional[CacheManager] = None

def get_global_cache() -> CacheManager:
    """Get global cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
    return _global_cache

def set_global_cache(cache: CacheManager):
    """Set global cache instance"""
    global _global_cache
    _global_cache = cache

# Decorator for caching function results
def cached(ttl: Optional[float] = None, cache_key_prefix: str = ""):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds
        cache_key_prefix: Prefix for cache keys
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [cache_key_prefix, func.__name__, str(args), str(sorted(kwargs.items()))]
            cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cache = get_global_cache()
            result = cache.get(cache_key)
            
            if result is not None:
                return result
            
            # Compute result
            result = func(*args, **kwargs)
            
            # Cache result
            cache.put(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator
