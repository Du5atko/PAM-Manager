"""
Remote Display Support Module
Extends GUI detection and GPU capabilities for remote X11 sessions.
Handles SSH X forwarding, X via TCP, and remote rendering scenarios.
"""

import os
import re
import socket
import subprocess
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RemoteDisplayInfo:
    """Information about remote display."""
    is_remote: bool  # Whether display is remote
    remote_host: Optional[str]  # Hostname or IP
    remote_port: Optional[int]  # X11 port (6000+)
    transport: str  # 'ssh', 'tcp', 'unix', 'local'
    forwarding_type: str  # 'x11-forwarding', 'tcp-display', 'direct'
    supports_gpu: bool  # Whether GPU acceleration likely works
    recommended_rendering: str  # 'gpu', 'software', 'remote-rendering'
    warnings: list  # List of warnings for remote setup


class RemoteDisplayDetector:
    """
    Detects and analyzes remote display configurations.
    Provides recommendations for remote X11 sessions.
    """
    
    @staticmethod
    def detect_remote_display() -> RemoteDisplayInfo:
        """
        Detect remote display configuration.
        
        Returns:
            RemoteDisplayInfo with detection results
        """
        display = os.environ.get('DISPLAY', '')
        
        # Parse DISPLAY variable
        if not display:
            return RemoteDisplayInfo(
                is_remote=False,
                remote_host=None,
                remote_port=None,
                transport='unix',
                forwarding_type='direct',
                supports_gpu=True,
                recommended_rendering='gpu',
                warnings=[]
            )
        
        # Try to parse display
        remote_info = RemoteDisplayDetector._parse_display(display)
        
        # If remote, get additional info
        if remote_info.is_remote:
            RemoteDisplayDetector._enhance_remote_info(remote_info)
        
        return remote_info
    
    @staticmethod
    def _parse_display(display: str) -> RemoteDisplayInfo:
        """Parse DISPLAY variable to extract remote info."""
        warnings = []
        
        # Pattern: [host]:display[.screen]
        # Examples:
        #   :0          -> local
        #   localhost:10 -> SSH forwarding
        #   192.168.1.1:10 -> TCP X11
        #   /tmp/.X11-unix/X0 -> Unix socket
        
        if display.startswith('/'):
            # Unix socket
            return RemoteDisplayInfo(
                is_remote=False,
                remote_host=None,
                remote_port=None,
                transport='unix',
                forwarding_type='direct',
                supports_gpu=True,
                recommended_rendering='gpu',
                warnings=[]
            )
        
        # Parse host:display.screen
        # Pattern: [host]:display[.screen] where host is optional
        # Examples: :0, localhost:10, 192.168.1.1:10
        match = re.match(r'^(?:([^:]*):)?(\d+)(?:\.(\d+))?$', display)
        if not match:
            warnings.append(f"Cannot parse DISPLAY format: {display}")
            return RemoteDisplayInfo(
                is_remote=False,
                remote_host=None,
                remote_port=None,
                transport='unknown',
                forwarding_type='direct',
                supports_gpu=False,
                recommended_rendering='software',
                warnings=warnings
            )
        
        host, display_num, screen = match.groups()
        display_num = int(display_num)
        port = 6000 + display_num
        
        # No host or localhost = local display
        if not host or host in ('localhost', '127.0.0.1', '::1'):
            return RemoteDisplayInfo(
                is_remote=False,
                remote_host=host or 'localhost',
                remote_port=port,
                transport='tcp' if host else 'unix',
                forwarding_type='x11-forwarding' if host else 'direct',
                supports_gpu=True,
                recommended_rendering='gpu',
                warnings=[]
            )
        
        # Remote host
        return RemoteDisplayInfo(
            is_remote=True,
            remote_host=host,
            remote_port=port,
            transport='tcp',
            forwarding_type='tcp-display',
            supports_gpu=False,  # Conservative default
            recommended_rendering='software',
            warnings=['Remote X11 over TCP detected - GPU likely unavailable']
        )
    
    @staticmethod
    def _enhance_remote_info(info: RemoteDisplayInfo):
        """Enhance remote info with additional detection."""
        if not info.is_remote or not info.remote_host:
            return
        
        # Try to detect SSH X forwarding
        if RemoteDisplayDetector._is_ssh_x_forwarding(info.remote_host):
            info.forwarding_type = 'x11-forwarding'
            info.supports_gpu = False  # SSH forwarding doesn't support GPU
            info.recommended_rendering = 'software'
            info.warnings = ['SSH X11 forwarding detected - GPU unavailable']
        
        # Try to detect direct TCP X11
        elif RemoteDisplayDetector._can_reach_x11_server(info.remote_host, info.remote_port):
            info.transport = 'tcp'
            info.forwarding_type = 'tcp-display'
            info.supports_gpu = False  # Direct TCP usually doesn't support GPU
            info.recommended_rendering = 'software'
            info.warnings.append('Direct TCP X11 connection - GPU likely unavailable')
        
        # Detect remote rendering capabilities
        if RemoteDisplayDetector._supports_remote_rendering(info.remote_host):
            info.supports_gpu = False  # Manual rendering required
            info.recommended_rendering = 'remote-rendering'
            info.warnings.append('Remote rendering detected - use quality setting wisely')
    
    @staticmethod
    def _is_ssh_x_forwarding(host: str) -> bool:
        """Check if we're connected via SSH X forwarding."""
        # SSH X forwarding sets DISPLAY=localhost:N
        # If host is localhost and we have SSH_CONNECTION env, likely SSH
        ssh_connection = os.environ.get('SSH_CONNECTION', '')
        return ssh_connection != ''
    
    @staticmethod
    def _can_reach_x11_server(host: str, port: int) -> bool:
        """Check if X11 server is reachable."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    @staticmethod
    def _supports_remote_rendering(host: str) -> bool:
        """Check if remote host supports remote rendering (VirtualGL, etc)."""
        try:
            # Check for VirtualGL or other remote rendering tools
            result = subprocess.run(
                ['ssh', host, 'which vglrun 2>/dev/null'],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def get_remote_display_capabilities() -> Dict[str, bool]:
        """
        Get capabilities available for remote display.
        
        Returns:
            Dict with capability flags
        """
        info = RemoteDisplayDetector.detect_remote_display()
        
        return {
            'gpu_acceleration': info.supports_gpu,
            'software_rendering': True,  # Always available
            'remote_rendering': info.recommended_rendering == 'remote-rendering',
            'ssh_forwarding': info.forwarding_type == 'x11-forwarding',
            'tcp_display': info.forwarding_type == 'tcp-display',
            'local_display': not info.is_remote,
        }
    
    @staticmethod
    def get_remote_display_recommendations() -> Dict[str, str]:
        """
        Get recommendations for remote display configuration.
        
        Returns:
            Dict with recommendations
        """
        info = RemoteDisplayDetector.detect_remote_display()
        
        recommendations = {
            'display': info.remote_host or 'local',
            'rendering_backend': info.recommended_rendering,
            'quality_setting': 'low' if info.recommended_rendering != 'gpu' else 'high',
            'optimization': '',
        }
        
        # Add specific recommendations
        if info.forwarding_type == 'x11-forwarding':
            recommendations['optimization'] = 'Use -X (untrusted) for better performance'
        elif info.forwarding_type == 'tcp-display':
            recommendations['optimization'] = 'Consider using SSH tunneling: ssh -X host'
        elif info.recommended_rendering == 'remote-rendering':
            recommendations['optimization'] = 'VirtualGL/remote rendering available'
        
        return recommendations


def enhance_environment_for_remote(caps_dict: dict) -> dict:
    """
    Enhance capabilities dictionary with remote display info.
    
    Args:
        caps_dict: Existing capabilities dictionary
        
    Returns:
        Updated dictionary with remote display enhancements
    """
    remote_caps = RemoteDisplayDetector.get_remote_display_capabilities()
    remote_info = RemoteDisplayDetector.detect_remote_display()
    
    # Add remote display info
    caps_dict['remote_display'] = {
        'is_remote': remote_info.is_remote,
        'remote_host': remote_info.remote_host,
        'transport': remote_info.transport,
        'forwarding_type': remote_info.forwarding_type,
    }
    
    # Override GPU capabilities if remote
    if remote_info.is_remote and not remote_info.supports_gpu:
        if 'gpu_acceleration' in caps_dict:
            caps_dict['gpu_acceleration']['glx'] = False
            caps_dict['gpu_acceleration']['egl'] = False
            caps_dict['gpu_acceleration']['vulkan'] = False
    
    # Update rendering backend recommendation
    if not remote_info.supports_gpu:
        caps_dict['rendering_backend'] = remote_info.recommended_rendering
    
    return caps_dict
