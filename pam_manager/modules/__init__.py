"""Modules package - database and registry."""

from pam_manager.modules.base import PAMModuleInfo
from pam_manager.modules.database import PAM_MODULES
from pam_manager.modules.registry import ModuleRegistry
from pam_manager.modules.json_loader import ModulesJSONLoader, get_modules_loader

__all__ = [
    "PAMModuleInfo",
    "PAM_MODULES",
    "ModuleRegistry",
    "ModulesJSONLoader",
    "get_modules_loader",
]
