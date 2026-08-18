"""
Configuration Auto-Optimization Module
Analyzes environment and automatically recommends optimal GUI configurations.
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum


class OptimizationLevel(Enum):
    """Optimization aggressiveness level."""
    CONSERVATIVE = "conservative"  # Minimal optimizations, maximum compatibility
    BALANCED = "balanced"  # Moderate optimizations
    AGGRESSIVE = "aggressive"  # Maximum optimizations for performance


@dataclass
class ConfigurationRecommendation:
    """Recommended configuration for GUI."""
    name: str  # Recommendation name
    description: str  # Human-readable description
    environment_vars: Dict[str, str]  # Environment variables to set
    adapter: str  # Adapter to use
    style: str  # Qt style to use
    quality_level: str  # 'low', 'medium', 'high'
    expected_performance: str  # 'poor', 'fair', 'good', 'excellent'
    compatibility_score: float  # 0.0-1.0 how compatible with this system
    reasoning: str  # Why this configuration is recommended


class ConfigurationOptimizer:
    """
    Analyzes environment and recommends optimal configurations.
    """
    
    @staticmethod
    def analyze_and_recommend(caps: 'GuiCapabilities', 
                             level: OptimizationLevel = OptimizationLevel.BALANCED) -> ConfigurationRecommendation:
        """
        Analyze environment and recommend optimal configuration.
        
        Args:
            caps: GuiCapabilities from environment detection
            level: Optimization level (conservative, balanced, aggressive)
            
        Returns:
            ConfigurationRecommendation with optimal settings
        """
        from pam_manager.gui_environment import DisplayServer, X11Server
        
        # Route to specialized analyzer based on display server
        if caps.display_server == DisplayServer.WAYLAND:
            return ConfigurationOptimizer._recommend_wayland(caps, level)
        elif caps.display_server == DisplayServer.X11:
            return ConfigurationOptimizer._recommend_x11(caps, level)
        elif caps.display_server == DisplayServer.HEADLESS:
            return ConfigurationOptimizer._recommend_headless(caps, level)
        else:
            return ConfigurationOptimizer._recommend_fallback(caps, level)
    
    @staticmethod
    def _recommend_wayland(caps: 'GuiCapabilities', 
                          level: OptimizationLevel) -> ConfigurationRecommendation:
        """Recommend configuration for Wayland."""
        env_vars = {
            'QT_QPA_PLATFORM': 'wayland',
            'QT_QPA_PLATFORMTHEME': 'adwaita',
        }
        
        if level == OptimizationLevel.AGGRESSIVE:
            env_vars['QT_QPA_ENABLE_HIDPI_SCALING'] = '1'
            env_vars['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
        
        return ConfigurationRecommendation(
            name='Wayland Native',
            description='Optimized for Wayland display server with native settings',
            environment_vars=env_vars,
            adapter='wayland',
            style='Adwaita',
            quality_level='high' if level != OptimizationLevel.CONSERVATIVE else 'medium',
            expected_performance='good',
            compatibility_score=0.98,
            reasoning='Wayland detected. Using native platform integration for best experience.'
        )
    
    @staticmethod
    def _recommend_x11(caps: 'GuiCapabilities',
                       level: OptimizationLevel) -> ConfigurationRecommendation:
        """Recommend configuration for X11."""
        from pam_manager.gui_environment import X11Server
        
        # Detect if remote
        if caps.supports_remote_x11:
            return ConfigurationOptimizer._recommend_x11_remote(caps, level)
        
        # Local X11 recommendations vary by X11 server
        if caps.x11_server == X11Server.XORG:
            return ConfigurationOptimizer._recommend_xorg(caps, level)
        elif caps.x11_server == X11Server.XFREE86:
            return ConfigurationOptimizer._recommend_xfree86(caps, level)
        elif caps.x11_server == X11Server.XLIBRE:
            return ConfigurationOptimizer._recommend_xlibre(caps, level)
        else:
            return ConfigurationOptimizer._recommend_x11_generic(caps, level)
    
    @staticmethod
    def _recommend_xorg(caps: 'GuiCapabilities',
                       level: OptimizationLevel) -> ConfigurationRecommendation:
        """Recommend configuration for Xorg."""
        env_vars = {
            'QT_QPA_PLATFORM': 'xcb',
        }
        
        # GPU optimization
        if caps.gpu_acceleration.get('glx', False) and level != OptimizationLevel.CONSERVATIVE:
            env_vars['QT_XCB_GL_INTEGRATION'] = 'xcb_glx'
            quality = 'high'
            performance = 'excellent'
        else:
            env_vars['QT_XCB_GL_INTEGRATION'] = 'none'
            env_vars['QT_XCB_SOFTWARE_RENDER'] = '1'
            quality = 'medium'
            performance = 'good'
        
        if level == OptimizationLevel.AGGRESSIVE:
            env_vars['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
        
        return ConfigurationRecommendation(
            name='Xorg Optimized' if caps.gpu_acceleration.get('glx') else 'Xorg Safe',
            description='Optimized for Xorg X11 server' + (' with GPU acceleration' if env_vars.get('QT_XCB_GL_INTEGRATION') == 'xcb_glx' else ''),
            environment_vars=env_vars,
            adapter='xorg',
            style='Fusion',
            quality_level=quality,
            expected_performance=performance,
            compatibility_score=0.95,
            reasoning=f"Xorg detected. GPU acceleration {'enabled' if env_vars.get('QT_XCB_GL_INTEGRATION') == 'xcb_glx' else 'disabled'} based on capabilities."
        )
    
    @staticmethod
    def _recommend_xfree86(caps: 'GuiCapabilities',
                          level: OptimizationLevel) -> ConfigurationRecommendation:
        """Recommend configuration for XFree86."""
        env_vars = {
            'QT_QPA_PLATFORM': 'xcb',
            'QT_XCB_GL_INTEGRATION': 'none',
            'QT_XCB_SOFTWARE_RENDER': '1',
            'QT_XCB_USE_NATIVE_PAINTING': '1',
        }
        
        return ConfigurationRecommendation(
            name='XFree86 Conservative',
            description='Conservative settings for legacy XFree86 server',
            environment_vars=env_vars,
            adapter='xfree86',
            style='Fusion',
            quality_level='medium',
            expected_performance='fair',
            compatibility_score=0.85,
            reasoning='XFree86 detected. Using conservative settings to ensure stability.'
        )
    
    @staticmethod
    def _recommend_xlibre(caps: 'GuiCapabilities',
                         level: OptimizationLevel) -> ConfigurationRecommendation:
        """Recommend configuration for XlibRE."""
        env_vars = {
            'QT_QPA_PLATFORM': 'xcb',
            'QT_XCB_GL_INTEGRATION': 'none',
            'QT_XCB_SOFTWARE_RENDER': '1',
        }
        
        return ConfigurationRecommendation(
            name='XlibRE Compatible',
            description='Optimized for XlibRE alternative X11 implementation',
            environment_vars=env_vars,
            adapter='xlibre',
            style='Fusion',
            quality_level='medium',
            expected_performance='fair',
            compatibility_score=0.82,
            reasoning='XlibRE detected. Using compatible settings for this X11 variant.'
        )
    
    @staticmethod
    def _recommend_x11_remote(caps: 'GuiCapabilities',
                             level: OptimizationLevel) -> ConfigurationRecommendation:
        """Recommend configuration for remote X11."""
        env_vars = {
            'QT_QPA_PLATFORM': 'xcb',
            'QT_XCB_GL_INTEGRATION': 'none',
            'QT_XCB_SOFTWARE_RENDER': '1',
        }
        
        if level == OptimizationLevel.AGGRESSIVE:
            # Remote rendering optimizations
            env_vars['QT_XCB_NATIVE_PAINTING'] = '1'
        
        return ConfigurationRecommendation(
            name='Remote X11 Optimized',
            description='Optimized for remote X11 over SSH or TCP',
            environment_vars=env_vars,
            adapter='xorg',
            style='Fusion',
            quality_level='low',
            expected_performance='fair',
            compatibility_score=0.80,
            reasoning='Remote X11 detected. GPU disabled. Software rendering recommended.'
        )
    
    @staticmethod
    def _recommend_x11_generic(caps: 'GuiCapabilities',
                              level: OptimizationLevel) -> ConfigurationRecommendation:
        """Generic X11 recommendation."""
        env_vars = {
            'QT_QPA_PLATFORM': 'xcb',
        }
        
        if caps.gpu_acceleration.get('glx', False) and level != OptimizationLevel.CONSERVATIVE:
            env_vars['QT_XCB_GL_INTEGRATION'] = 'xcb_glx'
        else:
            env_vars['QT_XCB_GL_INTEGRATION'] = 'none'
        
        return ConfigurationRecommendation(
            name='X11 Generic',
            description='Generic configuration for X11 display server',
            environment_vars=env_vars,
            adapter='xorg',
            style='Fusion',
            quality_level='medium',
            expected_performance='good',
            compatibility_score=0.80,
            reasoning='X11 detected. Using generic optimized settings.'
        )
    
    @staticmethod
    def _recommend_headless(caps: 'GuiCapabilities',
                           level: OptimizationLevel) -> ConfigurationRecommendation:
        """Recommend configuration for headless operation."""
        return ConfigurationRecommendation(
            name='Headless Offscreen',
            description='Offscreen rendering for headless systems',
            environment_vars={
                'QT_QPA_PLATFORM': 'offscreen',
            },
            adapter='offscreen',
            style='Fusion',
            quality_level='low',
            expected_performance='fair',
            compatibility_score=0.90,
            reasoning='No display detected. Using offscreen rendering.'
        )
    
    @staticmethod
    def _recommend_fallback(caps: 'GuiCapabilities',
                           level: OptimizationLevel) -> ConfigurationRecommendation:
        """Fallback generic recommendation."""
        return ConfigurationRecommendation(
            name='Default Configuration',
            description='Generic fallback configuration',
            environment_vars={
                'QT_QPA_PLATFORM': 'auto',
            },
            adapter='default',
            style='Fusion',
            quality_level='medium',
            expected_performance='good',
            compatibility_score=0.70,
            reasoning='Unable to determine optimal configuration. Using fallback defaults.'
        )
    
    @staticmethod
    def get_all_recommendations(caps: 'GuiCapabilities') -> Dict[str, List[ConfigurationRecommendation]]:
        """
        Get recommendations for all optimization levels.
        
        Args:
            caps: GuiCapabilities
            
        Returns:
            Dict mapping optimization levels to recommendations
        """
        return {
            'conservative': ConfigurationOptimizer.analyze_and_recommend(caps, OptimizationLevel.CONSERVATIVE),
            'balanced': ConfigurationOptimizer.analyze_and_recommend(caps, OptimizationLevel.BALANCED),
            'aggressive': ConfigurationOptimizer.analyze_and_recommend(caps, OptimizationLevel.AGGRESSIVE),
        }
    
    @staticmethod
    def print_recommendation(rec: ConfigurationRecommendation):
        """Print recommendation in human-readable format."""
        print("\n" + "=" * 70)
        print("CONFIGURATION RECOMMENDATION")
        print("=" * 70)
        print(f"\n{rec.name}")
        print(f"Description: {rec.description}")
        print(f"\nQuality Level: {rec.quality_level.upper()}")
        print(f"Expected Performance: {rec.expected_performance.upper()}")
        print(f"Compatibility: {rec.compatibility_score*100:.0f}%")
        print(f"\nAdapter: {rec.adapter}")
        print(f"Style: {rec.style}")
        print(f"\nEnvironment Variables:")
        for var, val in rec.environment_vars.items():
            print(f"  export {var}={val}")
        print(f"\nReasoning:")
        print(f"  {rec.reasoning}")
        print("\n" + "=" * 70 + "\n")
