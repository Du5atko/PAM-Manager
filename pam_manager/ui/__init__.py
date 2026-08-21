"""PAM Manager UI module - User Interface components."""

# Phase 4 - Advanced Features Imports
from pam_manager.ui.wizard import ConfigurationWizard, WizardState
from pam_manager.ui.validation_panel import (
    ValidationPanel,
    ValidationMessage,
    ValidationLevel,
    RealTimeValidator,
)
from pam_manager.ui.backup_manager import BackupManager, BackupSnapshot, BackupScheduler
from pam_manager.ui.dependency_visualizer import (
    DependencyVisualizer,
    ModuleConflictResolver,
    GraphNode,
    GraphEdge,
)
from pam_manager.ui.module_manager import (
    ModuleManager,
    ModuleInfo,
    ModuleStatus,
    ModuleInstallationHelper,
)
from pam_manager.ui.module_manager_tab import ModuleManagerTab

# Phase 5 - GUI Integration Imports
from pam_manager.ui.gui_integration import (
    GUIIntegrationContext,
    GUIIntegrationBridge,
    SignalHub,
    TabIdentifier,
    TabRegistration,
    IntegrationState,
    create_integration_context,
)
from pam_manager.ui.gui_integration_tabs import (
    TabManager,
    PAMManagerGUIExtension,
    integrate_with_gui,
)

# Phase 4 - PyQt Widget Wrappers
try:
    from pam_manager.ui.wizard_widget import ConfigurationWizardWidget
    from pam_manager.ui.validation_panel_widget import ValidationPanelWidget
    from pam_manager.ui.backup_manager_widget import BackupManagerWidget
    from pam_manager.ui.dependency_graph_widget import DependencyGraphWidget
    HAS_QT_WIDGETS = True
except ImportError:
    HAS_QT_WIDGETS = False

__all__ = [
    # Phase 4 - Configuration Wizard
    "ConfigurationWizard",
    "WizardState",
    # Phase 4 - Validation Panel
    "ValidationPanel",
    "ValidationMessage",
    "ValidationLevel",
    "RealTimeValidator",
    # Phase 4 - Backup Manager
    "BackupManager",
    "BackupSnapshot",
    "BackupScheduler",
    # Phase 4 - Dependency Visualization
    "DependencyVisualizer",
    "ModuleConflictResolver",
    "GraphNode",
    "GraphEdge",
    # Phase 4 - Module Manager
    "ModuleManager",
    "ModuleInfo",
    "ModuleStatus",
    "ModuleInstallationHelper",
    # Phase 5 - Module Manager Tab
    "ModuleManagerTab",
    # Phase 5 - GUI Integration
    "GUIIntegrationContext",
    "GUIIntegrationBridge",
    "SignalHub",
    "TabIdentifier",
    "TabRegistration",
    "IntegrationState",
    "create_integration_context",
    "TabManager",
    "PAMManagerGUIExtension",
    "integrate_with_gui",
    # Phase 4 - PyQt Widgets (optional if PyQt available)
]

if HAS_QT_WIDGETS:
    __all__.extend([
        "ConfigurationWizardWidget",
        "ValidationPanelWidget",
        "BackupManagerWidget",
        "DependencyGraphWidget",
    ])
