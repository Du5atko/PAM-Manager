# PAM Manager - Graphical Configuration Tool

PAM Manager is a comprehensive graphical user interface for managing Pluggable Authentication Modules (PAM) configuration on Linux and FreeBSD systems. It provides a modern, intuitive way to design, validate, and deploy PAM security policies without manual editing of PAM configuration files.

## Overview

The PAM Manager consists of several interconnected components that work together to provide a complete PAM configuration management solution:

- **PAM Modules Database**: Comprehensive catalog of 53+ PAM modules with full documentation
- **Policy Fragments**: Atomic reusable PAM configuration components
- **Policy Elements**: Collections of fragments configured for specific services
- **Service Definitions**: Complete PAM service configurations (login, sshd, sudo, gdm, etc.)
- **Template System**: Pre-built security policy bundles for common use cases
- **Configuration Export**: Generate standard PAM configuration files

## Core Components

### 1. Policy Fragments

A Policy Fragment represents a single PAM module invocation with its configuration. Fragments are the building blocks of PAM policies.

**Key Properties**:
- `id`: Unique identifier (e.g., "pam_unix/auth/standard")
- `module`: PAM module name (e.g., "pam_unix.so")
- `interface`: Interface type - auth, account, session, or password
- `parameters`: Module-specific configuration parameters
- `platform_support`: Platform compatibility matrix (Linux, FreeBSD, etc.)
- `tags`: Classification tags for organization

**Example Fragment**:
```yaml
fragments:
  - id: "pam_unix/auth/standard"
    module: "pam_unix.so"
    interface: "auth"
    parameters:
      nullok: "yes"
      try_first_pass: "yes"
    platform_support:
      Linux: true
      FreeBSD: true
```

See `Fragment.template.md` for detailed fragment specifications.

### 2. Policy Elements

A Policy Element combines one or more Fragments with control flags to define how PAM should process authentication. Elements define the order, conditions, and actions for a group of modules.

**Key Properties**:
- `id`: Unique identifier (e.g., "sshd/auth_1")
- `description`: Human-readable description
- `service_name`: Associated PAM service (e.g., "sshd")
- `fragments`: List of fragment references with control settings

**Fragment Reference Properties**:
- `fragment_ref`: Reference to a Policy Fragment
- `control_flag`: How PAM processes this module - required, requisite, sufficient, optional, include, substack
- `extended_control`: Advanced control syntax for return value mapping

**Example Element**:
```yaml
elements:
  - id: "sshd/auth_1"
    description: "SSH password authentication"
    service_name: "sshd"
    fragments:
      - fragment_ref: "pam_unix/auth/standard"
        control_flag: "required"
        interface: "auth"
```

See `Element.template.md` for detailed element specifications.

### 3. Service Definitions

A Service Definition assembles multiple Elements into a complete PAM configuration for a specific service.

**Key Properties**:
- `id`: Service name (e.g., "sshd", "login", "sudo")
- `elements`: List of element IDs to use
- `description`: Service description
- `tags`: Classification tags

**Example Service**:
```yaml
services:
  - id: "sshd"
    description: "SSH login service"
    elements:
      - "sshd/auth_1"
      - "sshd/account_1"
      - "sshd/session_1"
```

See `Service.template.md` for detailed service specifications.

### 4. Generic Templates

Generic Templates are pre-built security policy bundles that can be deployed as-is or customized. Each template includes metadata, documentation, and installation scripts.

**Template Categories**:
- **MFA/Authentication**: YubiKey, TOTP, OTP, Smart Card integration
- **Access Control**: Time-based restrictions, concurrent session limits
- **Session Management**: Private namespace isolation, MOTD display
- **Security**: Intruder lockout, password quality, faillock

See `Generic.template.md` for available templates and deployment procedures.

## Module Specifications

The PAM Manager includes a comprehensive database of PAM modules with their specifications, parameters, return values, and usage examples. Each module is documented in JSON format with:

- Module description and purpose
- Supported interfaces (auth, account, session, password)
- Parameters and their meanings
- Return value handling
- Platform support matrix
- Common use cases
- Security considerations

See `Module.md` for the complete module reference and JSON schema.

## Configuration Storage

PAM Manager stores all configuration in YAML and JSON formats:

- **pam-config.yaml**: Human-readable YAML format
- **pam-config.json**: JSON format for programmatic access
- **Atomic persistence**: Fragments, Elements, and Services are atomically saved
- **Transaction logging**: All operations are logged for audit trails

