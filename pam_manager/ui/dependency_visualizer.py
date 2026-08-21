"""Dependency graph visualization for UI - Phase 4."""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
import logging


logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """Node in dependency graph."""
    name: str
    node_type: str  # "module", "service", "facility"
    color: str = "blue"
    description: str = ""


@dataclass
class GraphEdge:
    """Edge in dependency graph."""
    source: str
    target: str
    edge_type: str  # "depends", "conflicts", "requires"
    style: str = "solid"
    label: str = ""


class DependencyVisualizer:
    """Visualize PAM module dependencies."""
    
    def __init__(self):
        """Initialize visualizer."""
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.conflict_map: Dict[str, List[str]] = {}
        self.dependency_map: Dict[str, List[str]] = {}
    
    def add_node(self, name: str, node_type: str, description: str = "") -> None:
        """
        Add node to graph.
        
        Args:
            name: Node name
            node_type: Node type
            description: Node description
        """
        color_map = {
            "module": "lightblue",
            "service": "lightgreen",
            "facility": "lightyellow",
            "conflict": "lightcoral",
        }
        
        self.nodes[name] = GraphNode(
            name=name,
            node_type=node_type,
            color=color_map.get(node_type, "gray"),
            description=description
        )
    
    def add_dependency(self, from_module: str, to_module: str, label: str = "") -> None:
        """
        Add dependency edge.
        
        Args:
            from_module: Source module
            to_module: Target module
            label: Edge label
        """
        self.add_node(from_module, "module")
        self.add_node(to_module, "module")
        
        edge = GraphEdge(
            source=from_module,
            target=to_module,
            edge_type="depends",
            style="solid",
            label=label
        )
        self.edges.append(edge)
        
        if from_module not in self.dependency_map:
            self.dependency_map[from_module] = []
        self.dependency_map[from_module].append(to_module)
    
    def add_conflict(self, module1: str, module2: str) -> None:
        """
        Add conflict edge.
        
        Args:
            module1: First module
            module2: Second module
        """
        self.add_node(module1, "module")
        self.add_node(module2, "module")
        
        edge = GraphEdge(
            source=module1,
            target=module2,
            edge_type="conflicts",
            style="dashed",
            label="conflicts"
        )
        self.edges.append(edge)
        
        if module1 not in self.conflict_map:
            self.conflict_map[module1] = []
        self.conflict_map[module1].append(module2)
        
        if module2 not in self.conflict_map:
            self.conflict_map[module2] = []
        self.conflict_map[module2].append(module1)
    
    def get_module_conflicts(self, module: str) -> List[str]:
        """
        Get modules that conflict with given module.
        
        Args:
            module: Module name
            
        Returns:
            List[str]: Conflicting modules
        """
        return self.conflict_map.get(module, [])
    
    def get_module_dependencies(self, module: str) -> List[str]:
        """
        Get modules that given module depends on.
        
        Args:
            module: Module name
            
        Returns:
            List[str]: Dependent modules
        """
        return self.dependency_map.get(module, [])
    
    def has_circular_dependency(self) -> bool:
        """
        Check if graph has circular dependencies.
        
        Returns:
            bool: True if circular dependency exists
        """
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.get_module_dependencies(node):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.nodes:
            if node not in visited:
                if has_cycle(node):
                    return True
        
        return False
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """
        Find all circular dependencies.
        
        Returns:
            List[List[str]]: Lists of modules in cycles
        """
        cycles = []
        visited = set()
        
        def find_cycles(node, path):
            if node in path:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            
            for neighbor in self.get_module_dependencies(node):
                find_cycles(neighbor, path + [node])
        
        for node in self.nodes:
            if node not in visited:
                find_cycles(node, [])
        
        # Remove duplicate cycles
        unique_cycles = []
        for cycle in cycles:
            normalized = tuple(sorted(set(cycle[:-1])))  # Remove duplicate end node
            if normalized not in [tuple(sorted(set(c[:-1]))) for c in unique_cycles]:
                unique_cycles.append(cycle)
        
        return unique_cycles
    
    def get_graphviz_dot(self) -> str:
        """
        Get Graphviz DOT format.
        
        Returns:
            str: DOT format graph definition
        """
        lines = ["digraph PAMDependencies {"]
        lines.append('  rankdir=LR;')
        lines.append('  node [shape=box, style=filled];')
        
        # Add nodes
        for name, node in self.nodes.items():
            lines.append(
                f'  "{name}" [label="{name}", fillcolor="{node.color}"];'
            )
        
        # Add edges
        for edge in self.edges:
            style_attr = f', style=dashed' if edge.edge_type == "conflicts" else ""
            label_attr = f', label="{edge.label}"' if edge.label else ""
            color_attr = ', color=red' if edge.edge_type == "conflicts" else ""
            
            lines.append(
                f'  "{edge.source}" -> "{edge.target}" '
                f'[{style_attr}{label_attr}{color_attr}];'
            )
        
        lines.append("}")
        return "\n".join(lines)
    
    def generate_ascii_graph(self) -> str:
        """
        Generate ASCII art representation.
        
        Returns:
            str: ASCII graph
        """
        report = [
            "╔════════════════════════════════════════╗",
            "║   PAM DEPENDENCY VISUALIZATION         ║",
            "╚════════════════════════════════════════╝",
            "",
            "MODULES:",
        ]
        
        for name in sorted(self.nodes.keys()):
            node = self.nodes[name]
            conflicts = self.get_module_conflicts(name)
            depends = self.get_module_dependencies(name)
            
            report.append(f"  • {name}")
            if node.description:
                report.append(f"    Description: {node.description}")
            if conflicts:
                report.append(f"    Conflicts with: {', '.join(conflicts)}")
            if depends:
                report.append(f"    Depends on: {', '.join(depends)}")
        
        report.append("")
        report.append("CONFLICTS:")
        
        if self.conflict_map:
            for module, conflicts in sorted(self.conflict_map.items()):
                for conflict in conflicts:
                    if module < conflict:  # Avoid duplicates
                        report.append(f"  ✗ {module} ↔ {conflict}")
        else:
            report.append("  None")
        
        report.append("")
        
        if self.has_circular_dependency():
            cycles = self.find_circular_dependencies()
            report.append("CIRCULAR DEPENDENCIES (ERRORS):")
            for cycle in cycles:
                report.append(f"  ✗ {' → '.join(cycle)}")
        
        return "\n".join(report)
    
    def analyze_configuration(self, modules: List[str]) -> Tuple[bool, List[str]]:
        """
        Analyze configuration for issues.
        
        Args:
            modules: List of modules in configuration
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, issues)
        """
        issues = []
        
        # Check for conflicts
        for i, module1 in enumerate(modules):
            for module2 in modules[i+1:]:
                if module2 in self.get_module_conflicts(module1):
                    issues.append(f"CONFLICT: {module1} and {module2} cannot be used together")
        
        # Check for missing dependencies
        for module in modules:
            dependencies = self.get_module_dependencies(module)
            missing = [d for d in dependencies if d not in modules]
            if missing:
                issues.append(f"MISSING: {module} requires {', '.join(missing)}")
        
        return (len(issues) == 0, issues)


