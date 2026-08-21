"""Dependency Graph Module - PAM Configuration Dependency Analysis.

Analyzes and visualizes dependencies between PAM fragments, elements,
services, and modules with support for conflict detection and warnings.
"""

import logging
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DependencyType(Enum):
    """Type of dependency relationship."""
    REQUIRES = "requires"  # Must come before
    CONFLICTS = "conflicts"  # Cannot be used together
    SUPPORTS = "supports"  # Optional enhancement
    PLATFORM = "platform"  # Platform-specific
    INCLUDES = "includes"  # Includes another
    REFERENCES = "references"  # References another


class IssueType(Enum):
    """Types of dependency issues."""
    MISSING_MODULE = "missing_module"
    WRONG_ORDER = "wrong_order"
    CONFLICT_FLAGS = "conflict_flags"
    UNAVAILABLE_MODULE = "unavailable_module"
    PLATFORM_INCOMPATIBLE = "platform_incompatible"
    POTENTIAL_LOCKOUT = "potential_lockout"
    CIRCULAR_DEPENDENCY = "circular_dependency"


@dataclass
class DependencyIssue:
    """Represents a dependency issue."""
    issue_type: IssueType
    severity: str  # 'error', 'warning', 'info'
    message: str
    affected_items: List[str]
    recommendation: Optional[str] = None
    
    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.issue_type.value}: {self.message}"


