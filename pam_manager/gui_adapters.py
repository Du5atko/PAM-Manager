"""
GUI Adapter Layer - Abstracts PyQt5 with fallback support.
Provides abstraction for multi-backend GUI support with platform-specific optimizations.
"""

import os
import sys
import time
from abc import ABC, abstractmethod
from typing import Type, Optional, Dict, Any, Tuple


class QtGuiAdapter(ABC):
    """
    Abstract base class for Qt GUI implementations.
    Allows swapping between different Qt backends or versions.
    """
    
    def __init__(self, display_server: str = 'auto'):
        """
        Initialize GUI adapter.
        
        Args:
            display_server: 'wayland', 'xcb', 'x11', 'offscreen', or 'auto'
        """
        self.display_server = display_server
        self.app = None
        self.configured = False
    
    @abstractmethod
    def configure_platform(self):
        """Configure platform-specific settings before creating QApplication."""
        pass
    
    @abstractmethod
    def create_application(self, argv: list):
        """
        Create and return QApplication instance.
        
        Args:
            argv: Command-line arguments
            
        Returns:
            QApplication instance
        """
        pass
    
    @abstractmethod
    def get_main_window_class(self):
        """
        Get the main window class to instantiate.
        
        Returns:
            QMainWindow subclass
        """
        pass
    
    @abstractmethod
    def get_style_name(self) -> str:
        """
        Get recommended Qt style for this platform.
        
        Returns:
            Style name (e.g., 'Fusion', 'Adwaita')
        """
        pass
    
    def run_event_loop(self, window):
        """
        Run the Qt event loop.
        
        Args:
            window: Main window instance
        """
        if self.app:
            window.show()
            sys.exit(self.app.exec_())
    
    def run_with_error_handling(self):
        """
        Run application with built-in error handling.
        Configures platform, creates QApplication, creates and shows main window, runs event loop.
        
        Raises:
            RuntimeError: If GUI initialization fails
        """
        try:
            # Step 1: Configure platform
            self.configure_platform()
            self.configured = True
            
            # Step 2: Create QApplication
            self.app = self.create_application(sys.argv)
            
            # Step 3: Set style
            self.app.setStyle(self.get_style_name())
            
            # Step 4: Create main window
            window_class = self.get_main_window_class()
            window = window_class()
            
            # Step 5: Run event loop (this will block until window closes)
            self.run_event_loop(window)
            
        except Exception as e:
            raise RuntimeError(f"GUI initialization failed: {e}")


class PyQt5Adapter(QtGuiAdapter):
    """
    PyQt5-based GUI adapter.
    Works with both Wayland and X11.
    """
    
    def __init__(self, display_server: str = 'auto'):
        super().__init__(display_server)
        self._qt_app = None
    
    def configure_platform(self):
        """Configure PyQt5 for the detected platform."""
        if self.display_server == 'wayland':
            # Wayland-specific settings
            os.environ['QT_QPA_PLATFORM'] = 'wayland'
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''
        elif self.display_server in ('xcb', 'x11'):
            # X11-specific settings
            os.environ['QT_QPA_PLATFORM'] = 'xcb'
            os.environ['QT_XCB_GL_INTEGRATION'] = 'none'
        elif self.display_server == 'auto':
            # Auto-detect and configure
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''
        elif self.display_server == 'offscreen':
            # Headless/offscreen rendering
            os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        
        # Common settings
        os.environ['QT_DEBUG_PLUGINS'] = '0'
        os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    
    def create_application(self, argv: list):
        """Create PyQt5 QApplication."""
        try:
            from PyQt5.QtWidgets import QApplication
            self._qt_app = QApplication(argv)
            return self._qt_app
        except ImportError as e:
            raise RuntimeError(f"PyQt5 not available: {e}")
    
    def get_main_window_class(self):
        """Get PAMManagerGUI class."""
        # Import here to avoid circular dependencies
        from PAMManager import PAMManagerGUI
        return PAMManagerGUI
    
    def get_style_name(self) -> str:
        """PyQt5 recommends Fusion style for compatibility."""
        return 'Fusion'
    
    @property
    def app(self):
        """Get current QApplication instance."""
        return self._qt_app
    
    @app.setter
    def app(self, value):
        """Set QApplication instance."""
        self._qt_app = value


