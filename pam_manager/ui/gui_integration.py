"""GUI Integration Layer - Phase 5 - Central coordination for all UI components."""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class IntegrationState(Enum):
    """Integration state."""
    INITIALIZED = "initialized"
    TABS_LOADED = "tabs_loaded"
    SIGNALS_CONNECTED = "signals_connected"
    READY = "ready"


class TabIdentifier(Enum):
    """Tab identifiers for Phase 5."""
    # Phase 4 Tabs
    WIZARD = "wizard"
    VALIDATION = "validation"
    BACKUP = "backup"
    DEPENDENCIES = "dependencies"
    MODULES = "modules"


@dataclass
class TabRegistration:
    """Tab registration info."""
    identifier: TabIdentifier
    tab_name: str
    tab_widget: Any  # QWidget
    index: Optional[int] = None
    is_enabled: bool = True


class SignalHub:
    """Central signal hub for inter-tab communication."""
    
    def __init__(self):
        """Initialize signal hub."""
        self.configuration_changed_callbacks: List[Callable] = []
        self.validation_completed_callbacks: List[Callable] = []
        self.backup_created_callbacks: List[Callable] = []
        self.module_enabled_callbacks: List[Callable] = []
        self.module_disabled_callbacks: List[Callable] = []
        self.error_occurred_callbacks: List[Callable] = []
    
    def register_configuration_changed(self, callback: Callable) -> None:
        """Register configuration changed handler."""
        self.configuration_changed_callbacks.append(callback)
    
    def emit_configuration_changed(self, config: Dict[str, Any]) -> None:
        """Emit configuration changed event."""
        for callback in self.configuration_changed_callbacks:
            try:
                callback(config)
            except Exception as e:
                logger.error(f"Error in configuration_changed callback: {e}")
    
    def register_validation_completed(self, callback: Callable) -> None:
        """Register validation completed handler."""
        self.validation_completed_callbacks.append(callback)
    
    def emit_validation_completed(self, results: Dict[str, Any]) -> None:
        """Emit validation completed event."""
        for callback in self.validation_completed_callbacks:
            try:
                callback(results)
            except Exception as e:
                logger.error(f"Error in validation_completed callback: {e}")
    
    def register_backup_created(self, callback: Callable) -> None:
        """Register backup created handler."""
        self.backup_created_callbacks.append(callback)
    
    def emit_backup_created(self, backup_id: str) -> None:
        """Emit backup created event."""
        for callback in self.backup_created_callbacks:
            try:
                callback(backup_id)
            except Exception as e:
                logger.error(f"Error in backup_created callback: {e}")
    
    def register_module_enabled(self, callback: Callable) -> None:
        """Register module enabled handler."""
        self.module_enabled_callbacks.append(callback)
    
    def emit_module_enabled(self, module_name: str) -> None:
        """Emit module enabled event."""
        for callback in self.module_enabled_callbacks:
            try:
                callback(module_name)
            except Exception as e:
                logger.error(f"Error in module_enabled callback: {e}")
    
    def register_module_disabled(self, callback: Callable) -> None:
        """Register module disabled handler."""
        self.module_disabled_callbacks.append(callback)
    
    def emit_module_disabled(self, module_name: str) -> None:
        """Emit module disabled event."""
        for callback in self.module_disabled_callbacks:
            try:
                callback(module_name)
            except Exception as e:
                logger.error(f"Error in module_disabled callback: {e}")
    
    def register_error_occurred(self, callback: Callable) -> None:
        """Register error occurred handler."""
        self.error_occurred_callbacks.append(callback)
    
    def emit_error_occurred(self, error_message: str) -> None:
        """Emit error occurred event."""
        for callback in self.error_occurred_callbacks:
            try:
                callback(error_message)
            except Exception as e:
                logger.error(f"Error in error_occurred callback: {e}")


