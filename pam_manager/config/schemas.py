"""Configuration schema definitions for PAM Manager."""

# JSON Schema definitions for all repository documents

SCHEMA_CUSTOM_PAM = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Custom PAM Configuration",
    "description": "Declarative PAM configuration repository document",
    "version": "1.0",
    "type": "object",
    "properties": {
        "schema_version": {
            "type": "string",
            "description": "Schema version (semantic versioning)",
            "pattern": "^\\d+\\.\\d+$",
            "default": "1.0"
        },
        "application_version": {
            "type": "string",
            "description": "Minimum application version required",
            "pattern": "^\\d+\\.\\d+\\.\\d+$"
        },
        "repository_version": {
            "type": "string",
            "description": "Repository version identifier",
            "pattern": "^\\d+\\.\\d+$"
        },
        "metadata": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "author": {"type": "string"},
                "created": {"type": "string", "format": "date-time"},
                "modified": {"type": "string", "format": "date-time"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["name"]
        },
        "services": {
            "type": "array",
            "description": "PAM service configurations",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Service identifier (e.g., 'common-auth')"
                    },
                    "description": {"type": "string"},
                    "platforms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Supported platforms (DEBIAN, UBUNTU, FEDORA, etc.)"
                    },
                    "fragments": {
                        "type": "array",
                        "description": "Policy fragments for this service",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ref": {
                                    "type": "string",
                                    "description": "Reference to policy fragment"
                                },
                                "interface": {
                                    "enum": ["auth", "account", "password", "session"]
                                },
                                "order": {
                                    "type": "integer",
                                    "minimum": 0
                                }
                            },
                            "required": ["ref", "interface"]
                        }
                    }
                },
                "required": ["name", "platforms", "fragments"]
            }
        },
        "policy_fragments": {
            "type": "array",
            "description": "Reusable policy fragments",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Fragment identifier"
                    },
                    "description": {"type": "string"},
                    "control": {
                        "enum": ["required", "requisite", "sufficient", "optional"]
                    },
                    "module": {"type": "string"},
                    "parameters": {
                        "type": "object",
                        "additionalProperties": {"type": "string"}
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fragment IDs this depends on"
                    },
                    "conflicts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fragment IDs this conflicts with"
                    },
                    "platforms": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["id", "control", "module"]
            }
        },
        "dependencies": {
            "type": "array",
            "description": "Package dependencies by platform",
            "items": {
                "type": "object",
                "properties": {
                    "package": {"type": "string"},
                    "platforms": {
                        "type": "object",
                        "additionalProperties": {"type": "string"}
                    }
                },
                "required": ["package", "platforms"]
            }
        },
        "renderers": {
            "type": "array",
            "description": "Rendering configurations",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["pam.d", "pam.conf", "other"]},
                    "target_path": {"type": "string"},
                    "format": {"enum": ["standard", "custom"]},
                    "backup": {"type": "boolean", "default": True}
                },
                "required": ["name", "type", "target_path"]
            }
        }
    },
    "required": ["schema_version", "metadata", "services"]
}

SCHEMA_POLICY_FRAGMENTS = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Policy Fragments Schema",
    "description": "Reusable PAM policy fragments",
    "type": "object",
    "properties": {
        "schema_version": {
            "type": "string",
            "pattern": "^\\d+\\.\\d+$"
        },
        "fragments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "category": {
                        "enum": ["authentication", "account", "session", "password"]
                    },
                    "control": {
                        "enum": ["required", "requisite", "sufficient", "optional"]
                    },
                    "module": {"type": "string"},
                    "parameters": {
                        "type": "object",
                        "additionalProperties": {"type": "string"}
                    },
                    "description": {"type": "string"},
                    "security_level": {
                        "enum": ["low", "medium", "high", "maximum"]
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["id", "category", "control", "module"]
            }
        }
    },
    "required": ["schema_version", "fragments"]
}

SCHEMA_SERVICES = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Services Schema",
    "description": "PAM service definitions",
    "type": "object",
    "properties": {
        "schema_version": {"type": "string", "pattern": "^\\d+\\.\\d+$"},
        "services": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "platforms": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "fragments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ref": {"type": "string"},
                                "interface": {
                                    "enum": ["auth", "account", "password", "session"]
                                },
                                "order": {"type": "integer"}
                            }
                        }
                    }
                },
                "required": ["name", "fragments"]
            }
        }
    },
    "required": ["schema_version", "services"]
}

SCHEMA_DEPENDENCY_GRAPH = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Dependency Graph Schema",
    "description": "Fragment dependencies and compatibility",
    "type": "object",
    "properties": {
        "schema_version": {"type": "string", "pattern": "^\\d+\\.\\d+$"},
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "type": {"enum": ["fragment", "service", "renderer"]},
                    "version": {"type": "string"}
                },
                "required": ["id", "type"]
            }
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "from": {"type": "string"},
                    "to": {"type": "string"},
                    "type": {"enum": ["depends_on", "conflicts_with", "references"]},
                    "required": {"type": "boolean", "default": True}
                },
                "required": ["from", "to", "type"]
            }
        }
    },
    "required": ["schema_version", "nodes", "edges"]
}

SCHEMA_METADATA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Metadata Schema",
    "description": "Repository metadata and compatibility",
    "type": "object",
    "properties": {
        "schema_version": {"type": "string", "pattern": "^\\d+\\.\\d+$"},
        "application_version": {"type": "string"},
        "supported_schemas": {
            "type": "array",
            "items": {"type": "string"}
        },
        "platforms": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "version_min": {"type": "string"},
                    "version_max": {"type": "string"},
                    "supported": {"type": "boolean"}
                }
            }
        },
        "features": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "available": {"type": "boolean"},
                    "requires_version": {"type": "string"}
                }
            }
        }
    },
    "required": ["schema_version", "application_version"]
}

SCHEMA_VALIDATION = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Validation Report Schema",
    "description": "Configuration validation results",
    "type": "object",
    "properties": {
        "schema_version": {"type": "string", "pattern": "^\\d+\\.\\d+$"},
        "timestamp": {"type": "string", "format": "date-time"},
        "valid": {"type": "boolean"},
        "errors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "enum": ["schema", "reference", "semantic", "compatibility"]
                    },
                    "severity": {
                        "enum": ["error", "warning", "info"]
                    },
                    "message": {"type": "string"},
                    "location": {"type": "string"},
                    "context": {"type": "object"}
                }
            }
        },
        "warnings": {
            "type": "array",
            "items": {"type": "string"}
        },
        "statistics": {
            "type": "object",
            "properties": {
                "services": {"type": "integer"},
                "fragments": {"type": "integer"},
                "dependencies": {"type": "integer"},
                "errors": {"type": "integer"},
                "warnings": {"type": "integer"}
            }
        }
    },
    "required": ["schema_version", "timestamp", "valid"]
}
