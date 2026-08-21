"""Tab Management and Extension System - Phase 5."""

from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass
import logging

# Try PyQt5 first, fallback to PyQt4
try:
    from PyQt5.QtWidgets import QTabWidget, QWidget
    from PyQt5.QtCore import pyqtSignal
    QT_VERSION = 5
except ImportError:
    from PyQt4.QtGui import QTabWidget, QWidget
    from PyQt4.QtCore import pyqtSignal
    QT_VERSION = 4

from pam_manager.ui.gui_integration import (
    GUIIntegrationContext,
    TabIdentifier,
    TabRegistration,
    create_integration_context,
)


logger = logging.getLogger(__name__)


class TabManager:
    """Manages tab lifecycle and registration."""
    
    def __init__(self, tab_widget: QTabWidget):
        """
        Initialize tab manager.
        
        Args:
            tab_widget: Parent QTabWidget
        """
        self.tab_widget = tab_widget
        self.tabs: Dict[str, Tuple[int, QWidget]] = {}
        self.tab_contexts: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
    
    def add_tab(self, name: str, widget: QWidget, context: Optional[Dict] = None) -> int:
        """
        Add tab to widget.
        
        Args:
            name: Tab name/title
            widget: QWidget for tab
            context: Optional context data
            
        Returns:
            int: Tab index
        """
        index = self.tab_widget.addTab(widget, name)
        self.tabs[name] = (index, widget)
        if context:
            self.tab_contexts[name] = context
        
        self.logger.info(f"Tab added: {name} at index {index}")
        return index
    
    def remove_tab(self, name: str) -> bool:
        """
        Remove tab by name.
        
        Args:
            name: Tab name
            
        Returns:
            bool: Success
        """
        if name not in self.tabs:
            return False
        
        index, _ = self.tabs[name]
        self.tab_widget.removeTab(index)
        del self.tabs[name]
        if name in self.tab_contexts:
            del self.tab_contexts[name]
        
        self.logger.info(f"Tab removed: {name}")
        return True
    
    def get_tab_index(self, name: str) -> Optional[int]:
        """Get tab index by name."""
        if name in self.tabs:
            return self.tabs[name][0]
        return None
    
    def get_tab_widget(self, name: str) -> Optional[QWidget]:
        """Get tab widget by name."""
        if name in self.tabs:
            return self.tabs[name][1]
        return None
    
    def get_all_tab_names(self) -> List[str]:
        """Get all tab names."""
        return list(self.tabs.keys())


