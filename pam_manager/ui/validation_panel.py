"""Validation panel widget for displaying PAM validation results - Phase 4."""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import logging


logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation result level."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationMessage:
    """Single validation message."""
    level: ValidationLevel
    stage: str  # syntax, semantic, platform, module_specific, security
    message: str
    line_number: Optional[int] = None
    module_name: Optional[str] = None
    service_name: Optional[str] = None
    details: Dict[str, any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class ValidationPanel:
    """Validation results panel controller."""
    
    def __init__(self):
        """Initialize validation panel."""
        self.messages: List[ValidationMessage] = []
        self.current_service: Optional[str] = None
        self.validation_in_progress = False
    
    def add_message(self, message: ValidationMessage) -> None:
        """
        Add validation message.
        
        Args:
            message: Validation message to add
        """
        self.messages.append(message)
        logger.debug(f"Added {message.level.value} message: {message.message}")
    
    def add_validation_result(
        self,
        level: ValidationLevel,
        stage: str,
        message: str,
        line_number: Optional[int] = None,
        module_name: Optional[str] = None,
        service_name: Optional[str] = None,
    ) -> None:
        """
        Add validation result.
        
        Args:
            level: Validation level
            stage: Validation stage
            message: Message text
            line_number: Optional line number
            module_name: Optional module name
            service_name: Optional service name
        """
        msg = ValidationMessage(
            level=level,
            stage=stage,
            message=message,
            line_number=line_number,
            module_name=module_name,
            service_name=service_name,
        )
        self.add_message(msg)
    
    def clear_messages(self) -> None:
        """Clear all messages."""
        self.messages = []
        logger.debug("Cleared validation messages")
    
    def get_messages_by_level(self, level: ValidationLevel) -> List[ValidationMessage]:
        """
        Get messages filtered by level.
        
        Args:
            level: Validation level to filter
            
        Returns:
            List[ValidationMessage]: Filtered messages
        """
        return [msg for msg in self.messages if msg.level == level]
    
    def get_messages_by_stage(self, stage: str) -> List[ValidationMessage]:
        """
        Get messages filtered by stage.
        
        Args:
            stage: Validation stage
            
        Returns:
            List[ValidationMessage]: Filtered messages
        """
        return [msg for msg in self.messages if msg.stage == stage]
    
    def get_messages_by_service(self, service: str) -> List[ValidationMessage]:
        """
        Get messages for a service.
        
        Args:
            service: Service name
            
        Returns:
            List[ValidationMessage]: Messages for service
        """
        return [msg for msg in self.messages if msg.service_name == service]
    
    def get_summary(self) -> Dict[str, int]:
        """
        Get validation summary.
        
        Returns:
            Dict[str, int]: Level -> count
        """
        summary = {
            "info": len(self.get_messages_by_level(ValidationLevel.INFO)),
            "warning": len(self.get_messages_by_level(ValidationLevel.WARNING)),
            "error": len(self.get_messages_by_level(ValidationLevel.ERROR)),
            "critical": len(self.get_messages_by_level(ValidationLevel.CRITICAL)),
            "total": len(self.messages),
        }
        return summary
    
    def has_errors(self) -> bool:
        """Check if there are errors or critical issues."""
        return bool(
            self.get_messages_by_level(ValidationLevel.ERROR) or
            self.get_messages_by_level(ValidationLevel.CRITICAL)
        )
    
    def has_warnings(self) -> bool:
        """Check if there are warnings."""
        return bool(self.get_messages_by_level(ValidationLevel.WARNING))
    
    def get_formatted_message(self, message: ValidationMessage) -> str:
        """
        Get formatted message for display.
        
        Args:
            message: Validation message
            
        Returns:
            str: Formatted message
        """
        parts = [
            f"[{message.level.value.upper()}]",
            f"[{message.stage}]",
        ]
        
        if message.line_number:
            parts.append(f"(line {message.line_number})")
        
        if message.module_name:
            parts.append(f"({message.module_name})")
        
        if message.service_name:
            parts.append(f"({message.service_name})")
        
        parts.append(message.message)
        
        return " ".join(parts)
    
    def get_all_formatted_messages(self) -> str:
        """
        Get all messages formatted for display.
        
        Returns:
            str: All formatted messages
        """
        if not self.messages:
            return "No validation messages"
        
        return "\n".join(
            self.get_formatted_message(msg) for msg in self.messages
        )
    
    def export_as_json(self) -> Dict[str, any]:
        """
        Export validation results as JSON-compatible dict.
        
        Returns:
            Dict[str, any]: JSON-compatible validation results
        """
        return {
            "summary": self.get_summary(),
            "messages": [
                {
                    "level": msg.level.value,
                    "stage": msg.stage,
                    "message": msg.message,
                    "line_number": msg.line_number,
                    "module_name": msg.module_name,
                    "service_name": msg.service_name,
                    "details": msg.details,
                }
                for msg in self.messages
            ]
        }
    
    def get_analysis_report(self) -> str:
        """
        Generate analysis report.
        
        Returns:
            str: Analysis report
        """
        summary = self.get_summary()
        
        report = [
            "╔════════════════════════════════════════╗",
            "║     PAM CONFIGURATION ANALYSIS         ║",
            "╚════════════════════════════════════════╝",
            "",
            f"Total Issues: {summary['total']}",
            f"  ✓ Info: {summary['info']}",
            f"  ⚠ Warnings: {summary['warning']}",
            f"  ✗ Errors: {summary['error']}",
            f"  ✗✗ Critical: {summary['critical']}",
            "",
        ]
        
        # Add message details
        for level in [ValidationLevel.CRITICAL, ValidationLevel.ERROR, ValidationLevel.WARNING, ValidationLevel.INFO]:
            messages = self.get_messages_by_level(level)
            if messages:
                report.append(f"{level.value.upper()}S ({len(messages)}):")
                for msg in messages:
                    report.append(f"  • {self.get_formatted_message(msg)}")
                report.append("")
        
        return "\n".join(report)


class RealTimeValidator:
    """Real-time validation during configuration."""
    
    def __init__(self, panel: ValidationPanel):
        """
        Initialize real-time validator.
        
        Args:
            panel: Validation panel to update
        """
        self.panel = panel
        self.callback = None
    
    def set_validation_callback(self, callback) -> None:
        """
        Set callback for validation updates.
        
        Args:
            callback: Callable to invoke on validation updates
        """
        self.callback = callback
    
    def validate_service_line(
        self,
        line: str,
        service: str,
        line_number: int,
    ) -> bool:
        """
        Validate a single PAM configuration line.
        
        Args:
            line: Configuration line
            service: Service name
            line_number: Line number
            
        Returns:
            bool: True if valid
        """
        # Basic syntax check
        if not line or line.startswith("#"):
            return True
        
        parts = line.split()
        if len(parts) < 3:
            self.panel.add_validation_result(
                ValidationLevel.ERROR,
                "syntax",
                "Line has insufficient parts (need: facility control module)",
                line_number,
                service_name=service,
            )
            if self.callback:
                self.callback(self.panel)
            return False
        
        facility, control, module = parts[0], parts[1], parts[2]
        
        # Validate facility
        valid_facilities = ["auth", "account", "session", "password"]
        if facility not in valid_facilities:
            self.panel.add_validation_result(
                ValidationLevel.ERROR,
                "syntax",
                f"Invalid facility '{facility}' (valid: {', '.join(valid_facilities)})",
                line_number,
                service_name=service,
            )
            if self.callback:
                self.callback(self.panel)
            return False
        
        # Validate control flag
        valid_controls = ["required", "requisite", "sufficient", "optional"]
        if control not in valid_controls:
            self.panel.add_validation_result(
                ValidationLevel.WARNING,
                "syntax",
                f"Unusual control flag '{control}' (typical: {', '.join(valid_controls)})",
                line_number,
                module_name=module,
                service_name=service,
            )
        
        # Validate module path
        if not module.startswith("pam_") and not module.startswith("/"):
            self.panel.add_validation_result(
                ValidationLevel.INFO,
                "syntax",
                f"Module name '{module}' is relative path",
                line_number,
                module_name=module,
                service_name=service,
            )
        
        if self.callback:
            self.callback(self.panel)
        
        return True