class XorgOptimizedAdapter(PyQt5Adapter):
    """
    X.Org-optimized PyQt5 adapter.
    Provides specific optimizations for X.Org display server.
    Supports GPU acceleration when available, falls back to software rendering.
    """
    
    def __init__(self, capabilities: Optional[Dict] = None):
        super().__init__(display_server='xcb')
        self.capabilities = capabilities or {}
        self.gpu_available = self.capabilities.get('gpu_acceleration', {}).get('glx', False)
        self.supports_composite = self.capabilities.get('x11_extensions', {}).get('composite', False)
        self.rendering_backend = self.capabilities.get('rendering_backend', 'software')
    
    def configure_platform(self):
        """Configure PyQt5 specifically for Xorg with advanced features."""
        # Force XCB backend (X11 native)
        os.environ['QT_QPA_PLATFORM'] = 'xcb'
        
        # GPU acceleration handling
        if self.gpu_available:
            # Enable GPU acceleration if GLX available
            os.environ['QT_XCB_GL_INTEGRATION'] = 'xcb_glx'
            os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
            os.environ['QT_XCB_EGLFS_INTEGRATION'] = 'none'
            os.environ['QT_LOGGING_RULES'] = 'qt.qpa.gl=false'
        else:
            # Disable GPU acceleration for software rendering
            os.environ['QT_XCB_GL_INTEGRATION'] = 'none'
            os.environ['QT_XCB_SOFTWARE_RENDER'] = '1'
            os.environ['QT_LOGGING_RULES'] = '*=false'
        
        # DPI scaling
        os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
        os.environ['QT_FONT_DPI'] = '96'
        
        # Composite support
        if self.supports_composite:
            os.environ['QT_XCB_USE_NATIVE_PAINTING'] = '0'
        else:
            os.environ['QT_XCB_USE_NATIVE_PAINTING'] = '1'
    
    def get_style_name(self) -> str:
        """
        Recommend style based on Xorg capabilities.
        GPU-accelerated systems can use more complex styles.
        """
        if self.gpu_available:
            return 'Fusion'  # Modern, GPU-friendly
        else:
            return 'Fusion'  # Still best for compatibility


class XFree86OptimizedAdapter(PyQt5Adapter):
    """
    XFree86-optimized adapter.
    Provides compatibility with older XFree86 servers with very conservative settings.
    """
    
    def __init__(self, capabilities: Optional[Dict] = None):
        super().__init__(display_server='xcb')
        self.capabilities = capabilities or {}
    
    def configure_platform(self):
        """Configure for XFree86 compatibility - very conservative."""
        # XFree86 is very old, use most conservative settings possible
        os.environ['QT_QPA_PLATFORM'] = 'xcb'
        
        # Disable ALL GPU features (XFree86 is very old)
        os.environ['QT_XCB_GL_INTEGRATION'] = 'none'
        os.environ['QT_XCB_SOFTWARE_RENDER'] = '1'
        os.environ['QT_LOGGING_RULES'] = '*=false'
        
        # Minimal DPI handling
        os.environ['QT_FONT_DPI'] = '96'
        
        # Disable composite (very old systems don't support it)
        os.environ['QT_XCB_USE_NATIVE_PAINTING'] = '1'
        
        # No advanced extensions
        os.environ['QT_XCB_EGLFS_INTEGRATION'] = 'none'
        
        # Disable problematic features
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''
        os.environ['QT_DEBUG_PLUGINS'] = '0'
    
    def get_style_name(self) -> str:
        """
        Plastique style has better legacy compatibility than Fusion.
        """
        return 'Plastique'


class WaylandOptimizedAdapter(PyQt5Adapter):
    """
    Wayland-optimized adapter.
    Provides Wayland-native optimizations and capabilities handling.
    """
    
    def __init__(self, capabilities: Optional[Dict] = None):
        super().__init__(display_server='wayland')
        self.capabilities = capabilities or {}
    
    def configure_platform(self):
        """Configure specifically for Wayland."""
        os.environ['QT_QPA_PLATFORM'] = 'wayland'
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''
        
        # Wayland-specific optimizations
        os.environ['QT_QPA_PLATFORMTHEME'] = 'adwaita'
    
    def get_style_name(self) -> str:
        """Use Adwaita style for Wayland (GNOME-like)."""
        return 'Adwaita'


class OffscreenAdapter(PyQt5Adapter):
    """
    Offscreen/headless adapter.
    Used when no display is available.
    Handles headless rendering and CLI fallback.
    """
    
    def __init__(self, capabilities: Optional[Dict] = None):
        super().__init__(display_server='offscreen')
        self.capabilities = capabilities or {}
    
    def configure_platform(self):
        """Configure for headless operation."""
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        os.environ['QT_DEBUG_PLUGINS'] = '0'
    
    def get_style_name(self) -> str:
        """Use Fusion for consistency."""
        return 'Fusion'
    
    def run_event_loop(self, window):
        """Override - offscreen mode doesn't show windows."""
        if self.app:
            # Don't call window.show() - no display
            sys.exit(self.app.exec_())


class XlibreOptimizedAdapter(PyQt5Adapter):
    """
    XlibRE-optimized adapter.
    XlibRE is an alternative X11 implementation, similar to XFree86 in terms of compatibility.
    Provides conservative settings similar to XFree86 for maximum compatibility.
    """
    
    def __init__(self, capabilities: Optional[Dict] = None):
        super().__init__(display_server='xcb')
        self.capabilities = capabilities or {}
    
    def configure_platform(self):
        """Configure for XlibRE compatibility - conservative like XFree86."""
        # XlibRE is like XFree86 - use conservative settings
        os.environ['QT_QPA_PLATFORM'] = 'xcb'
        
        # Disable GPU features (XlibRE is alternative, not as modern)
        os.environ['QT_XCB_GL_INTEGRATION'] = 'none'
        os.environ['QT_XCB_SOFTWARE_RENDER'] = '1'
        
        # Minimal features
        os.environ['QT_LOGGING_RULES'] = '*=false'
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''
        os.environ['QT_FONT_DPI'] = '96'
        
        # No composite support
        os.environ['QT_XCB_USE_NATIVE_PAINTING'] = '1'
    
    def get_style_name(self) -> str:
        """Use Plastique style for XlibRE (legacy but compatible)."""
        return 'Plastique'