## Workflow

1. **Design Policies**: Define Fragments and Elements using the GUI
2. **Organize Services**: Assemble Elements into Service Definitions
3. **Validate Configuration**: Check for conflicts and compatibility
4. **Export Configuration**: Generate PAM configuration files
5. **Deploy**: Install files to /etc/pam.d or user directory
6. **Audit**: Review transaction logs for compliance

## Integration Points

### Import from System Configuration
- Parse existing /etc/pam.d files
- Auto-generate Fragments from system configuration
- Create Elements and Services from imports
- Preserve original control flags and parameters

### Export to PAM Configuration
- Generate PAM-compliant configuration files
- Support standard control flags and extended syntax
- Preserve all parameters and settings
- Create backup of existing files before deployment

### Template Deployment
- Install pre-built security policies
- Manage template versioning
- Support platform-specific customization
- Track template deployment history

## Security Considerations

### Principle of Least Privilege
- Only enable required authentication methods
- Use 'required' and 'requisite' flags judiciously
- Apply time-based and resource restrictions
- Implement proper audit logging

### Policy Validation
- Validate control flag sequences
- Check for conflicting requirements
- Verify module compatibility
- Test on non-production systems first

### Compliance
- Document policy rationale
- Maintain audit trails
- Support compliance frameworks (NIST, PCI-DSS, HIPAA)
- Regular policy review and updates

## Data Structure

### Fragment Storage Format
Each fragment contains:
- Unique identifier
- Module name and interface
- Configuration parameters
- Platform support metadata
- Creation and modification timestamps

### Element Storage Format
Each element contains:
- Unique identifier
- Service association
- Fragment references with control settings
- Return value mapping for extended syntax
- Timestamps

### Service Storage Format
Each service contains:
- Service identifier
- Associated elements list
- Description and tags
- Metadata

## Command Line Usage

```bash
# View system information
python PAMManager.py

# Enable debug output
python PAMManager.py --debug

# Display help
python PAMManager.py --help
python PAMManager.py -h

# Import from system
# (GUI: Service Definition tab -> Import Services)

# Export to files
# (GUI: Service Definition tab -> Export Services)
```

## Supported Platforms

- **Linux**: Debian, Ubuntu, Fedora, RHEL, Rocky, AlmaLinux, CentOS, Alpine, Arch
- **BSD**: FreeBSD, OpenBSD, NetBSD
- **Desktop Environments**: GNOME, KDE, XFCE

## Version History

### v2.0.0 - Optimized Window Sizing
- Window geometry constraints for better UX
- Tab bar optimization for all 8 tabs
- Improved layout management

### v15.0.0 - Enhanced Utility Features
- Action-based statistics (Import, Save, Export)
- Improved backup/restore mechanism
- Adapter pattern support

### v14.0.0 - Qt4/Qt5 Compatibility
- PyQt5 with Qt4 fallback support
- Enhanced Help System
- Comprehensive debug logging

## Documentation Files

- `Readme.md`: This file - General overview
- `Module.md`: PAM module specification and reference
- `Fragment.template.md`: Fragment definition schema and examples
- `Element.template.md`: Element definition schema and examples
- `Service.template.md`: Service definition schema and examples
- `Generic.template.md`: Pre-built template bundles

## Getting Started

1. Launch PAM Manager: `python PAMManager.py`
2. Review "System Information" tab for platform details
3. Browse "PAM Modules" tab to understand available modules
4. Use "Service Definition" tab to import existing services
5. Create new Fragments in "Policy Fragment" tab
6. Assemble Elements in "Policy Element" tab
7. Define Services in "Service Definition" tab
8. Export configuration when ready

## Support and Resources

- Inline help in GUI (hover over labels)
- Debug output available with `--debug` flag
- PAM Linux Manual: `man pam`, `man pam.conf`
- Module documentation in Module.md
- Template examples in Generic.template.md

## License

PAM Manager is provided under open source license. See LICENSE file for details.

## Contributing

To contribute improvements:
1. Review existing code structure
2. Follow naming conventions for Fragments, Elements, Services
3. Document new modules in pam.modules/ JSON files
4. Test on multiple platforms
5. Submit changes with clear documentation

---

For detailed technical information, see the template documentation files:
- Fragment schema: Fragment.template.md
- Element schema: Element.template.md  
- Service schema: Service.template.md
- Module reference: Module.md
- Template bundles: Generic.template.md