class PAMManagerGUIExtension:
    """Extension system for PAMManagerGUI - Phase 5."""
    
    def __init__(self, main_gui, tab_widget: Optional[QTabWidget] = None):
        """
        Initialize GUI extension.
        
        Args:
            main_gui: Main PAMManagerGUI instance
            tab_widget: Optional custom QTabWidget
        """
        self.main_gui = main_gui
        self.tab_widget = tab_widget
        self.context = create_integration_context()
        self.tab_manager: Optional[TabManager] = None
        self.widgets_cache: Dict[str, QWidget] = {}
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("PAMManagerGUIExtension initialized")
    
    def initialize(self) -> bool:
        """
        Initialize extension.
        
        Returns:
            bool: Success
        """
        try:
            # Create tab manager if not provided
            if self.tab_widget is None:
                if hasattr(self.main_gui, 'tab_widget'):
                    self.tab_widget = self.main_gui.tab_widget
                else:
                    self.logger.error("No tab widget available")
                    return False
            
            self.tab_manager = TabManager(self.tab_widget)
            
            self.logger.info("Extension initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing extension: {e}")
            return False
    
    def load_phase5_tabs(self) -> bool:
        """
        Load Phase 5 tabs.
        
        Returns:
            bool: Success
        """
        if not self.tab_manager:
            self.logger.error("TabManager not initialized")
            return False
        
        try:
            # Import widgets
            from pam_manager.ui.wizard_widget import ConfigurationWizardWidget
            from pam_manager.ui.validation_panel_widget import ValidationPanelWidget
            from pam_manager.ui.backup_manager_widget import BackupManagerWidget
            from pam_manager.ui.dependency_graph_widget import DependencyGraphWidget
            from pam_manager.ui.module_manager_tab import ModuleManagerTab
            
            # Create wizard tab
            wizard_widget = ConfigurationWizardWidget()
            self.tab_manager.add_tab("Wizard", wizard_widget)
            self.widgets_cache["wizard"] = wizard_widget
            
            # Create validation tab
            validation_widget = ValidationPanelWidget()
            self.tab_manager.add_tab("Validation", validation_widget)
            self.widgets_cache["validation"] = validation_widget
            
            # Create backup tab
            backup_widget = BackupManagerWidget()
            self.tab_manager.add_tab("Backup", backup_widget)
            self.widgets_cache["backup"] = backup_widget
            
            # Create dependencies tab
            deps_widget = DependencyGraphWidget()
            self.tab_manager.add_tab("Dependencies", deps_widget)
            self.widgets_cache["dependencies"] = deps_widget
            
            # Create modules tab
            modules_widget = ModuleManagerTab()
            self.tab_manager.add_tab("Modules", modules_widget)
            self.widgets_cache["modules"] = modules_widget
            
            self.logger.info("All Phase 5 tabs loaded successfully")
            return True
        
        except ImportError as e:
            self.logger.error(f"Failed to import Phase 5 widgets: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error loading Phase 5 tabs: {e}")
            return False
    
    def connect_signals(self) -> bool:
        """
        Connect signals between tabs.
        
        Returns:
            bool: Success
        """
        try:
            # Get widget references
            wizard = self.widgets_cache.get("wizard")
            validation = self.widgets_cache.get("validation")
            backup = self.widgets_cache.get("backup")
            modules = self.widgets_cache.get("modules")
            
            # Connect wizard to validation
            if wizard and validation:
                if hasattr(wizard, 'wizard_completed'):
                    wizard.wizard_completed.connect(
                        lambda cfg: self.context.set_configuration(cfg)
                    )
                    self.logger.info("Connected wizard to validation")
            
            # Connect backup signals
            if backup and hasattr(backup, 'backup_created'):
                backup.backup_created.connect(
                    lambda bid: self.context.signal_hub.emit_backup_created(bid)
                )
            
            # Connect module signals
            if modules and hasattr(modules, 'modules_changed'):
                modules.modules_changed.connect(
                    lambda mods: self.logger.info(f"Modules changed: {mods}")
                )
            
            self.logger.info("Signal connections established")
            return True
        
        except Exception as e:
            self.logger.error(f"Error connecting signals: {e}")
            return False
    
    def get_widget(self, name: str) -> Optional[QWidget]:
        """
        Get tab widget by name.
        
        Args:
            name: Widget name (wizard, validation, backup, dependencies, modules)
            
        Returns:
            Optional[QWidget]: Widget or None
        """
        return self.widgets_cache.get(name)
    
    def get_wizard(self):
        """Get wizard widget."""
        return self.get_widget("wizard")
    
    def get_validation(self):
        """Get validation widget."""
        return self.get_widget("validation")
    
    def get_backup(self):
        """Get backup widget."""
        return self.get_widget("backup")
    
    def get_dependencies(self):
        """Get dependency widget."""
        return self.get_widget("dependencies")
    
    def get_modules(self):
        """Get modules widget."""
        return self.get_widget("modules")
    
    def get_integration_context(self) -> GUIIntegrationContext:
        """Get integration context."""
        return self.context
    
    def get_tab_manager(self) -> Optional[TabManager]:
        """Get tab manager."""
        return self.tab_manager
    
    def get_all_widgets(self) -> Dict[str, QWidget]:
        """Get all cached widgets."""
        return dict(self.widgets_cache)
    
    def is_ready(self) -> bool:
        """Check if extension is fully ready."""
        return (
            self.tab_manager is not None and
            len(self.widgets_cache) == 5 and
            self.context.is_ready()
        )


def integrate_with_gui(main_gui_instance) -> Optional[PAMManagerGUIExtension]:
    """
    Integrate Phase 5 with main GUI.
    
    Args:
        main_gui_instance: PAMManagerGUI instance
        
    Returns:
        Optional[PAMManagerGUIExtension]: Extension instance or None
    """
    try:
        extension = PAMManagerGUIExtension(main_gui_instance)
        
        if not extension.initialize():
            logger.error("Failed to initialize extension")
            return None
        
        if not extension.load_phase5_tabs():
            logger.error("Failed to load Phase 5 tabs")
            return None
        
        if not extension.connect_signals():
            logger.error("Failed to connect signals")
            return None
        
        logger.info("Phase 5 GUI integration successful")
        return extension
    
    except Exception as e:
        logger.error(f"Error integrating with GUI: {e}")
        return None