class ModuleConflictResolver:
    """Resolve module conflicts."""
    
    def __init__(self, visualizer: DependencyVisualizer):
        """
        Initialize conflict resolver.
        
        Args:
            visualizer: Dependency visualizer
        """
        self.visualizer = visualizer
    
    def get_conflict_resolution(self, module: str) -> Dict[str, any]:
        """
        Get conflict resolution options for module.
        
        Args:
            module: Module name
            
        Returns:
            Dict[str, any]: Resolution options
        """
        conflicts = self.visualizer.get_module_conflicts(module)
        
        return {
            "module": module,
            "conflicts_with": conflicts,
            "options": {
                "remove": f"Remove conflicting modules: {conflicts}",
                "replace": f"Replace with alternative modules",
                "skip": f"Skip this module",
            }
        }
    
    def suggest_alternative_modules(self, module: str) -> List[str]:
        """
        Suggest alternative modules.
        
        Args:
            module: Module name
            
        Returns:
            List[str]: Alternative modules
        """
        # This would be populated from platform metadata
        alternatives = {
            "pam_pwquality": ["pam_cracklib", "pam_passwdqc"],
            "pam_cracklib": ["pam_pwquality", "pam_passwdqc"],
            "pam_faillock": ["pam_tally2"],
            "pam_tally2": ["pam_faillock"],
        }
        
        return alternatives.get(module, [])
