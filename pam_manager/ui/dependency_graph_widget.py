"""Dependency Graph Visualization Widget - PyQt5/PyQt4 GUI - Phase 4."""

from typing import Optional, List
import logging

# Try PyQt5 first, fallback to PyQt4
try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,
        QPushButton, QComboBox, QGroupBox, QMessageBox
    )
    from PyQt5.QtCore import Qt
    QT_VERSION = 5
except ImportError:
    from PyQt4.QtGui import (
        QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,
        QPushButton, QComboBox, QGroupBox, QMessageBox
    )
    from PyQt4.QtCore import Qt
    QT_VERSION = 4

from pam_manager.ui.dependency_visualizer import DependencyVisualizer, ModuleConflictResolver


logger = logging.getLogger(__name__)


class DependencyGraphWidget(QWidget):
    """PyQt widget for dependency graph visualization."""
    
    def __init__(self, parent=None):
        """
        Initialize dependency graph widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.visualizer = DependencyVisualizer()
        self.conflict_resolver = ModuleConflictResolver(self.visualizer)
        
        self.setWindowTitle("Dependency Graph")
        self.setGeometry(100, 100, 1000, 700)
        
        self._create_ui()
        self._populate_demo_data()
    
    def _create_ui(self):
        """Create user interface."""
        main_layout = QVBoxLayout()
        
        # Controls section
        controls_group = QGroupBox("Analysis Controls")
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Analyze module:"))
        
        self.module_combo = QComboBox()
        self.module_combo.currentIndexChanged.connect(self._on_module_selected)
        controls_layout.addWidget(self.module_combo)
        
        controls_layout.addStretch()
        
        self.refresh_button = QPushButton("Refresh Graph")
        self.refresh_button.clicked.connect(self._update_display)
        controls_layout.addWidget(self.refresh_button)
        
        controls_group.setLayout(controls_layout)
        main_layout.addWidget(controls_group)
        
        # ASCII Graph Display
        graph_group = QGroupBox("Dependency Graph (ASCII)")
        graph_layout = QVBoxLayout()
        
        self.graph_text = QTextEdit()
        self.graph_text.setReadOnly(True)
        self.graph_text.setFont(self._get_monospace_font())
        graph_layout.addWidget(self.graph_text)
        
        graph_group.setLayout(graph_layout)
        main_layout.addWidget(graph_group)
        
        # Analysis section
        analysis_group = QGroupBox("Module Analysis")
        analysis_layout = QVBoxLayout()
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setMaximumHeight(200)
        analysis_layout.addWidget(self.analysis_text)
        
        analysis_group.setLayout(analysis_layout)
        main_layout.addWidget(analysis_group)
        
        # Information section
        info_layout = QHBoxLayout()
        
        self.export_dot_button = QPushButton("Export DOT")
        self.export_dot_button.clicked.connect(self._export_dot)
        info_layout.addWidget(self.export_dot_button)
        
        info_layout.addStretch()
        
        main_layout.addLayout(info_layout)
        
        self.setLayout(main_layout)
    
    def _get_monospace_font(self):
        """Get monospace font."""
        try:
            from PyQt5.QtGui import QFont
        except ImportError:
            from PyQt4.QtGui import QFont
        
        font = QFont("Courier")
        font.setPointSize(9)
        return font
    
    def _populate_demo_data(self):
        """Populate with demo dependency data."""
        # Common PAM module relationships
        self.visualizer.add_node("pam_unix", "module", "Unix password authentication")
        self.visualizer.add_node("pam_ldap", "module", "LDAP authentication")
        self.visualizer.add_node("pam_krb5", "module", "Kerberos authentication")
        self.visualizer.add_node("pam_pwquality", "module", "Password quality checker")
        self.visualizer.add_node("pam_cracklib", "module", "Password quality (legacy)")
        self.visualizer.add_node("pam_faillock", "module", "Account lockout")
        self.visualizer.add_node("pam_tally2", "module", "Account lockout (legacy)")
        self.visualizer.add_node("pam_env", "module", "Environment variables")
        self.visualizer.add_node("pam_motd", "module", "Message of the day")
        self.visualizer.add_node("pam_limits", "module", "Resource limits")
        self.visualizer.add_node("pam_lastlog", "module", "Last login reporting")
        
        # Add dependencies (some modules can depend on others)
        # In practice, PAM modules are usually independent
        
        # Add conflicts (common known conflicts)
        self.visualizer.add_conflict("pam_pwquality", "pam_cracklib")
        self.visualizer.add_conflict("pam_faillock", "pam_tally2")
        
        # Update combo box
        all_modules = list(self.visualizer.nodes.keys())
        self.module_combo.addItems(sorted(all_modules))
        
        self._update_display()
    
    def _on_module_selected(self):
        """Handle module selection."""
        self._update_display()
    
    def _update_display(self):
        """Update display."""
        # Show full graph
        graph = self.visualizer.generate_ascii_graph()
        self.graph_text.setText(graph)
        
        # Show analysis for selected module
        selected_module = self.module_combo.currentText()
        if selected_module:
            self._analyze_module(selected_module)
    
    def _analyze_module(self, module_name: str):
        """Analyze specific module."""
        analysis_lines = [
            f"MODULE ANALYSIS: {module_name}",
            "=" * 50,
            "",
        ]
        
        # Conflicts
        conflicts = self.visualizer.get_module_conflicts(module_name)
        if conflicts:
            analysis_lines.append("CONFLICTS WITH:")
            for conflict in conflicts:
                analysis_lines.append(f"  • {conflict}")
            analysis_lines.append("")
        else:
            analysis_lines.append("CONFLICTS: None")
            analysis_lines.append("")
        
        # Dependencies
        deps = self.visualizer.get_module_dependencies(module_name)
        if deps:
            analysis_lines.append("DEPENDS ON:")
            for dep in deps:
                analysis_lines.append(f"  • {dep}")
            analysis_lines.append("")
        else:
            analysis_lines.append("DEPENDENCIES: None")
            analysis_lines.append("")
        
        # Resolution advice for conflicts
        if conflicts:
            analysis_lines.append("CONFLICT RESOLUTION:")
            resolution = self.conflict_resolver.get_conflict_resolution(module_name)
            for option_key, option_text in resolution.get("options", {}).items():
                analysis_lines.append(f"  • {option_text}")
            analysis_lines.append("")
            
            # Suggest alternatives
            alternatives = self.conflict_resolver.suggest_alternative_modules(module_name)
            if alternatives:
                analysis_lines.append("ALTERNATIVES:")
                for alt in alternatives:
                    analysis_lines.append(f"  • {alt}")
        
        self.analysis_text.setText("\n".join(analysis_lines))
    
    def _export_dot(self):
        """Export as Graphviz DOT format."""
        dot_content = self.visualizer.get_graphviz_dot()
        
        try:
            from PyQt5.QtWidgets import QFileDialog
        except ImportError:
            from PyQt4.QtGui import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Dependency Graph",
            "pam_dependencies.dot",
            "DOT Files (*.dot);;Text Files (*.txt)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(dot_content)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Graph exported to {filename}\n\n"
                    f"To visualize, run:\n"
                    f"  dot -Tpng {filename} -o pam_dependencies.png"
                )
                logger.info(f"Exported DOT to {filename}")
            except Exception as e:
                logger.error(f"Error exporting: {e}")
                QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
    
    def set_modules(self, module_list: List[str]) -> None:
        """
        Set modules to analyze.
        
        Args:
            module_list: List of module names
        """
        for module in module_list:
            if module not in self.visualizer.nodes:
                self.visualizer.add_node(module, "module")
        
        self._update_display()
    
    def validate_configuration(self, modules: List[str]) -> bool:
        """
        Validate configuration for conflicts.
        
        Args:
            modules: List of modules in configuration
            
        Returns:
            bool: True if valid (no conflicts/issues)
        """
        is_valid, issues = self.visualizer.analyze_configuration(modules)
        
        if not is_valid:
            issues_text = "\n".join(issues)
            QMessageBox.warning(
                self,
                "Configuration Issues",
                f"Found issues in configuration:\n\n{issues_text}"
            )
        else:
            QMessageBox.information(
                self,
                "Configuration Valid",
                "No dependency conflicts detected!"
            )
        
        return is_valid