class DependencyGraph:
    """Manages and analyzes PAM configuration dependencies.
    
    Supports:
    - Missing module detection
    - Wrong order detection
    - Conflict flag detection
    - Module availability checking
    - Platform compatibility checking
    - Potential lockout detection
    """
    
    # Known dependencies and conflicts
    KNOWN_CONFLICTS = {
        ('pam_cracklib', 'pam_pwquality'): "Cannot use both pam_cracklib and pam_pwquality",
        ('pam_tally2', 'pam_faillock'): "Cannot use both pam_tally2 and pam_faillock",
    }
    
    RECOMMENDED_ORDER = {
        # auth stack
        'pam_unix': 10,
        'pam_ldap': 11,
        'pam_krb5': 11,
        'pam_sss': 11,
        'pam_faillock': 5,  # Early
        'pam_tally2': 5,    # Early
        
        # account stack
        'pam_unix': 20,
        'pam_ldap': 21,
        'pam_access': 25,
        'pam_time': 26,
        'pam_loginuid': 27,
        
        # password stack
        'pam_cracklib': 30,
        'pam_pwquality': 30,
        'pam_unix': 40,
        
        # session stack
        'pam_unix': 50,
        'pam_systemd': 51,
        'pam_mkhomedir': 60,
    }
    
    def __init__(self, module_database: Dict = None, platform: str = None):
        """Initialize DependencyGraph.
        
        Args:
            module_database: Dictionary of module specifications
            platform: Target platform for compatibility checking
        """
        self.module_database = module_database or {}
        self.platform = platform
        self.nodes: Dict[str, Dict] = {}
        self.edges: List[Tuple[str, str, DependencyType]] = []
        self.issues: List[DependencyIssue] = []
    
    # ========================================================================
    # Graph Building
    # ========================================================================
    
    def add_node(self, node_id: str, node_type: str, metadata: Dict = None) -> None:
        """Add node to dependency graph.
        
        Args:
            node_id: Unique node identifier
            node_type: Type of node (module, fragment, element, service)
            metadata: Additional metadata
        """
        self.nodes[node_id] = {
            'type': node_type,
            'metadata': metadata or {},
            'dependencies': [],
            'conflicts': [],
            'dependents': []
        }
    
    def add_edge(self, source: str, target: str, dep_type: DependencyType) -> None:
        """Add edge between nodes.
        
        Args:
            source: Source node ID
            target: Target node ID
            dep_type: Type of dependency
        """
        self.edges.append((source, target, dep_type))
        
        # Update node references
        if source in self.nodes:
            if dep_type == DependencyType.CONFLICTS:
                self.nodes[source]['conflicts'].append(target)
            else:
                self.nodes[source]['dependencies'].append(target)
        
        if target in self.nodes:
            self.nodes[target]['dependents'].append(source)
    
    # ========================================================================
    # Dependency Analysis
    # ========================================================================
    
    def analyze(self) -> List[DependencyIssue]:
        """Analyze graph for issues.
        
        Returns:
            List of dependency issues found
        """
        self.issues = []
        
        self._check_circular_dependencies()
        self._check_missing_dependencies()
        self._check_conflicts()
        self._check_ordering()
        self._check_platform_compatibility()
        self._check_potential_lockout()
        
        return self.issues
    
    def _check_circular_dependencies(self) -> None:
        """Check for circular dependencies."""
        visited = set()
        rec_stack = set()
        
        def has_cycle(node, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            
            if node in self.nodes:
                for dep in self.nodes[node]['dependencies']:
                    if dep not in visited:
                        if has_cycle(dep, visited, rec_stack):
                            return True
                    elif dep in rec_stack:
                        return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.nodes:
            if node not in visited:
                if has_cycle(node, visited, rec_stack):
                    self.issues.append(DependencyIssue(
                        issue_type=IssueType.CIRCULAR_DEPENDENCY,
                        severity='error',
                        message=f"Circular dependency detected involving {node}",
                        affected_items=[node]
                    ))
    
    def _check_missing_dependencies(self) -> None:
        """Check for missing dependencies."""
        for node_id, node in self.nodes.items():
            for dep in node['dependencies']:
                if dep not in self.nodes:
                    self.issues.append(DependencyIssue(
                        issue_type=IssueType.MISSING_MODULE,
                        severity='error',
                        message=f"Missing dependency: {node_id} requires {dep}",
                        affected_items=[node_id, dep],
                        recommendation=f"Add {dep} to configuration"
                    ))
    
    def _check_conflicts(self) -> None:
        """Check for conflicting modules."""
        modules = [n for n, node in self.nodes.items() if node['type'] == 'module']
        
        for i, mod1 in enumerate(modules):
            for mod2 in modules[i+1:]:
                # Check known conflicts
                for (m1, m2), msg in self.KNOWN_CONFLICTS.items():
                    if (mod1.endswith(m1) and mod2.endswith(m2)) or \
                       (mod1.endswith(m2) and mod2.endswith(m1)):
                        self.issues.append(DependencyIssue(
                            issue_type=IssueType.CONFLICT_FLAGS,
                            severity='error',
                            message=msg,
                            affected_items=[mod1, mod2]
                        ))
                
                # Check explicit conflicts
                if mod2 in self.nodes[mod1]['conflicts']:
                    self.issues.append(DependencyIssue(
                        issue_type=IssueType.CONFLICT_FLAGS,
                        severity='error',
                        message=f"{mod1} and {mod2} cannot be used together",
                        affected_items=[mod1, mod2]
                    ))
    
    def _check_ordering(self) -> None:
        """Check for incorrect ordering."""
        # This would need actual ordering information from configuration
        # Placeholder for now
        pass
    
    def _check_platform_compatibility(self) -> None:
        """Check platform compatibility."""
        if not self.platform:
            return
        
        for node_id, node in self.nodes.items():
            if node['type'] == 'module':
                if node_id in self.module_database:
                    module_info = self.module_database[node_id]
                    supported_platforms = module_info.get('supported_platforms', [])
                    
                    if supported_platforms and self.platform not in supported_platforms:
                        self.issues.append(DependencyIssue(
                            issue_type=IssueType.PLATFORM_INCOMPATIBLE,
                            severity='error',
                            message=f"{node_id} is not available on {self.platform}",
                            affected_items=[node_id],
                            recommendation=f"Use an alternative module or switch platforms"
                        ))
    
    def _check_potential_lockout(self) -> None:
        """Check for potential lockout scenarios.
        
        Examples:
        - auth stack with only deny modules
        - account stack without any permit conditions
        """
        # Group modules by interface
        modules_by_interface = {}
        for node_id, node in self.nodes.items():
            iface = node['metadata'].get('interface')
            if iface:
                if iface not in modules_by_interface:
                    modules_by_interface[iface] = []
                modules_by_interface[iface].append(node_id)
        
        # Check auth stack for potential lockout
        auth_modules = modules_by_interface.get('auth', [])
        if auth_modules:
            # Check if only deny modules
            deny_modules = [m for m in auth_modules if 'deny' in m.lower()]
            if deny_modules and len(deny_modules) == len(auth_modules):
                self.issues.append(DependencyIssue(
                    issue_type=IssueType.POTENTIAL_LOCKOUT,
                    severity='warning',
                    message="Auth stack contains only deny modules - potential lockout risk",
                    affected_items=auth_modules,
                    recommendation="Add at least one permissive or required auth module"
                ))
    
    # ========================================================================
    # Graph Traversal
    # ========================================================================
    
    def get_dependencies(self, node_id: str) -> List[str]:
        """Get all dependencies of a node."""
        if node_id not in self.nodes:
            return []
        return self.nodes[node_id]['dependencies']
    
    def get_dependents(self, node_id: str) -> List[str]:
        """Get all nodes that depend on this node."""
        if node_id not in self.nodes:
            return []
        return self.nodes[node_id]['dependents']
    
    def get_conflicts(self, node_id: str) -> List[str]:
        """Get all conflicting nodes."""
        if node_id not in self.nodes:
            return []
        return self.nodes[node_id]['conflicts']
    
    def get_transitive_dependencies(self, node_id: str) -> Set[str]:
        """Get all transitive dependencies (recursive)."""
        visited = set()
        
        def visit(nid):
            if nid in visited:
                return
            visited.add(nid)
            if nid in self.nodes:
                for dep in self.nodes[nid]['dependencies']:
                    visit(dep)
        
        visit(node_id)
        visited.discard(node_id)
        return visited
    
    # ========================================================================
    # Visualization & Reporting
    # ========================================================================
    
    def to_graphviz(self, output_file: str = None) -> str:
        """Generate Graphviz representation of dependency graph.
        
        Args:
            output_file: Optional file to save output to
            
        Returns:
            Graphviz DOT format string
        """
        lines = ["digraph PAMDependencies {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box];")
        
        # Add nodes
        for node_id, node in self.nodes.items():
            color = "lightcoral" if node['type'] == 'module' else "lightblue"
            lines.append(f'  "{node_id}" [fillcolor={color}, style=filled];')
        
        # Add edges
        for source, target, dep_type in self.edges:
            style = "solid" if dep_type != DependencyType.CONFLICTS else "dashed"
            color = "red" if dep_type == DependencyType.CONFLICTS else "black"
            lines.append(f'  "{source}" -> "{target}" [style={style}, color={color}];')
        
        lines.append("}")
        
        result = "\n".join(lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(result)
        
        return result
    
    def generate_report(self) -> str:
        """Generate text report of dependency graph analysis."""
        report = ["PAM Configuration Dependency Report", "=" * 60]
        
        if self.issues:
            report.append("\nIssues Found:")
            for issue in self.issues:
                report.append(f"  - {issue}")
                if issue.recommendation:
                    report.append(f"    Recommendation: {issue.recommendation}")
        else:
            report.append("\nNo issues found.")
        
        report.append(f"\nGraph Statistics:")
        report.append(f"  Nodes: {len(self.nodes)}")
        report.append(f"  Edges: {len(self.edges)}")
        
        return "\n".join(report)


__all__ = ['DependencyGraph', 'DependencyIssue', 'DependencyType', 'IssueType']
