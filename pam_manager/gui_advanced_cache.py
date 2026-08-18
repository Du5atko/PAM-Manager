"""
Advanced Caching Strategy Module
Intelligent caching with invalidation triggers, TTL, and dependency tracking.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass, asdict
from functools import wraps


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""
    key: str  # Cache key
    value: Any  # Cached value
    timestamp: float  # Cache creation time
    ttl_seconds: int  # Time to live
    dependencies: list  # List of dependency keys
    hits: int = 0  # Number of cache hits
    misses: int = 0  # Number of cache misses
    
    def is_valid(self) -> bool:
        """Check if cache entry is still valid."""
        age_seconds = time.time() - self.timestamp
        return age_seconds < self.ttl_seconds
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class AdvancedCache:
    """
    Intelligent caching system with TTL, dependencies, and invalidation.
    """
    
    DEFAULT_TTL = 3600  # 1 hour default TTL
    CACHE_DIR = Path.home() / '.cache/pam-gui-advanced'
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize advanced cache.
        
        Args:
            cache_dir: Directory for persistent cache
        """
        self.cache_dir = cache_dir or self.CACHE_DIR
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.invalidation_triggers: Dict[str, list] = {}  # key -> list of dependent keys
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        # Check memory cache first
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if entry.is_valid():
                entry.hits += 1
                return entry.value
            else:
                # Expired - remove from cache
                del self.memory_cache[key]
        
        # Try persistent cache
        persistent_value = self._load_from_disk(key)
        if persistent_value is not None:
            self.memory_cache[key] = persistent_value
            if persistent_value.is_valid():
                persistent_value.hits += 1
                return persistent_value.value
        
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, 
            dependencies: Optional[list] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live (default: 1 hour)
            dependencies: List of dependency keys for invalidation
        """
        if ttl_seconds is None:
            ttl_seconds = self.DEFAULT_TTL
        
        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=time.time(),
            ttl_seconds=ttl_seconds,
            dependencies=dependencies or [],
        )
        
        # Store in memory
        self.memory_cache[key] = entry
        
        # Store on disk
        self._save_to_disk(entry)
        
        # Track invalidation triggers
        if dependencies:
            for dep in dependencies:
                if dep not in self.invalidation_triggers:
                    self.invalidation_triggers[dep] = []
                if key not in self.invalidation_triggers[dep]:
                    self.invalidation_triggers[dep].append(key)
    
    def invalidate(self, key: str):
        """
        Invalidate cache entry and all dependents.
        
        Args:
            key: Key to invalidate
        """
        # Remove from memory
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # Remove from disk
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            cache_file.unlink()
        
        # Invalidate all dependent keys
        if key in self.invalidation_triggers:
            for dependent_key in self.invalidation_triggers[key]:
                self.invalidate(dependent_key)
    
    def invalidate_by_pattern(self, pattern: str):
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Pattern to match (e.g., 'gpu_*')
        """
        import fnmatch
        
        keys_to_invalidate = [
            key for key in self.memory_cache.keys()
            if fnmatch.fnmatch(key, pattern)
        ]
        
        for key in keys_to_invalidate:
            self.invalidate(key)
    
    def cleanup_expired(self):
        """Remove all expired entries from memory and disk."""
        # Memory cleanup
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if not entry.is_valid()
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        # Disk cleanup
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    entry = CacheEntry(**data)
                    if not entry.is_valid():
                        cache_file.unlink()
            except Exception:
                pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.memory_cache)
        valid_entries = sum(1 for e in self.memory_cache.values() if e.is_valid())
        total_hits = sum(e.hits for e in self.memory_cache.values())
        total_misses = sum(e.misses for e in self.memory_cache.values())
        
        hit_rate = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'expired_entries': total_entries - valid_entries,
            'total_hits': total_hits,
            'total_misses': total_misses,
            'hit_rate': hit_rate,
        }
    
    def _load_from_disk(self, key: str) -> Optional[CacheEntry]:
        """Load cache entry from disk."""
        cache_file = self.cache_dir / f"{key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                return CacheEntry(**data)
        except Exception:
            return None
    
    def _save_to_disk(self, entry: CacheEntry):
        """Save cache entry to disk."""
        cache_file = self.cache_dir / f"{entry.key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(entry.to_dict(), f)
        except Exception:
            pass


def cached_operation(ttl_seconds: int = 3600, dependencies: Optional[list] = None):
    """
    Decorator for caching operation results.
    
    Usage:
        @cached_operation(ttl_seconds=3600)
        def detect_gpu():
            # code
            pass
    """
    _cache = None
    
    def get_cache():
        nonlocal _cache
        if _cache is None:
            _cache = AdvancedCache()
        return _cache
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key
            cache_key = f"{func.__module__}.{func.__name__}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl_seconds=ttl_seconds, 
                     dependencies=dependencies)
            
            return result
        
        return wrapper
    return decorator


# Global cache instance
_global_cache = None

def get_global_cache() -> AdvancedCache:
    """Get or create global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = AdvancedCache()
    return _global_cache
