"""
GUI Performance Profiling Module
Measures and optimizes GUI detection and initialization performance.
"""

import time
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, Callable, Any
from functools import wraps


@dataclass
class PerformanceMetrics:
    """Performance measurement data."""
    operation: str  # Name of measured operation
    duration_ms: float  # Duration in milliseconds
    start_time: float  # Unix timestamp
    end_time: float  # Unix timestamp
    cached: bool = False  # Whether result was cached
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional data
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class PerformanceProfiler:
    """
    Profiles GUI detection and initialization performance.
    Tracks timing, caching effectiveness, and identifies bottlenecks.
    """
    
    PROFILE_DIR = Path.home() / '.cache/pam-gui-profiles'
    MAX_PROFILE_RECORDS = 1000  # Keep last 1000 measurements
    
    def __init__(self, enabled: bool = True):
        """
        Initialize profiler.
        
        Args:
            enabled: Whether profiling is enabled
        """
        self.enabled = enabled
        self.measurements: Dict[str, list] = {}
        self.session_start = time.time()
        
        # Create profile directory if needed
        if self.enabled:
            self.PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    
    def measure(self, operation: str, cached: bool = False, **metadata) -> Callable:
        """
        Decorator to measure operation timing.
        
        Usage:
            @profiler.measure('detect_gpu')
            def detect_gpu():
                # code here
                pass
        
        Args:
            operation: Operation name
            cached: Whether this is cached result
            **metadata: Additional metadata to store
            
        Returns:
            Decorator function
        """
        if not self.enabled:
            return lambda func: func
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                start_unix = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end = time.time()
                    end_unix = time.time()
                    duration_ms = (end - start) * 1000
                    
                    metric = PerformanceMetrics(
                        operation=operation,
                        duration_ms=duration_ms,
                        start_time=start_unix,
                        end_time=end_unix,
                        cached=cached,
                        metadata=metadata
                    )
                    
                    self._record_metric(metric)
            
            return wrapper
        return decorator
    
    def _record_metric(self, metric: PerformanceMetrics):
        """Record a single measurement."""
        if not self.enabled:
            return
        
        if metric.operation not in self.measurements:
            self.measurements[metric.operation] = []
        
        self.measurements[metric.operation].append(metric)
        
        # Keep size reasonable
        if len(self.measurements[metric.operation]) > self.MAX_PROFILE_RECORDS:
            self.measurements[metric.operation] = self.measurements[metric.operation][-self.MAX_PROFILE_RECORDS:]
    
    def get_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance statistics.
        
        Args:
            operation: Specific operation to analyze, or None for all
            
        Returns:
            Statistics dict with timing info
        """
        if not self.enabled:
            return {}
        
        if operation:
            if operation not in self.measurements:
                return {}
            
            metrics = self.measurements[operation]
            return self._calculate_stats(metrics, operation)
        
        # Calculate stats for all operations
        all_stats = {}
        for op_name, metrics in self.measurements.items():
            all_stats[op_name] = self._calculate_stats(metrics, op_name)
        
        return all_stats
    
    @staticmethod
    def _calculate_stats(metrics: list, operation: str) -> Dict[str, Any]:
        """Calculate statistics from metrics list."""
        if not metrics:
            return {}
        
        durations = [m.duration_ms for m in metrics]
        cached_count = sum(1 for m in metrics if m.cached)
        
        return {
            'operation': operation,
            'count': len(metrics),
            'cached': cached_count,
            'uncached': len(metrics) - cached_count,
            'min_ms': min(durations),
            'max_ms': max(durations),
            'avg_ms': sum(durations) / len(durations),
            'total_ms': sum(durations),
            'cache_hit_rate': cached_count / len(metrics) if metrics else 0.0,
        }
    
    def save_report(self, filepath: Optional[Path] = None) -> Path:
        """
        Save performance report to file.
        
        Args:
            filepath: Path to save report (default: ~/.cache/pam-gui-profiles/report.json)
            
        Returns:
            Path to saved report
        """
        if not self.enabled:
            return Path()
        
        if filepath is None:
            filepath = self.PROFILE_DIR / 'latest_report.json'
        
        # Calculate stats
        stats = self.get_stats()
        
        report = {
            'session_duration_seconds': time.time() - self.session_start,
            'total_measurements': sum(len(m) for m in self.measurements.values()),
            'operations': stats,
            'timestamp': time.time(),
        }
        
        # Save report
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        return filepath
    
    def print_summary(self):
        """Print performance summary to console."""
        if not self.enabled:
            print("[PROFILER] Profiling disabled")
            return
        
        stats = self.get_stats()
        
        print("\n" + "=" * 70)
        print("GUI PERFORMANCE PROFILING SUMMARY")
        print("=" * 70)
        
        for operation, op_stats in stats.items():
            if not op_stats:
                continue
            
            print(f"\n{operation}:")
            print(f"  Count: {op_stats['count']} (cached: {op_stats['cached']}, uncached: {op_stats['uncached']})")
            print(f"  Timing: min={op_stats['min_ms']:.1f}ms, avg={op_stats['avg_ms']:.1f}ms, max={op_stats['max_ms']:.1f}ms")
            print(f"  Cache hit rate: {op_stats['cache_hit_rate']*100:.1f}%")
            print(f"  Total time: {op_stats['total_ms']:.1f}ms")
        
        print("\n" + "=" * 70)
        print(f"Session duration: {time.time() - self.session_start:.1f}s")
        print("=" * 70 + "\n")


# Global profiler instance
_profiler = None

def get_profiler(enabled: bool = True) -> PerformanceProfiler:
    """Get or create global profiler instance."""
    global _profiler
    if _profiler is None:
        _profiler = PerformanceProfiler(enabled=enabled)
    return _profiler


def profile_operation(operation: str, **metadata) -> Callable:
    """
    Convenience decorator for profiling operations.
    
    Usage:
        @profile_operation('detect_gpu')
        def detect_gpu():
            # code
            pass
    """
    profiler = get_profiler()
    return profiler.measure(operation, **metadata)
