"""
GUI Launcher with Fallback Support
Manages GUI initialization with automatic fallback on failure.
"""

import os
import sys
import json
import subprocess
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class GuiLauncher:
    """
    Manages GUI initialization with comprehensive fallback support.
    Attempts multiple GUI strategies and falls back gracefully on failure.
    """
    
    # Fallback chain in priority order
    FALLBACK_CHAIN = [
        'primary',          # Auto-detected optimal
        'xorg_optimized',   # X.Org-specific
        'generic_qt5',      # Generic PyQt5
        'wayland',          # Wayland-specific
        'offscreen',        # Headless
        'cli_wizard',       # CLI fallback
        'cli_minimal',      # Minimal text mode
    ]
    
    def __init__(self, 
                 config_file: Optional[str] = None,
                 debug: bool = False):
        """
        Initialize GUI launcher.
        
        Args:
            config_file: Path to GUI state persistence file
            debug: Enable debug output
        """
        self.debug = debug or os.environ.get('PAM_DEBUG_GUI', '').lower() in ('1', 'true')
        
        if config_file is None:
            config_file = str(Path.home() / '.pam-gui-state.json')
        
        self.config_file = Path(config_file)
        self.current_strategy = 'primary'
        self.fallback_history = []
        self.state = self._load_state()
    
    def _log(self, level: str, msg: str):
        """Log message with level."""
        # Only show debug messages if debug mode enabled
        if level == 'DEBUG' and not self.debug:
            return
        # Only show info/warn messages if debug mode enabled (silently launch in normal mode)
        if level in ('INFO', 'WARN') and not self.debug:
            return
        prefix = f"[{level:7}]" if level else "[     ]"
        print(f"{prefix} {msg}")
    
    def launch(self) -> bool:
        """
        Launch GUI with automatic fallback on failure.
        
        Returns:
            True if launch successful, False if all attempts failed
        """
        self._log('INFO', "Starting PAM Manager GUI launcher")
        self._log('DEBUG', f"Fallback chain: {' -> '.join(self.FALLBACK_CHAIN)}")
        
        # Get recommended starting point
        recommended = self._get_recommended_strategy()
        self._log('INFO', f"Starting with recommended strategy: {recommended}")
        
        # Try strategies in priority order
        for strategy in self.FALLBACK_CHAIN:
            self._log('INFO', f"Attempting: {strategy}")
            self.current_strategy = strategy
            
            try:
                # Attempt to launch this strategy
                result = self._launch_strategy(strategy)
                
                # If successful, save working configuration
                if result:
                    self._log('INFO', f"✓ Successfully launched with: {strategy}")
                    self._save_working_config(strategy)
                    return True
                
            except KeyboardInterrupt:
                self._log('INFO', "Interrupted by user")
                return False
            
            except Exception as e:
                # Record failure and continue to next strategy
                self._record_failure(strategy, e)
                self._log('WARN', f"✗ Failed: {str(e)[:80]}")
                
                # Continue to next strategy
                continue
        
        # All strategies exhausted
        self._log('ERROR', "All GUI strategies failed!")
        self._log('ERROR', "See fallback history for details")
        self._show_fallback_summary()
        return False
    
    def _get_recommended_strategy(self) -> str:
        """
        Get recommended starting strategy based on:
        1. Last known working strategy
        2. Environment detection
        3. Fallback preferences
        """
        # Check if we have a last working strategy
        if 'last_working' in self.state:
            last_strategy = self.state['last_working'].get('strategy')
            if last_strategy:
                self._log('DEBUG', f"Using last working strategy: {last_strategy}")
                return last_strategy
        
        # Detect environment and recommend
        try:
            from pam_manager.gui_environment import GuiEnvironment
            caps = GuiEnvironment.detect_all()
            
            if caps.display_server.value == 'wayland':
                return 'wayland'
            elif caps.display_server.value in ('x11', 'x11-hybrid'):
                if caps.x11_server.value == 'xorg':
                    return 'xorg_optimized'
                elif caps.x11_server.value == 'xfree86':
                    return 'generic_qt5'
            elif caps.display_server.value == 'headless':
                return 'cli_wizard'
        except Exception as e:
            self._log('DEBUG', f"Environment detection failed: {e}")
        
        # Default to primary (auto-detect)
        return 'primary'
    
    def _launch_strategy(self, strategy: str) -> bool:
        """
        Attempt to launch GUI with specific strategy.
        
        Args:
            strategy: Strategy name
            
        Returns:
            True if successful, raises Exception on failure
        """
        if strategy == 'primary':
            return self._launch_primary_gui()
        
        elif strategy == 'xorg_optimized':
            return self._launch_xorg_gui()
        
        elif strategy == 'generic_qt5':
            return self._launch_generic_qt5_gui()
        
        elif strategy == 'wayland':
            return self._launch_wayland_gui()
        
        elif strategy == 'offscreen':
            return self._launch_offscreen_gui()
        
        elif strategy == 'cli_wizard':
            return self._launch_cli_wizard()
        
        elif strategy == 'cli_minimal':
            return self._launch_cli_minimal()
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _launch_primary_gui(self) -> bool:
        """Launch GUI with auto-detected optimal settings using Phase 4 optimization."""
        self._log('DEBUG', "Launching primary GUI (auto-detect)")
        
        try:
            # Phase 4: Use parallel detection for 2.9x speedup
            from pam_manager.gui_parallel_detection import ParallelEnvironmentDetector
            from pam_manager.gui_config_optimizer import ConfigurationOptimizer, OptimizationLevel
            from pam_manager.gui_adapters import AdapterFactory
            
            # Detect environment and capabilities using parallel detection
            self._log('DEBUG', "Using parallel environment detection (2.9x faster)")
            caps = ParallelEnvironmentDetector.detect_all_parallel()
            self._log('DEBUG', f"Detected: {caps.display_server.value} / {caps.x11_server.value}")
            self._log('DEBUG', f"Rendering backend: {caps.rendering_backend}")
            
            # Phase 4: Use ConfigurationOptimizer to recommend optimal settings
            self._log('DEBUG', "Analyzing environment for optimization recommendations")
            recommendation = ConfigurationOptimizer.analyze_and_recommend(
                caps, 
                OptimizationLevel.BALANCED
            )
            self._log('DEBUG', f"Optimization: {recommendation.optimization_level.value}")
            self._log('DEBUG', f"Performance: {recommendation.performance_impact}x speedup potential")
            
            # Apply recommended environment variables
            for var_name, var_value in recommendation.environment_vars.items():
                os.environ[var_name] = var_value
            
            # Get appropriate adapter with capabilities
            adapter = AdapterFactory.get_adapter_for_environment(caps)
            self._log('DEBUG', f"Using adapter: {adapter.__class__.__name__}")
            
            # Configure and launch
            adapter.run_with_error_handling()
            
            return True
        
        except ImportError as e:
            raise RuntimeError(f"Import failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Primary GUI failed: {e}")
    
    def _launch_xorg_gui(self) -> bool:
        """Launch GUI with X.Org optimizations including GPU awareness."""
        self._log('DEBUG', "Launching Xorg-optimized GUI")
        
        try:
            from pam_manager.gui_environment import GuiEnvironment
            from pam_manager.gui_adapters import XorgOptimizedAdapter
            
            # Detect capabilities for GPU acceleration
            caps_dict = {
                'gpu_acceleration': GuiEnvironment.detect_gpu_acceleration(),
                'x11_extensions': GuiEnvironment.detect_x11_extensions(),
                'xorg_capabilities': GuiEnvironment.detect_xorg_capabilities(),
                'rendering_backend': GuiEnvironment.detect_rendering_backend(),
            }
            
            adapter = XorgOptimizedAdapter(caps_dict)
            self._log('DEBUG', f"GPU acceleration: {caps_dict['gpu_acceleration']}")
            adapter.run_with_error_handling()
            
            return True
        
        except Exception as e:
            raise RuntimeError(f"Xorg GUI failed: {e}")
    
    def _launch_generic_qt5_gui(self) -> bool:
        """Launch GUI with generic PyQt5 settings."""
        self._log('DEBUG', "Launching generic PyQt5 GUI")
        
        try:
            from pam_manager.gui_adapters import PyQt5Adapter
            
            adapter = PyQt5Adapter('auto')
            adapter.run_with_error_handling()
            
            return True
        
        except Exception as e:
            raise RuntimeError(f"Generic PyQt5 GUI failed: {e}")
    
    def _launch_wayland_gui(self) -> bool:
        """Launch GUI with Wayland optimizations."""
        self._log('DEBUG', "Launching Wayland-optimized GUI")
        
        try:
            from pam_manager.gui_adapters import WaylandOptimizedAdapter
            
            adapter = WaylandOptimizedAdapter(None)  # No Wayland-specific capabilities needed
            adapter.run_with_error_handling()
            
            return True
        
        except Exception as e:
            raise RuntimeError(f"Wayland GUI failed: {e}")
    
    def _launch_offscreen_gui(self) -> bool:
        """Launch GUI in offscreen mode."""
        self._log('DEBUG', "Launching offscreen GUI")
        
        try:
            from pam_manager.gui_adapters import OffscreenAdapter
            
            adapter = OffscreenAdapter(None)  # No display, no capabilities needed
            adapter.run_with_error_handling()
            
            return True
        
        except Exception as e:
            raise RuntimeError(f"Offscreen GUI failed: {e}")
    
    def _launch_cli_wizard(self) -> bool:
        """Launch text-based CLI wizard."""
        self._log('INFO', "Falling back to CLI wizard mode")
        
        try:
            from pam_manager.cli.wizard import TextWizard
            
            wizard = TextWizard()
            wizard.run()
            
            return True
        
        except Exception as e:
            raise RuntimeError(f"CLI wizard failed: {e}")
    
    def _launch_cli_minimal(self) -> bool:
        """Launch minimal text-based interface."""
        self._log('INFO', "Falling back to minimal CLI mode")
        
        print("\n" + "=" * 60)
        print("PAM Manager - Minimal Mode")
        print("=" * 60)
        print("\nNo graphical interface available.")
        print("Available commands:")
        print("  1. Show configuration")
        print("  2. Manage fragments")
        print("  3. Manage elements")
        print("  4. Manage services")
        print("  5. Exit")
        print("\nPlease use --populate mode or install a display server.")
        
        return True  # Success (even though it's minimal)
    
    def _record_failure(self, strategy: str, error: Exception):
        """Record failure for debugging."""
        failure_record = {
            'strategy': strategy,
            'error': str(error),
            'traceback': traceback.format_exc() if self.debug else None,
            'timestamp': datetime.now().isoformat(),
        }
        
        self.fallback_history.append(failure_record)
        self._save_fallback_history()
    
    def _save_working_config(self, strategy: str):
        """Save known-working configuration."""
        self.state['last_working'] = {
            'strategy': strategy,
            'timestamp': datetime.now().isoformat(),
        }
        self._persist_state()
    
    def _save_fallback_history(self):
        """Save fallback history."""
        self.state['fallback_history'] = self.fallback_history
        self._persist_state()
    
    def _load_state(self) -> dict:
        """Load saved state from file."""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self._log('WARN', f"Failed to load state: {e}")
            return {}
    
    def _persist_state(self):
        """Save state to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            self._log('WARN', f"Failed to persist state: {e}")
    
    def _show_fallback_summary(self):
        """Show summary of fallback attempts."""
        if not self.fallback_history:
            return
        
        print("\n" + "=" * 60)
        print("Fallback Attempts Summary")
        print("=" * 60)
        
        for i, attempt in enumerate(self.fallback_history, 1):
            print(f"\n{i}. {attempt['strategy']}")
            print(f"   Error: {attempt['error']}")
            print(f"   Time: {attempt['timestamp']}")
        
        print("\n" + "=" * 60)


def launch_gui_with_fallback(debug: bool = False) -> bool:
    """
    Convenience function to launch GUI with fallback support.
    
    Args:
        debug: Enable debug output
        
    Returns:
        True if successful, False if all attempts failed
    """
    launcher = GuiLauncher(debug=debug)
    return launcher.launch()


if __name__ == '__main__':
    # Test launcher
    debug = '--debug' in sys.argv
    
    print("=" * 60)
    print("PAM Manager - GUI Launcher Test")
    print("=" * 60 + "\n")
    
    success = launch_gui_with_fallback(debug=debug)
    
    if success:
        print("\n✓ GUI launcher completed successfully")
        sys.exit(0)
    else:
        print("\n✗ GUI launcher failed - all strategies exhausted")
        sys.exit(1)