class AdapterFactory:
    """Factory for creating appropriate GUI adapters with capabilities."""
    
    # Map display server types to adapter classes
    ADAPTER_MAP = {
        'wayland': WaylandOptimizedAdapter,
        'xcb': XorgOptimizedAdapter,
        'xorg': XorgOptimizedAdapter,
        'xfree86': XFree86OptimizedAdapter,
        'xlibre': XlibreOptimizedAdapter,
        'offscreen': OffscreenAdapter,
        'default': PyQt5Adapter,
    }
    
    @staticmethod
    def get_adapter(backend: str, capabilities: Optional[Dict] = None) -> QtGuiAdapter:
        """
        Get appropriate adapter for backend.
        
        Args:
            backend: 'wayland', 'xcb', 'xorg', 'xfree86', 'offscreen', or 'default'
            capabilities: Optional capabilities dict from environment detection
            
        Returns:
            QtGuiAdapter instance
        """
        backend = backend.lower().strip()
        
        if backend in AdapterFactory.ADAPTER_MAP:
            adapter_class = AdapterFactory.ADAPTER_MAP[backend]
            # All adapters can now accept capabilities
            if capabilities is None:
                # No capabilities provided, use adapter defaults
                return adapter_class()
            try:
                return adapter_class(capabilities)
            except TypeError:
                # Fallback for adapters that don't accept capabilities
                return adapter_class()
        
        # Fallback to default
        return PyQt5Adapter()
    
    @staticmethod
    def get_fallback_chain(capabilities: Optional[Dict] = None) -> list:
        """
        Get recommended fallback chain of adapters with capabilities.
        
        Args:
            capabilities: Optional capabilities dict from environment detection
            
        Returns:
            List of adapter instances in fallback order
        """
        return [
            PyQt5Adapter('auto'),           # Auto-detect and use best
            XorgOptimizedAdapter(capabilities),         # X.Org optimized
            XFree86OptimizedAdapter(capabilities),      # XFree86 compatible
            XlibreOptimizedAdapter(capabilities),       # XlibRE optimized
            WaylandOptimizedAdapter(),      # Wayland optimized
            OffscreenAdapter(),             # Headless/offscreen
        ]
    
    @staticmethod
    def get_adapter_for_environment(caps) -> QtGuiAdapter:
        """
        Get best adapter for detected environment with full capabilities.
        
        Args:
            caps: GuiCapabilities object from environment detection
            
        Returns:
            Appropriate QtGuiAdapter instance with capabilities configured
        """
        from pam_manager.gui_environment import DisplayServer, X11Server
        
        # Convert capabilities to dict for passing to adapters
        caps_dict = {
            'gpu_acceleration': caps.gpu_acceleration,
            'x11_extensions': caps.x11_extensions,
            'xorg_capabilities': caps.xorg_capabilities,
            'rendering_backend': caps.rendering_backend,
        }
        
        if caps.display_server == DisplayServer.WAYLAND:
            return WaylandOptimizedAdapter()
        
        if caps.display_server in (DisplayServer.X11, DisplayServer.X11_HYBRID):
            if caps.x11_server == X11Server.XORG:
                return XorgOptimizedAdapter(caps_dict)
            elif caps.x11_server == X11Server.XFREE86:
                return XFree86OptimizedAdapter(caps_dict)
            elif caps.x11_server == X11Server.XLIBRE:
                return XlibreOptimizedAdapter(caps_dict)
        
        if caps.display_server == DisplayServer.HEADLESS:
            return OffscreenAdapter()
        
        # Default fallback
        return PyQt5Adapter('auto')


if __name__ == '__main__':
    # Test adapter creation
    print("=" * 60)
    print("PAM Manager - GUI Adapter Factory")
    print("=" * 60)
    
    print("\nAvailable Adapters:")
    for backend, adapter_class in AdapterFactory.ADAPTER_MAP.items():
        print(f"  - {backend}: {adapter_class.__name__}")
    
    print("\nGetting auto-detected adapter...")
    adapter = AdapterFactory.get_adapter('default')
    print(f"  Adapter: {adapter.__class__.__name__}")
    print(f"  Display Server: {adapter.display_server}")
    
    print("\nTesting adapter configuration...")
    try:
        adapter.configure_platform()
        print("  ✓ Configuration successful")
        print(f"  Recommended Style: {adapter.get_style_name()}")
    except Exception as e:
        print(f"  ✗ Configuration failed: {e}")