class GUIIntegrationContext:
    """Context for GUI integration."""
    
    def __init__(self):
        """Initialize context."""
        self.signal_hub = SignalHub()
        self.state = IntegrationState.INITIALIZED
        self.tabs: Dict[TabIdentifier, TabRegistration] = {}
        self.current_configuration: Optional[Dict[str, Any]] = None
        self.current_validation_results: Optional[Dict[str, Any]] = None
        self.callbacks: Dict[str, List[Callable]] = {}
        
        logger.info("GUIIntegrationContext initialized")
    
    def register_tab(self, registration: TabRegistration) -> bool:
        """
        Register tab.
        
        Args:
            registration: Tab registration
            
        Returns:
            bool: Success
        """
        if registration.identifier in self.tabs:
            logger.warning(f"Tab {registration.identifier.value} already registered")
            return False
        
        self.tabs[registration.identifier] = registration
        logger.info(f"Tab registered: {registration.identifier.value}")
        return True
    
    def get_tab(self, identifier: TabIdentifier) -> Optional[TabRegistration]:
        """Get tab by identifier."""
        return self.tabs.get(identifier)
    
    def get_all_tabs(self) -> List[TabRegistration]:
        """Get all registered tabs."""
        return list(self.tabs.values())
    
    def set_configuration(self, config: Dict[str, Any]) -> None:
        """
        Set current configuration.
        
        Args:
            config: Configuration dict
        """
        self.current_configuration = config
        self.signal_hub.emit_configuration_changed(config)
        logger.debug("Configuration updated")
    
    def get_configuration(self) -> Optional[Dict[str, Any]]:
        """Get current configuration."""
        return self.current_configuration
    
    def set_validation_results(self, results: Dict[str, Any]) -> None:
        """
        Set validation results.
        
        Args:
            results: Validation results
        """
        self.current_validation_results = results
        self.signal_hub.emit_validation_completed(results)
        logger.debug("Validation results updated")
    
    def get_validation_results(self) -> Optional[Dict[str, Any]]:
        """Get validation results."""
        return self.current_validation_results
    
    def transition_to_ready(self) -> None:
        """Transition context to ready state."""
        self.state = IntegrationState.READY
        logger.info("Integration context is ready")
    
    def is_ready(self) -> bool:
        """Check if context is ready."""
        return self.state == IntegrationState.READY


class GUIIntegrationBridge:
    """Bridge between Phase 4 components and PAMManagerGUI."""
    
    def __init__(self, context: GUIIntegrationContext):
        """
        Initialize bridge.
        
        Args:
            context: Integration context
        """
        self.context = context
        self.logger = logging.getLogger(__name__)
    
    def connect_wizard_to_validation(self) -> None:
        """Connect wizard output to validation panel."""
        def on_wizard_completed(config):
            self.context.set_configuration(config)
            self.logger.info("Wizard completed, configuration updated")
        
        self.context.signal_hub.register_configuration_changed(on_wizard_completed)
    
    def connect_validation_to_backup(self) -> None:
        """Connect validation results to backup manager."""
        def on_validation_completed(results):
            if results.get("has_errors"):
                self.context.signal_hub.emit_error_occurred(
                    "Configuration has validation errors"
                )
            else:
                self.logger.info("Validation passed, backup can proceed")
        
        self.context.signal_hub.register_validation_completed(on_validation_completed)
    
    def connect_modules_to_dependencies(self) -> None:
        """Connect module selection to dependency analysis."""
        def on_module_enabled(module_name):
            self.logger.info(f"Module enabled: {module_name}, check dependencies")
        
        def on_module_disabled(module_name):
            self.logger.info(f"Module disabled: {module_name}")
        
        self.context.signal_hub.register_module_enabled(on_module_enabled)
        self.context.signal_hub.register_module_disabled(on_module_disabled)
    
    def establish_all_connections(self) -> None:
        """Establish all inter-tab connections."""
        self.logger.info("Establishing inter-tab connections...")
        
        self.connect_wizard_to_validation()
        self.connect_validation_to_backup()
        self.connect_modules_to_dependencies()
        
        self.context.transition_to_ready()
        self.logger.info("All connections established")


def create_integration_context() -> GUIIntegrationContext:
    """
    Create and configure integration context.
    
    Returns:
        GUIIntegrationContext: Configured context
    """
    context = GUIIntegrationContext()
    bridge = GUIIntegrationBridge(context)
    bridge.establish_all_connections()
    return context
