"""
GUI Environment Detection Module
Provides comprehensive environment detection for multi-platform GUI support.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional, Literal, Any
from enum import Enum


class DisplayServer(Enum):
    """Display server types."""
    WAYLAND = "wayland"
    X11 = "x11"
    X11_HYBRID = "x11-hybrid"
    HEADLESS = "headless"
    UNKNOWN = "unknown"


class X11Server(Enum):
    """X11 server variants."""
    XORG = "xorg"
    XFREE86 = "xfree86"
    XVFB = "xvfb"
    XEPHYR = "xephyr"
    XLIBRE = "xlibre"  # XlibRE - alternative X11 implementation
    UNKNOWN = "unknown"


@dataclass
class GuiCapabilities:
    """Detected GUI capabilities."""
    display_server: DisplayServer
    x11_server: X11Server
    qt_version: int  # 5 or 6
    has_window_manager: bool
    supports_remote_x11: bool
    supports_wayland_native: bool
    supports_opengl: bool
    supports_vulkan: bool
    recommended_backend: str  # 'wayland', 'xcb', 'offscreen'
    recommended_style: str  # 'Fusion', 'Adwaita', etc.
    warnings: list  # List of detected issues
    
    # Phase 2 additions
    gpu_acceleration: Dict[str, bool] = None  # GPU capabilities
    x11_extensions: Dict[str, bool] = None  # X11 extension support
    xorg_capabilities: Dict[str, Any] = None  # Xorg-specific info
    rendering_backend: str = 'software'  # 'gpu' or 'software'
    
    def __post_init__(self):
        """Initialize optional fields with defaults."""
        if self.gpu_acceleration is None:
            self.gpu_acceleration = {}
        if self.x11_extensions is None:
            self.x11_extensions = {}
        if self.xorg_capabilities is None:
            self.xorg_capabilities = {}
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'display_server': self.display_server.value,
            'x11_server': self.x11_server.value,
            'qt_version': self.qt_version,
            'has_window_manager': self.has_window_manager,
            'supports_remote_x11': self.supports_remote_x11,
            'supports_wayland_native': self.supports_wayland_native,
            'supports_opengl': self.supports_opengl,
            'supports_vulkan': self.supports_vulkan,
            'recommended_backend': self.recommended_backend,
            'recommended_style': self.recommended_style,
            'warnings': self.warnings,
            'gpu_acceleration': self.gpu_acceleration,
            'x11_extensions': self.x11_extensions,
            'xorg_capabilities': self.xorg_capabilities,
            'rendering_backend': self.rendering_backend,
        }


class GuiEnvironment:
    """
    Comprehensive environment detection for GUI initialization.
    Detects display server, X11 variants, Qt availability, and capabilities.
    """
    
    DEBUG = os.environ.get('PAM_DEBUG_GUI', '').lower() in ('1', 'true', 'yes')
    
    @staticmethod
    def _log_debug(msg: str):
        """Log debug message if debug mode enabled."""
        if GuiEnvironment.DEBUG:
            print(f"[DEBUG-GUI] {msg}")
    
    @staticmethod
    def detect_display_server() -> DisplayServer:
        """
        Detect the active display server.
        
        Returns:
            DisplayServer enum value indicating detected display server.
        """
        GuiEnvironment._log_debug("Detecting display server...")
        
        # Collect all display-related environment variables
        xdg_session = os.environ.get('XDG_SESSION_TYPE', '').lower()
        wayland_display = os.environ.get('WAYLAND_DISPLAY', '')
        x11_display = os.environ.get('DISPLAY', '')
        
        # Determine if X11 display is in valid format
        is_valid_x11_display = False
        if x11_display:
            is_valid_x11_display = (
                x11_display.startswith(':') or                  # :0, :1, etc.
                x11_display.startswith('localhost:') or         # localhost:0
                ('.' not in x11_display and ':' in x11_display) # host:0 (simple hostname)
            )
        
        # Decision logic based on combinations
        
        # Wayland session (explicit XDG_SESSION_TYPE=wayland)
        if xdg_session == 'wayland':
            if is_valid_x11_display:
                # Wayland session with X11 display too (hybrid setup)
                GuiEnvironment._log_debug(f"  → XDG_SESSION_TYPE=wayland + DISPLAY={x11_display} (hybrid)")
                return DisplayServer.X11_HYBRID
            elif wayland_display:
                # Wayland session with native Wayland display
                GuiEnvironment._log_debug(f"  → XDG_SESSION_TYPE=wayland + WAYLAND_DISPLAY={wayland_display}")
                return DisplayServer.WAYLAND
            else:
                # Wayland session without explicit display yet
                GuiEnvironment._log_debug(f"  → XDG_SESSION_TYPE=wayland (no explicit display)")
                return DisplayServer.WAYLAND
        
        # X11 session (explicit XDG_SESSION_TYPE=x11)
        elif xdg_session == 'x11':
            # XDG_SESSION_TYPE=x11 is explicit, trust it even without DISPLAY
            GuiEnvironment._log_debug(f"  → XDG_SESSION_TYPE=x11")
            return DisplayServer.X11
        
        # No explicit XDG_SESSION_TYPE, fallback to display socket checks
        
        # Wayland display socket available
        if wayland_display:
            GuiEnvironment._log_debug(f"  → WAYLAND_DISPLAY={wayland_display}")
            return DisplayServer.WAYLAND
        
        # X11 display available
        if is_valid_x11_display:
            GuiEnvironment._log_debug(f"  → DISPLAY={x11_display}")
            return DisplayServer.X11
        elif x11_display:
            # Invalid X11 DISPLAY format
            GuiEnvironment._log_debug(f"  → DISPLAY={x11_display} (invalid X11 format)")
        
        # No display detected
        GuiEnvironment._log_debug("  → No display detected (headless)")
        return DisplayServer.HEADLESS
    
    @staticmethod
    def detect_x11_server() -> X11Server:
        """
        Detect X11 server type and variant.
        
        Returns:
            X11Server enum value or X11Server.UNKNOWN if not applicable.
        """
        GuiEnvironment._log_debug("Detecting X11 server...")
        
        # Try standard X11 version check
        try:
            result = subprocess.run(
                ['Xorg', '-version'],
                capture_output=True,
                text=True,
                timeout=2
            )
            output = result.stderr + result.stdout
            GuiEnvironment._log_debug(f"  → Xorg detected: {output.split(chr(10))[0]}")
            
            if 'XFree86' in output:
                return X11Server.XFREE86
            else:
                return X11Server.XORG
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try XlibRE detection
        try:
            result = subprocess.run(
                ['XlibRE', '-version'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                GuiEnvironment._log_debug(f"  → XlibRE detected")
                return X11Server.XLIBRE
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try legacy X command
        try:
            result = subprocess.run(
                ['X', '-version'],
                capture_output=True,
                text=True,
                timeout=2
            )
            output = result.stderr + result.stdout
            GuiEnvironment._log_debug(f"  → X detected: {output.split(chr(10))[0]}")
            
            if 'XFree86' in output:
                return X11Server.XFREE86
            elif 'XlibRE' in output or 'xlibre' in output.lower():
                return X11Server.XLIBRE
            else:
                return X11Server.XORG
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Check /proc for X process info
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if 'Xorg' in result.stdout:
                GuiEnvironment._log_debug("  → Xorg detected via ps")
                return X11Server.XORG
            elif 'XlibRE' in result.stdout or 'xlibre' in result.stdout.lower():
                GuiEnvironment._log_debug("  → XlibRE detected via ps")
                return X11Server.XLIBRE
            elif 'Xvfb' in result.stdout:
                GuiEnvironment._log_debug("  → Xvfb detected via ps")
                return X11Server.XVFB
        except subprocess.TimeoutExpired:
            pass
        
        GuiEnvironment._log_debug("  → X11 server type unknown")
        return X11Server.UNKNOWN
    
    @staticmethod
    def detect_qt_version() -> int:
        """
        Detect available Qt version (5 or 6).
        Prefers higher version if both available.
        
        Returns:
            5 or 6 (default 5 if neither available)
        """
        GuiEnvironment._log_debug("Detecting Qt version...")
        
        # Try PyQt6 first
        try:
            import PyQt6
            GuiEnvironment._log_debug("  → PyQt6 available")
            return 6
        except ImportError:
            pass
        
        # Try PyQt5
        try:
            import PyQt5
            GuiEnvironment._log_debug("  → PyQt5 available")
            return 5
        except ImportError:
            pass
        
        # Default to 5 (current app requirement)
        GuiEnvironment._log_debug("  → Qt version not detected, assuming 5")
        return 5
    
    @staticmethod
    def detect_opengl_support() -> bool:
        """Detect if OpenGL support is available."""
        try:
            result = subprocess.run(
                ['glxinfo'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                GuiEnvironment._log_debug("  → OpenGL (GLX) available")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        GuiEnvironment._log_debug("  → OpenGL not available")
        return False
    
    @staticmethod
    def detect_window_manager() -> bool:
        """Detect if window manager is running."""
        # Check for common window managers
        window_managers = [
            'GNOME', 'KDE', 'XFCE', 'i3', 'sway', 'openbox',
            'dwm', 'fluxbox', 'windowmaker'
        ]
        
        # Check XDG_CURRENT_DESKTOP
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        if any(wm.lower() in desktop for wm in window_managers):
            GuiEnvironment._log_debug(f"  → Window manager detected: {desktop}")
            return True
        
        # Check DESKTOP_SESSION
        session = os.environ.get('DESKTOP_SESSION', '').lower()
        if any(wm.lower() in session for wm in window_managers):
            GuiEnvironment._log_debug(f"  → Window manager detected: {session}")
            return True
        
        # Try to check for running WM process
        try:
            result = subprocess.run(
                ['wmctrl', '-l'],
                capture_output=True,
                timeout=1
            )
            if result.returncode == 0:
                GuiEnvironment._log_debug("  → Window manager detected (wmctrl)")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        GuiEnvironment._log_debug("  → Window manager not detected")
        return False
    
    @staticmethod
    def detect_remote_x11() -> bool:
        """Detect if using remote X11 (SSH -X)."""
        # Remote X11 typically has DISPLAY like localhost:10.0 or similar
        display = os.environ.get('DISPLAY', '')
        
        if display.startswith('localhost:') or \
           display.startswith('127.0.0.1:') or \
           (':' in display and not display.startswith(':')):
            GuiEnvironment._log_debug(f"  → Remote X11 detected: {display}")
            return True
        
        GuiEnvironment._log_debug("  → Local X11 connection")
        return False
    
    @staticmethod
    def detect_gpu_acceleration() -> Dict[str, bool]:
        """
        Detect GPU acceleration capabilities.
        
        Returns:
            Dictionary with GPU capability flags:
            - 'glx': GLX support (OpenGL for X11)
            - 'egl': EGL support (modern OpenGL)
            - 'vulkan': Vulkan support
            - 'nvidia': NVIDIA GPU detected
            - 'amd': AMD GPU detected
            - 'intel': Intel GPU detected
        """
        GuiEnvironment._log_debug("Detecting GPU acceleration...")
        
        capabilities = {
            'glx': False,
            'egl': False,
            'vulkan': False,
            'nvidia': False,
            'amd': False,
            'intel': False,
        }
        
        # Check for GLX (X11 OpenGL)
        try:
            result = subprocess.run(
                ['glxinfo'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                capabilities['glx'] = True
                # Check GPU vendor
                if 'NVIDIA' in result.stdout:
                    capabilities['nvidia'] = True
                    GuiEnvironment._log_debug("  → NVIDIA GPU (GLX)")
                elif 'AMD' in result.stdout or 'ATI' in result.stdout:
                    capabilities['amd'] = True
                    GuiEnvironment._log_debug("  → AMD GPU (GLX)")
                elif 'Intel' in result.stdout:
                    capabilities['intel'] = True
                    GuiEnvironment._log_debug("  → Intel GPU (GLX)")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Check for EGL
        try:
            result = subprocess.run(
                ['eglinfo'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                capabilities['egl'] = True
                GuiEnvironment._log_debug("  → EGL available")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Check for Vulkan
        try:
            result = subprocess.run(
                ['vulkaninfo'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                capabilities['vulkan'] = True
                GuiEnvironment._log_debug("  → Vulkan available")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Check lspci for GPU
        try:
            result = subprocess.run(
                ['lspci'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                output_lower = result.stdout.lower()
                if 'nvidia' in output_lower:
                    capabilities['nvidia'] = True
                if 'amd' in output_lower or 'ati' in output_lower:
                    capabilities['amd'] = True
                if 'intel' in output_lower and 'graphics' in output_lower:
                    capabilities['intel'] = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return capabilities
    
    @staticmethod
    def detect_x11_extensions() -> Dict[str, bool]:
        """
        Detect X11 server extensions and features.
        
        Returns:
            Dictionary with extension availability:
            - 'render': RENDER extension
            - 'xfixes': XFixes extension
            - 'composite': Composite extension
            - 'randr': RandR extension (multi-monitor)
            - 'xinerama': Xinerama extension
        """
        GuiEnvironment._log_debug("Detecting X11 extensions...")
        
        extensions = {
            'render': False,
            'xfixes': False,
            'composite': False,
            'randr': False,
            'xinerama': False,
        }
        
        # Try xdpyinfo for extension list
        try:
            result = subprocess.run(
                ['xdpyinfo'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                output = result.stdout.lower()
                if 'render' in output:
                    extensions['render'] = True
                    GuiEnvironment._log_debug("  → RENDER extension")
                if 'xfixes' in output:
                    extensions['xfixes'] = True
                    GuiEnvironment._log_debug("  → XFixes extension")
                if 'composite' in output:
                    extensions['composite'] = True
                    GuiEnvironment._log_debug("  → Composite extension")
                if 'randr' in output:
                    extensions['randr'] = True
                    GuiEnvironment._log_debug("  → RandR extension")
                if 'xinerama' in output:
                    extensions['xinerama'] = True
                    GuiEnvironment._log_debug("  → Xinerama extension")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return extensions
    
    @staticmethod
    def detect_xorg_capabilities() -> Dict[str, Any]:
        """
        Detect Xorg-specific capabilities and version.
        
        Returns:
            Dictionary with Xorg details:
            - 'version': Version string
            - 'supports_render': RENDER extension
            - 'supports_composite': Composite extension
            - 'supports_randr': RandR multi-monitor
            - 'default_depth': Color depth (bits)
        """
        GuiEnvironment._log_debug("Detecting Xorg capabilities...")
        
        capabilities = {
            'version': 'unknown',
            'supports_render': False,
            'supports_composite': False,
            'supports_randr': False,
            'default_depth': 24,
        }
        
        # Get Xorg version
        try:
            result = subprocess.run(
                ['Xorg', '-version'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                output = result.stderr + result.stdout
                # Extract version info
                lines = output.split('\n')
                if lines:
                    capabilities['version'] = lines[0].strip()
                    GuiEnvironment._log_debug(f"  → {capabilities['version']}")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Get X11 extensions
        extensions = GuiEnvironment.detect_x11_extensions()
        capabilities['supports_render'] = extensions['render']
        capabilities['supports_composite'] = extensions['composite']
        capabilities['supports_randr'] = extensions['randr']
        
        # Get default color depth
        try:
            result = subprocess.run(
                ['xdpyinfo'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'depths supported' in line.lower():
                        # Extract depth info
                        try:
                            # Usually looks like "depths (7):  24, 32, ..."
                            depth_part = line.split(':')[-1].strip()
                            depths = [int(d.strip().rstrip(',')) for d in depth_part.split(',') if d.strip()]
                            if depths:
                                capabilities['default_depth'] = depths[0]
                                GuiEnvironment._log_debug(f"  → Depth: {capabilities['default_depth']} bits")
                        except:
                            pass
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return capabilities
    
    @staticmethod
    def detect_rendering_backend() -> str:
        """
        Determine optimal rendering backend based on capabilities.
        
        Returns:
            'gpu' (GPU-accelerated) or 'software' (software rendering)
        """
        GuiEnvironment._log_debug("Determining rendering backend...")
        
        # Check for GPU support
        gpu_caps = GuiEnvironment.detect_gpu_acceleration()
        
        # If GLX or EGL available, use GPU acceleration
        if gpu_caps['glx'] or gpu_caps['egl']:
            GuiEnvironment._log_debug("  → GPU rendering available")
            return 'gpu'
        
        # Fallback to software rendering
        GuiEnvironment._log_debug("  → Using software rendering")
        return 'software'
    
    @staticmethod
    def get_recommended_backend(caps: 'GuiCapabilities' = None) -> str:
        """
        Determine recommended Qt backend.
        
        Returns:
            'wayland', 'xcb', 'offscreen'
        """
        if caps is None:
            return 'auto'
        if caps.display_server == DisplayServer.WAYLAND:
            return 'wayland'
        elif caps.display_server in (DisplayServer.X11, DisplayServer.X11_HYBRID):
            return 'xcb'
        else:
            return 'offscreen'
    
    @staticmethod
    def get_recommended_style(caps: 'GuiCapabilities' = None) -> str:
        """
        Determine recommended Qt style.
        
        Returns:
            Style name string
        """
        if caps is None:
            return 'Fusion'
        # Wayland-native styles
        if caps.display_server == DisplayServer.WAYLAND:
            return 'Adwaita'  # GNOME-like style for Wayland
        
        # X11 styles
        if caps.x11_server == X11Server.XORG:
            return 'Fusion'  # Most compatible for Xorg
        
        # X11 variants
        if caps.x11_server == X11Server.XFREE86:
            return 'Plastique'  # Legacy style for XFree86
        
        # Virtual displays
        if caps.x11_server == X11Server.XVFB:
            return 'Fusion'  # No GPU acceleration, use software rendering
        
        # Default fallback
        return 'Fusion'
    
    @staticmethod
    def detect_all() -> GuiCapabilities:
        """
        Perform complete environment detection.
        
        Returns:
            GuiCapabilities object with all detected information.
        """
        GuiEnvironment._log_debug("=== Starting complete GUI environment detection ===")
        
        # Detect all components
        display_server = GuiEnvironment.detect_display_server()
        x11_server = GuiEnvironment.detect_x11_server() if display_server != DisplayServer.WAYLAND else X11Server.UNKNOWN
        qt_version = GuiEnvironment.detect_qt_version()
        has_wm = GuiEnvironment.detect_window_manager()
        remote_x11 = GuiEnvironment.detect_remote_x11()
        opengl = GuiEnvironment.detect_opengl_support()
        
        # Phase 2: Extended detection
        gpu_caps = GuiEnvironment.detect_gpu_acceleration()
        x11_ext = GuiEnvironment.detect_x11_extensions()
        xorg_caps = GuiEnvironment.detect_xorg_capabilities() if display_server in (DisplayServer.X11, DisplayServer.X11_HYBRID) else {}
        rendering = GuiEnvironment.detect_rendering_backend()
        
        # Build capabilities object
        caps = GuiCapabilities(
            display_server=display_server,
            x11_server=x11_server,
            qt_version=qt_version,
            has_window_manager=has_wm,
            supports_remote_x11=remote_x11,
            supports_wayland_native=(display_server == DisplayServer.WAYLAND),
            supports_opengl=opengl,
            supports_vulkan=gpu_caps.get('vulkan', False),
            recommended_backend=GuiEnvironment.get_recommended_backend(None),  # Will fix
            recommended_style=GuiEnvironment.get_recommended_style(None),  # Will fix
            warnings=[],
            gpu_acceleration=gpu_caps,
            x11_extensions=x11_ext,
            xorg_capabilities=xorg_caps,
            rendering_backend=rendering,
        )
        
        # Fix backend and style recommendations
        caps.recommended_backend = GuiEnvironment.get_recommended_backend(caps)
        caps.recommended_style = GuiEnvironment.get_recommended_style(caps)
        
        # Add warnings for problematic configurations
        if display_server == DisplayServer.HEADLESS:
            caps.warnings.append("No display server detected - GUI will not work")
        
        if remote_x11 and not opengl:
            caps.warnings.append("Remote X11 without OpenGL may have performance issues")
        
        if not has_wm:
            caps.warnings.append("No window manager detected - window management may be limited")
        
        # Phase 2 warnings
        if rendering == 'software' and remote_x11:
            caps.warnings.append("Software rendering over remote X11 will be slow")
        
        if x11_server in (X11Server.XFREE86, X11Server.XVFB):
            caps.warnings.append(f"Legacy X11 server detected ({x11_server.value}) - performance may be limited")
        
        GuiEnvironment._log_debug(f"=== Detection complete ===")
        GuiEnvironment._log_debug(f"Summary: {caps.display_server.value} + "
                                  f"Qt{caps.qt_version} + "
                                  f"{caps.recommended_style} + "
                                  f"{caps.rendering_backend} rendering")
        
        return caps
    
    @staticmethod
    def save_to_cache(caps: GuiCapabilities, cache_file: Optional[str] = None):
        """Cache detected capabilities to file."""
        if cache_file is None:
            cache_file = str(Path.home() / '.cache' / 'pam-gui-capabilities.json')
        
        Path(cache_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(cache_file, 'w') as f:
            json.dump(caps.to_dict(), f, indent=2)
        
        GuiEnvironment._log_debug(f"Saved capabilities to {cache_file}")
    
    @staticmethod
    def load_from_cache(cache_file: Optional[str] = None) -> Optional[GuiCapabilities]:
        """Load cached capabilities (max 24h old)."""
        if cache_file is None:
            cache_file = str(Path.home() / '.cache' / 'pam-gui-capabilities.json')
        
        cache_path = Path(cache_file)
        if not cache_path.exists():
            return None
        
        # Check cache age (24h max)
        import time
        age = time.time() - cache_path.stat().st_mtime
        if age > 86400:  # 24 hours
            GuiEnvironment._log_debug(f"Cache expired ({age/3600:.1f}h old)")
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            GuiEnvironment._log_debug(f"Loaded cached capabilities from {cache_file}")
            
            # Convert back to enums
            return GuiCapabilities(
                display_server=DisplayServer(data['display_server']),
                x11_server=X11Server(data['x11_server']),
                qt_version=data['qt_version'],
                has_window_manager=data['has_window_manager'],
                supports_remote_x11=data['supports_remote_x11'],
                supports_wayland_native=data['supports_wayland_native'],
                supports_opengl=data['supports_opengl'],
                supports_vulkan=data['supports_vulkan'],
                recommended_backend=data['recommended_backend'],
                recommended_style=data['recommended_style'],
                warnings=data['warnings'],
            )
        except Exception as e:
            GuiEnvironment._log_debug(f"Failed to load cache: {e}")
            return None


if __name__ == '__main__':
    # Test environment detection
    os.environ['PAM_DEBUG_GUI'] = '1'
    
    print("=" * 60)
    print("PAM Manager - GUI Environment Detection")
    print("=" * 60)
    
    caps = GuiEnvironment.detect_all()
    
    print("\nDetection Results:")
    print(f"  Display Server: {caps.display_server.value}")
    print(f"  X11 Server: {caps.x11_server.value}")
    print(f"  Qt Version: {caps.qt_version}")
    print(f"  Window Manager: {caps.has_window_manager}")
    print(f"  Remote X11: {caps.supports_remote_x11}")
    print(f"  OpenGL: {caps.supports_opengl}")
    print(f"  Recommended Backend: {caps.recommended_backend}")
    print(f"  Recommended Style: {caps.recommended_style}")
    
    if caps.warnings:
        print("\nWarnings:")
        for warning in caps.warnings:
            print(f"  ⚠ {warning}")
    else:
        print("\nNo warnings detected.")
    
    # Save to cache
    GuiEnvironment.save_to_cache(caps)
    print("\nCapabilities saved to cache.")
