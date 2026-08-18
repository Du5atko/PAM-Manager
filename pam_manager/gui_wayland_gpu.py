"""
Wayland GPU Detection Module
Detects GPU capabilities on Wayland display server environments.
"""

import os
import subprocess
from typing import Dict, Optional


class WaylandGPUDetector:
    """
    Detects GPU acceleration capabilities in Wayland environments.
    Uses EGL (OpenGL ES) and other Wayland-specific detection methods.
    """
    
    @staticmethod
    def detect_egl_support() -> bool:
        """
        Detect EGL (OpenGL ES) support in Wayland.
        
        Returns:
            True if EGL is available
        """
        # Check for EGL libraries
        egl_libs = [
            '/usr/lib/libEGL.so',
            '/usr/lib/libEGL.so.1',
            '/usr/lib64/libEGL.so',
            '/usr/lib64/libEGL.so.1',
            '/usr/local/lib/libEGL.so',
        ]
        
        for lib in egl_libs:
            if os.path.exists(lib):
                return True
        
        # Try eglinfo command
        try:
            result = subprocess.run(
                ['eglinfo'],
                capture_output=True,
                timeout=2,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def detect_wayland_egl_extensions() -> Dict[str, bool]:
        """
        Detect Wayland-specific EGL extensions.
        
        Returns:
            Dict with EGL extension support status
        """
        extensions = {
            'egl_wayland': False,
            'egl_khr_platform_wayland': False,
            'egl_mesa_platform_wayland': False,
            'egl_buffer_age': False,
            'egl_swap_buffers_with_damage': False,
        }
        
        try:
            result = subprocess.run(
                ['eglinfo'],
                capture_output=True,
                timeout=2,
                text=True
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                # Check for various extension names
                if 'wayland' in output or 'khr_platform_wayland' in output:
                    extensions['egl_wayland'] = True
                    extensions['egl_khr_platform_wayland'] = True
                
                if 'mesa_platform_wayland' in output:
                    extensions['egl_mesa_platform_wayland'] = True
                
                if 'buffer_age' in output:
                    extensions['egl_buffer_age'] = True
                
                if 'swap_buffers_with_damage' in output or 'khr_partial_update' in output:
                    extensions['egl_swap_buffers_with_damage'] = True
        
        except Exception:
            pass
        
        return extensions
    
    @staticmethod
    def detect_wayland_gpu_vendor() -> Optional[str]:
        """
        Detect GPU vendor in Wayland environment.
        
        Returns:
            GPU vendor name or None if not detected
        """
        # Check via weston-info (Wayland utility)
        try:
            result = subprocess.run(
                ['weston-info'],
                capture_output=True,
                timeout=2,
                text=True
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                if 'nvidia' in output:
                    return 'nvidia'
                elif 'amd' in output or 'radeon' in output:
                    return 'amd'
                elif 'intel' in output:
                    return 'intel'
        
        except Exception:
            pass
        
        # Fallback to lspci
        try:
            result = subprocess.run(
                ['lspci'],
                capture_output=True,
                timeout=2,
                text=True
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                for line in output.split('\n'):
                    if 'vga' in line or '3d' in line or 'display' in line:
                        if 'nvidia' in line:
                            return 'nvidia'
                        elif 'amd' in line or 'radeon' in line:
                            return 'amd'
                        elif 'intel' in line:
                            return 'intel'
        
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def detect_vulkan_support_wayland() -> bool:
        """
        Detect Vulkan support in Wayland.
        
        Returns:
            True if Vulkan is available for Wayland
        """
        try:
            result = subprocess.run(
                ['vulkaninfo'],
                capture_output=True,
                timeout=2,
                text=True
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                # Check for Wayland platform support
                if 'wayland' in output or 'khr_wayland_surface' in output:
                    return True
        
        except Exception:
            pass
        
        return False
    
    @staticmethod
    def detect_wayland_compositing() -> Dict[str, bool]:
        """
        Detect Wayland compositor capabilities for GPU rendering.
        
        Returns:
            Dict with compositor capabilities
        """
        caps = {
            'hw_compositing': False,
            'direct_rendering': False,
            'tearing_control': False,
            'damage_tracking': False,
        }
        
        try:
            # Check WAYLAND_DISPLAY
            wayland_display = os.environ.get('WAYLAND_DISPLAY', '')
            if not wayland_display:
                return caps
            
            # Try to query via weston-info
            result = subprocess.run(
                ['weston-info'],
                capture_output=True,
                timeout=2,
                text=True
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                # Check for various capabilities
                if 'hardware' in output or 'gpu' in output:
                    caps['hw_compositing'] = True
                
                if 'direct' in output:
                    caps['direct_rendering'] = True
                
                if 'tearing' in output or 'vsync' in output:
                    caps['tearing_control'] = True
                
                if 'damage' in output:
                    caps['damage_tracking'] = True
        
        except Exception:
            pass
        
        return caps
    
    @staticmethod
    def detect_wayland_gpu_acceleration() -> Dict[str, bool]:
        """
        Comprehensive Wayland GPU acceleration detection.
        
        Returns:
            Dict with GPU acceleration capabilities
        """
        return {
            'egl': WaylandGPUDetector.detect_egl_support(),
            'vulkan': WaylandGPUDetector.detect_vulkan_support_wayland(),
            'gl_es': WaylandGPUDetector.detect_egl_support(),  # EGL implies GL ES
            'hw_compositing': WaylandGPUDetector.detect_wayland_compositing().get('hw_compositing', False),
            'direct_rendering': WaylandGPUDetector.detect_wayland_compositing().get('direct_rendering', False),
        }
    
    @staticmethod
    def get_wayland_gpu_capabilities() -> Dict[str, any]:
        """
        Get comprehensive Wayland GPU capabilities.
        
        Returns:
            Dict with all GPU capabilities for Wayland
        """
        return {
            'gpu_acceleration': WaylandGPUDetector.detect_wayland_gpu_acceleration(),
            'egl_extensions': WaylandGPUDetector.detect_wayland_egl_extensions(),
            'gpu_vendor': WaylandGPUDetector.detect_wayland_gpu_vendor(),
            'compositor_caps': WaylandGPUDetector.detect_wayland_compositing(),
        }
    
    @staticmethod
    def is_wayland_gpu_capable() -> bool:
        """
        Determine if Wayland environment supports GPU acceleration.
        
        Returns:
            True if GPU acceleration is available on Wayland
        """
        caps = WaylandGPUDetector.detect_wayland_gpu_acceleration()
        
        # GPU capable if any acceleration method is available
        return any(caps.values())
    
    @staticmethod
    def get_wayland_rendering_recommendation() -> str:
        """
        Get recommended rendering backend for Wayland.
        
        Returns:
            'gpu' if capable, 'software' otherwise
        """
        return 'gpu' if WaylandGPUDetector.is_wayland_gpu_capable() else 'software'
