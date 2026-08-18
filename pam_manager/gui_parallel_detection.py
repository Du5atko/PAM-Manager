"""
Parallel Environment Detection Module
Optimizes detection performance through parallel processing and concurrent queries.
"""

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass


@dataclass
class ParallelDetectionResult:
    """Result of parallel detection operation."""
    operation: str  # Operation name
    success: bool  # Whether operation succeeded
    result: Any  # Result value
    duration_ms: float  # Time taken
    error: Optional[str] = None  # Error message if failed


class ParallelDetector:
    """
    Performs environment detection operations in parallel for faster execution.
    Reduces total detection time from sequential to concurrent.
    """
    
    MAX_WORKERS = 4  # Maximum concurrent detection threads
    DETECTION_TIMEOUT = 5  # Timeout per detection in seconds
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize parallel detector.
        
        Args:
            max_workers: Maximum concurrent workers (default: 4)
        """
        self.max_workers = max_workers or self.MAX_WORKERS
        self.results: Dict[str, ParallelDetectionResult] = {}
        self.lock = threading.Lock()
    
    def detect_in_parallel(self, detection_methods: Dict[str, Callable]) -> Dict[str, Any]:
        """
        Run multiple detection methods in parallel.
        
        Args:
            detection_methods: Dict mapping operation names to detection functions
            
        Returns:
            Dict with results for each operation
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_op = {
                executor.submit(self._run_detection, op, func): op
                for op, func in detection_methods.items()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_op, timeout=self.DETECTION_TIMEOUT):
                op = future_to_op[future]
                try:
                    result = future.result(timeout=self.DETECTION_TIMEOUT)
                    results[op] = result
                    self.results[op] = result
                except Exception as e:
                    result = ParallelDetectionResult(
                        operation=op,
                        success=False,
                        result=None,
                        duration_ms=0.0,
                        error=str(e)
                    )
                    results[op] = result
                    self.results[op] = result
        
        return results
    
    @staticmethod
    def _run_detection(operation: str, func: Callable) -> ParallelDetectionResult:
        """Run single detection operation with timing."""
        start = time.time()
        try:
            result = func()
            duration_ms = (time.time() - start) * 1000
            return ParallelDetectionResult(
                operation=operation,
                success=True,
                result=result,
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            return ParallelDetectionResult(
                operation=operation,
                success=False,
                result=None,
                duration_ms=duration_ms,
                error=str(e)
            )
    
    def get_results_dict(self) -> Dict[str, Any]:
        """Get results as simple dict (operation -> value)."""
        return {
            op: result.result 
            for op, result in self.results.items() 
            if result.success
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary."""
        successful = sum(1 for r in self.results.values() if r.success)
        failed = len(self.results) - successful
        total_time = sum(r.duration_ms for r in self.results.values())
        
        return {
            'total_operations': len(self.results),
            'successful': successful,
            'failed': failed,
            'total_duration_ms': total_time,
            'average_duration_ms': total_time / len(self.results) if self.results else 0,
            'errors': {
                op: result.error 
                for op, result in self.results.items() 
                if result.error
            }
        }
    
    def print_summary(self):
        """Print execution summary."""
        summary = self.get_summary()
        
        print("\n" + "=" * 70)
        print("PARALLEL DETECTION SUMMARY")
        print("=" * 70)
        print(f"\nOperations: {summary['total_operations']} total")
        print(f"  Successful: {summary['successful']} ✓")
        print(f"  Failed: {summary['failed']} ✗")
        print(f"\nTiming:")
        print(f"  Total: {summary['total_duration_ms']:.1f}ms")
        print(f"  Average: {summary['average_duration_ms']:.1f}ms per operation")
        
        if summary['errors']:
            print(f"\nErrors:")
            for op, error in summary['errors'].items():
                print(f"  ✗ {op}: {error[:50]}...")
        
        print("\n" + "=" * 70 + "\n")


class ParallelEnvironmentDetector:
    """
    Enhanced environment detector using parallel detection for speed.
    Combines results from parallel operations into GuiCapabilities.
    """
    
    @staticmethod
    def detect_all_parallel() -> 'GuiCapabilities':
        """
        Detect all environment capabilities using parallel detection.
        
        Returns:
            GuiCapabilities object with all detected values
        """
        from pam_manager.gui_environment import GuiEnvironment
        
        detector = ParallelDetector()
        
        # Define detection methods to run in parallel
        detection_methods = {
            'display_server': GuiEnvironment.detect_display_server,
            'x11_server': GuiEnvironment.detect_x11_server,
            'qt_version': GuiEnvironment.detect_qt_version,
            'window_manager': GuiEnvironment.detect_window_manager,
            'remote_x11': GuiEnvironment.detect_remote_x11,
            'gpu_acceleration': GuiEnvironment.detect_gpu_acceleration,
            'x11_extensions': GuiEnvironment.detect_x11_extensions,
            'xorg_capabilities': GuiEnvironment.detect_xorg_capabilities,
            'rendering_backend': GuiEnvironment.detect_rendering_backend,
        }
        
        # Run all detections in parallel
        results = detector.detect_in_parallel(detection_methods)
        
        # Construct GuiCapabilities from results
        return ParallelEnvironmentDetector._build_capabilities(results)
    
    @staticmethod
    def _build_capabilities(results: Dict[str, ParallelDetectionResult]) -> 'GuiCapabilities':
        """Build GuiCapabilities from parallel results."""
        from pam_manager.gui_environment import (
            GuiCapabilities, DisplayServer, X11Server
        )
        
        # Extract successful results
        display_server = results.get('display_server', {}).result or DisplayServer.UNKNOWN
        x11_server = results.get('x11_server', {}).result or X11Server.UNKNOWN
        qt_version = results.get('qt_version', {}).result or 5
        has_window_manager = results.get('window_manager', {}).result or False
        supports_remote = results.get('remote_x11', {}).result or False
        gpu_accel = results.get('gpu_acceleration', {}).result or {}
        x11_ext = results.get('x11_extensions', {}).result or {}
        xorg_caps = results.get('xorg_capabilities', {}).result or {}
        render_backend = results.get('rendering_backend', {}).result or 'software'
        
        # Create capabilities object
        caps = GuiCapabilities(
            display_server=display_server,
            x11_server=x11_server,
            qt_version=qt_version,
            has_window_manager=has_window_manager,
            supports_remote_x11=supports_remote,
            supports_wayland_native=(display_server == DisplayServer.WAYLAND),
            supports_opengl=gpu_accel.get('glx', False),
            supports_vulkan=gpu_accel.get('vulkan', False),
            recommended_backend='wayland' if display_server == DisplayServer.WAYLAND else 'xcb',
            recommended_style='Adwaita' if display_server == DisplayServer.WAYLAND else 'Fusion',
            warnings=[],
            gpu_acceleration=gpu_accel,
            x11_extensions=x11_ext,
            xorg_capabilities=xorg_caps,
            rendering_backend=render_backend,
        )
        
        return caps
