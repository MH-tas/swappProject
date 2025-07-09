#!/usr/bin/env python3
"""
Professional Caching System
High-performance caching for Cisco Switch Manager

Author: Professional Network Management Team
Version: 2.0.0
Date: 2024-12-20
"""

import time
import threading
import hashlib
import pickle
import zlib
from typing import Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    data: Any
    timestamp: float
    ttl: int
    access_count: int = 0
    compressed: bool = False
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return time.time() - self.timestamp > self.ttl
    
    @property
    def age(self) -> float:
        """Get age of cache entry in seconds"""
        return time.time() - self.timestamp


class ThreadSafeCache:
    """Thread-safe LRU cache with compression and TTL"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300, 
                 compress_threshold: int = 1024):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.compress_threshold = compress_threshold
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'compressions': 0,
            'total_requests': 0
        }
    
    def _generate_key(self, key_parts: Tuple[Any, ...]) -> str:
        """Generate consistent cache key"""
        key_str = "|".join(str(part) for part in key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _compress_data(self, data: Any) -> Tuple[bytes, bool]:
        """Compress data if beneficial"""
        try:
            serialized = pickle.dumps(data)
            if len(serialized) > self.compress_threshold:
                compressed = zlib.compress(serialized, level=6)
                if len(compressed) < len(serialized) * 0.9:  # Only if 10%+ savings
                    return compressed, True
            return serialized, False
        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            return pickle.dumps(data), False
    
    def _decompress_data(self, data: bytes, compressed: bool) -> Any:
        """Decompress data if needed"""
        try:
            if compressed:
                decompressed = zlib.decompress(data)
                return pickle.loads(decompressed)
            else:
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            raise
    
    def get(self, key_parts: Tuple[Any, ...], default: Any = None) -> Any:
        """Get value from cache"""
        key = self._generate_key(key_parts)
        
        with self.lock:
            self.stats['total_requests'] += 1
            
            if key in self.cache:
                entry = self.cache[key]
                
                if entry.is_expired:
                    del self.cache[key]
                    self.stats['misses'] += 1
                    return default
                
                # Move to end (LRU)
                self.cache.move_to_end(key)
                entry.access_count += 1
                self.stats['hits'] += 1
                
                try:
                    return self._decompress_data(entry.data, entry.compressed)
                except Exception:
                    del self.cache[key]
                    self.stats['misses'] += 1
                    return default
            
            self.stats['misses'] += 1
            return default
    
    def set(self, key_parts: Tuple[Any, ...], value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        key = self._generate_key(key_parts)
        ttl = ttl or self.default_ttl
        
        try:
            data, compressed = self._compress_data(value)
            if compressed:
                self.stats['compressions'] += 1
        except Exception as e:
            logger.warning(f"Failed to serialize cache value: {e}")
            return
        
        with self.lock:
            # Remove if exists
            if key in self.cache:
                del self.cache[key]
            
            # Add new entry
            entry = CacheEntry(
                data=data,
                timestamp=time.time(),
                ttl=ttl,
                compressed=compressed
            )
            
            self.cache[key] = entry
            
            # Evict if over limit
            while len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                self.stats['evictions'] += 1
    
    def invalidate(self, key_parts: Tuple[Any, ...]) -> bool:
        """Remove specific entry from cache"""
        key = self._generate_key(key_parts)
        
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'compressions': 0,
                'total_requests': 0
            }
    
    def cleanup_expired(self) -> int:
        """Remove expired entries"""
        removed = 0
        current_time = time.time()
        
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if current_time - entry.timestamp > entry.ttl
            ]
            
            for key in expired_keys:
                del self.cache[key]
                removed += 1
        
        return removed
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            hit_rate = (self.stats['hits'] / max(1, self.stats['total_requests'])) * 100
            
            return {
                **self.stats,
                'hit_rate': round(hit_rate, 2),
                'size': len(self.cache),
                'max_size': self.max_size,
                'memory_usage': sum(len(entry.data) for entry in self.cache.values())
            }
    
    def cache_decorator(self, ttl: Optional[int] = None):
        """Decorator for caching function results"""
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                # Create cache key from function name and arguments
                key_parts = (func.__name__, args, tuple(sorted(kwargs.items())))
                
                # Try to get from cache
                result = self.get(key_parts)
                if result is not None:
                    return result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                if result is not None:
                    self.set(key_parts, result, ttl)
                
                return result
            
            return wrapper
        return decorator


class CacheManager:
    """Global cache manager with multiple cache types"""
    
    def __init__(self):
        self.interface_cache = ThreadSafeCache(max_size=500, default_ttl=30)
        self.device_cache = ThreadSafeCache(max_size=100, default_ttl=300)
        self.command_cache = ThreadSafeCache(max_size=1000, default_ttl=60)
        self.mac_cache = ThreadSafeCache(max_size=1000, default_ttl=120)
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
    
    def _cleanup_worker(self) -> None:
        """Background cleanup worker"""
        while True:
            try:
                time.sleep(60)  # Cleanup every minute
                
                total_removed = 0
                total_removed += self.interface_cache.cleanup_expired()
                total_removed += self.device_cache.cleanup_expired()
                total_removed += self.command_cache.cleanup_expired()
                total_removed += self.mac_cache.cleanup_expired()
                
                if total_removed > 0:
                    logger.debug(f"Cache cleanup removed {total_removed} expired entries")
                    
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches"""
        return {
            'interface': self.interface_cache.get_stats(),
            'device': self.device_cache.get_stats(),
            'command': self.command_cache.get_stats(),
            'mac': self.mac_cache.get_stats()
        }
    
    def clear_all(self) -> None:
        """Clear all caches"""
        self.interface_cache.clear()
        self.device_cache.clear()
        self.command_cache.clear()
        self.mac_cache.clear()
        logger.info("All caches cleared")


# Global cache manager instance
cache_manager = CacheManager() 