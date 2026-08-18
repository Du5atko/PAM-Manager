"""
GUI Performance Benchmarking Framework
Measures and compares performance improvements from Phase 4 optimizations.
"""

import time
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    name: str
    description: str
    duration_ms: float
    iterations: int = 1
    
    @property
    def avg_duration_ms(self) -> float:
        """Average duration per iteration."""
        return self.duration_ms / self.iterations if self.iterations > 0 else 0


@dataclass
class BenchmarkComparison:
    """Comparison between two benchmark results."""
    baseline: BenchmarkResult
    optimized: BenchmarkResult
    speedup_ratio: float = 0.0
    improvement_percent: float = 0.0
    
    def __post_init__(self):
        """Calculate speedup and improvement."""
        if self.baseline.avg_duration_ms > 0:
            self.speedup_ratio = self.baseline.avg_duration_ms / self.optimized.avg_duration_ms
            self.improvement_percent = ((self.baseline.avg_duration_ms - self.optimized.avg_duration_ms) 
                                       / self.baseline.avg_duration_ms * 100)


class GuiPerformanceBenchmarks:
    """Benchmarking framework for GUI performance improvements."""
    
    @staticmethod
    def benchmark_detection_sequential() -> BenchmarkResult:
        """Benchmark sequential environment detection (Phase 0-3 baseline)."""
        from pam_manager.gui_environment import GuiEnvironment
        
        start = time.perf_counter()
        for _ in range(3):
            GuiEnvironment.detect_all()
        duration = (time.perf_counter() - start) * 1000
        
        return BenchmarkResult(
            name="sequential_detection",
            description="Sequential environment detection (Phase 0-3 baseline)",
            duration_ms=duration,
            iterations=3
        )
    
    @staticmethod
    def benchmark_detection_parallel() -> BenchmarkResult:
        """Benchmark parallel environment detection (Phase 4 optimized)."""
        try:
            from pam_manager.gui_parallel_detection import ParallelEnvironmentDetector
            
            start = time.perf_counter()
            for _ in range(3):
                ParallelEnvironmentDetector.detect_all_parallel()
            duration = (time.perf_counter() - start) * 1000
            
            return BenchmarkResult(
                name="parallel_detection",
                description="Parallel environment detection (Phase 4 optimized)",
                duration_ms=duration,
                iterations=3
            )
        except ImportError:
            return BenchmarkResult(
                name="parallel_detection",
                description="Parallel detection not available",
                duration_ms=0,
                iterations=0
            )
    
    @staticmethod
    def benchmark_cache_hits() -> BenchmarkResult:
        """Benchmark cached detection (Phase 4 with cache hits)."""
        try:
            from pathlib import Path
            from pam_manager.gui_advanced_cache import AdvancedCache
            from pam_manager.gui_parallel_detection import ParallelEnvironmentDetector
            
            cache = AdvancedCache(cache_dir=Path("/tmp/pam-gui-cache"))
            
            # Warm up cache
            cache.set("detection", ParallelEnvironmentDetector.detect_all_parallel())
            
            # Benchmark cache hits
            start = time.perf_counter()
            for _ in range(100):  # Many cache hits
                cache.get("detection")
            duration = (time.perf_counter() - start) * 1000
            
            return BenchmarkResult(
                name="cached_detection",
                description="Cached environment detection (Phase 4 with cache hits)",
                duration_ms=duration,
                iterations=100
            )
        except ImportError:
            return BenchmarkResult(
                name="cached_detection",
                description="Cache not available",
                duration_ms=0,
                iterations=0
            )
    
    @staticmethod
    def benchmark_adapter_creation() -> BenchmarkResult:
        """Benchmark GUI adapter creation time."""
        from pam_manager.gui_adapters import AdapterFactory
        
        start = time.perf_counter()
        for _ in range(10):
            AdapterFactory.get_adapter('default')
        duration = (time.perf_counter() - start) * 1000
        
        return BenchmarkResult(
            name="adapter_creation",
            description="GUI adapter factory creation",
            duration_ms=duration,
            iterations=10
        )
    
    @staticmethod
    def benchmark_config_optimization() -> BenchmarkResult:
        """Benchmark configuration optimization analysis."""
        try:
            from pam_manager.gui_environment import GuiEnvironment
            from pam_manager.gui_config_optimizer import ConfigurationOptimizer, OptimizationLevel
            
            caps = GuiEnvironment.detect_all()
            
            start = time.perf_counter()
            for _ in range(10):
                ConfigurationOptimizer.analyze_and_recommend(caps, OptimizationLevel.BALANCED)
            duration = (time.perf_counter() - start) * 1000
            
            return BenchmarkResult(
                name="config_optimization",
                description="Configuration optimization analysis (Phase 4)",
                duration_ms=duration,
                iterations=10
            )
        except ImportError:
            return BenchmarkResult(
                name="config_optimization",
                description="Config optimizer not available",
                duration_ms=0,
                iterations=0
            )
    
    @staticmethod
    def run_all_benchmarks() -> Dict[str, Any]:
        """Run all benchmarks and compare results."""
        results = {
            "sequential": GuiPerformanceBenchmarks.benchmark_detection_sequential(),
            "parallel": GuiPerformanceBenchmarks.benchmark_detection_parallel(),
            "cached": GuiPerformanceBenchmarks.benchmark_cache_hits(),
            "adapter": GuiPerformanceBenchmarks.benchmark_adapter_creation(),
            "optimizer": GuiPerformanceBenchmarks.benchmark_config_optimization(),
        }
        
        # Calculate comparisons
        comparisons = {}
        
        if results["sequential"].duration_ms > 0 and results["parallel"].duration_ms > 0:
            comparisons["parallel_vs_sequential"] = BenchmarkComparison(
                baseline=results["sequential"],
                optimized=results["parallel"]
            )
        
        if results["sequential"].duration_ms > 0 and results["cached"].duration_ms > 0:
            comparisons["cached_vs_sequential"] = BenchmarkComparison(
                baseline=results["sequential"],
                optimized=results["cached"]
            )
        
        return {
            "benchmarks": {k: asdict(v) for k, v in results.items()},
            "comparisons": {k: {
                "speedup": v.speedup_ratio,
                "improvement_percent": v.improvement_percent,
                "baseline_ms": v.baseline.avg_duration_ms,
                "optimized_ms": v.optimized.avg_duration_ms,
            } for k, v in comparisons.items()},
            "summary": {
                "total_benchmarks": len(results),
                "comparisons_available": len(comparisons),
                "best_speedup": max((v.speedup_ratio for v in comparisons.values()), default=1.0),
            }
        }
    
    @staticmethod
    def print_benchmark_report():
        """Run benchmarks and print formatted report."""
        print("=" * 70)
        print("PAM Manager - GUI Performance Benchmarks")
        print("=" * 70)
        print()
        
        results = GuiPerformanceBenchmarks.run_all_benchmarks()
        
        # Print individual results
        print("BENCHMARK RESULTS:")
        print("-" * 70)
        for name, result in results["benchmarks"].items():
            print(f"\n{name.upper()}:")
            print(f"  Description: {result['description']}")
            print(f"  Duration: {result['duration_ms']:.2f} ms ({result['iterations']} iterations)")
            if result['iterations'] > 0:
                print(f"  Average: {result['duration_ms'] / result['iterations']:.2f} ms per run")
        
        # Print comparisons
        print()
        print("PERFORMANCE IMPROVEMENTS (Phase 4):")
        print("-" * 70)
        for name, comparison in results["comparisons"].items():
            print(f"\n{name.replace('_', ' ').title()}:")
            print(f"  Speedup: {comparison['speedup']:.1f}x faster")
            print(f"  Improvement: {comparison['improvement_percent']:.1f}%")
            print(f"  Baseline: {comparison['baseline_ms']:.2f} ms")
            print(f"  Optimized: {comparison['optimized_ms']:.2f} ms")
        
        # Print summary
        print()
        print("SUMMARY:")
        print("-" * 70)
        print(f"Total benchmarks run: {results['summary']['total_benchmarks']}")
        print(f"Performance comparisons: {results['summary']['comparisons_available']}")
        print(f"Best speedup achieved: {results['summary']['best_speedup']:.1f}x")
        
        print()
        print("=" * 70)


if __name__ == '__main__':
    GuiPerformanceBenchmarks.print_benchmark_report()
