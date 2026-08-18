# Policy Service Template Specification

This document describes Policy Services - complete PAM configuration definitions for specific system services.

## Overview

A Policy Service assembles multiple Policy Elements into a complete PAM configuration for a specific system service (sshd, login, sudo, etc.). Services define the complete authentication and authorization flow for a given service.

**Key Concept**: Services combine all necessary elements (auth, account, session, password) to create a complete, deployable PAM configuration.

**Hierarchy**:
```
Service (e.g., "sshd")
  ├── Elements (auth_1, auth_2, ...)
  │   └── Fragments (pam_unix, pam_google_authenticator, ...)
  ├── Elements (account_1, account_2, ...)
  └── Elements (session_1, ...)
```

## Service Structure

### Root Properties

```yaml
id: "sshd"
description: "SSH login service with strong MFA"
elements:
  - "sshd/auth_1"
  - "sshd/account_1"
  - "sshd/session_1"
tags:
  - "ssh"
  - "network"
  - "critical"
  - "mfa"
created: "2026-08-16T10:00:00"
modified: "2026-08-16T10:00:00"
```

### Property Definitions

#### id (string, required)

Unique identifier for the service - typically the PAM service name.

**Naming conventions**:
- Lowercase letters and hyphens
- Match system PAM service names when possible
- Examples: `sshd`, `login`, `sudo`, `gdm`, `common-auth`

**Standard services**:
- `sshd` - SSH daemon
- `login` - Console/terminal login
- `sudo` - Sudo command
- `su` - Su command
- `gdm` - GNOME Display Manager
- `lightdm` - LightDM display manager
- `common-auth` - Shared authentication (included by others)
- `common-account` - Shared account checks
- `common-session` - Shared session setup
- `common-password` - Shared password operations

**Custom services**: Use descriptive names for non-standard services

#### description (string, required)

Comprehensive description of the service configuration.

**Should include**:
- Service purpose and usage
- Authentication flow summary
- Special features or requirements
- Security considerations
- Deployment notes

**Example**: "SSH login service with MFA using TOTP and password, including account lockout protection and private session namespace"

#### elements (array of strings, required)

Ordered list of element IDs to include in this service.

**Requirements**:
- Array must not be empty
- Each element ID must exist in configuration
- Elements must be from compatible interfaces
- Order matters - PAM processes in list order

**Typical order**:
1. Auth elements (interface: auth)
2. Account elements (interface: account)
3. Session elements (interface: session)
4. Password elements (interface: password) - if needed

**Example**:
```yaml
elements:
  - "sshd/auth_1"        # First auth module
  - "sshd/auth_2"        # Second auth module (MFA)
  - "sshd/account_1"     # Account checking
  - "sshd/session_1"     # Session setup
```

**Rules for ordering**:
- Group by interface type (auth, account, session, password)
- Within same interface, order by requirements
- Fast checks before slow checks
- Critical checks before optional checks

#### tags (array of strings, optional)

Classification and discovery tags.

**Predefined tags**:
- By type: `network`, `local`, `desktop`, `system`
- By security: `high-security`, `mfa`, `audit`, `critical`
- By function: `authentication`, `authorization`, `session`
- By platform: `ssh`, `login`, `sudo`, `desktop`

**Usage**:
```yaml
tags:
  - "ssh"
  - "network"
  - "critical"
  - "mfa"
```

**Guidelines**:
- Use 3-5 tags per service
- Choose tags that enable filtering
- Be consistent with other services

#### created (string, required)

ISO 8601 timestamp when service was created.

**Format**: `YYYY-MM-DDTHH:MM:SS`

**Rules**:
- Set automatically on creation
- Do not manually edit
- Enables audit trail

#### modified (string, required)

ISO 8601 timestamp of last modification.

**Format**: `YYYY-MM-DDTHH:MM:SS`

**Rules**:
- Updated automatically on changes
- Do not manually edit
- Tracks configuration evolution

## Service Types and Patterns

### Authentication Service (SSH/Remote)

Focuses on secure remote access with MFA.

**Typical elements**:
- Authentication (password + OTP)
- Account checking (lockout, expiration)
- Session setup (environment, limits)

**Example**:
```yaml
id: "sshd"
description: "SSH login with strong MFA and account controls"
elements:
  - "sshd/auth_1"        # Faillock check
  - "sshd/auth_2"        # Unix password required
  - "sshd/auth_3"        # TOTP OTP required
  - "sshd/account_1"     # Account expiration
  - "sshd/account_2"     # Access restrictions
  - "sshd/session_1"     # Environment setup
tags:
  - "ssh"
  - "network"
  - "critical"
  - "mfa"
created: "2026-08-16T10:00:00"
modified: "2026-08-16T10:00:00"
```

### Desktop Service (Login/Display Manager)

Focuses on local desktop user experience while maintaining security.

**Typical elements**:
- Authentication (password, biometric)
- Account checking
- Session setup (Xsession, environment)
- Password management

**Example**:
```yaml
id: "gdm"
description: "GNOME display manager with password and fingerprint support"
elements:
  - "gdm/auth_1"         # Fingerprint (optional)
  - "gdm/auth_2"         # Unix password (fallback)
  - "gdm/account_1"      # Account checking
  - "gdm/session_1"      # Desktop environment setup
tags:
  - "desktop"
  - "gnome"
  - "local"
  - "biometric"
created: "2026-08-16T11:00:00"
modified: "2026-08-16T11:00:00"
```

### Privilege Escalation Service (Sudo)

Focuses on secure privilege elevation with audit.

**Typical elements**:
- Authentication (re-authenticate)
- Session setup (audit logging)

**Example**:
```yaml
id: "sudo"
description: "Sudo privilege escalation with password re-authentication and audit logging"
elements:
  - "sudo/auth_1"        # Re-authenticate user
  - "sudo/auth_2"        # Check against sudoers
  - "sudo/session_1"     # Audit logging
tags:
  - "sudo"
  - "privilege"
  - "audit"
  - "critical"
created: "2026-08-16T12:00:00"
modified: "2026-08-16T12:00:00"
```

### Shared/Include Service

Provides common configuration for other services to include.

**Typical elements**:
- Often uses include directives
- Provides default configuration

**Example**:
```yaml
id: "common-auth"
description: "Shared authentication module for inclusion by other services"
elements:
  - "common/auth_1"      # Unix password
  - "common/auth_2"      # Kerberos fallback
tags:
  - "shared"
  - "authentication"
  - "common"
created: "2026-08-16T13:00:00"
modified: "2026-08-16T13:00:00"
```

## Service Configuration Examples

### Example 1: Basic SSH Configuration

```yaml
id: "sshd"
description: "Standard SSH login with Unix password authentication"
elements:
  - "sshd/auth_1"        # Unix password (required)
  - "sshd/account_1"     # Account checking (required)
  - "sshd/session_1"     # Session setup (required)
tags:
  - "ssh"
  - "network"
  - "basic"
created: "2026-08-16T10:00:00"
modified: "2026-08-16T10:00:00"
```

**Generated PAM configuration**:
```
auth required pam_unix.so try_first_pass nullok=no
account required pam_unix.so
account required pam_faillock.so
session required pam_limits.so
session required pam_env.so
```

### Example 2: SSH with MFA

```yaml
id: "sshd-mfa"
description: "SSH with mandatory two-factor authentication using OTP and password"
elements:
  - "sshd/auth_faillock"        # Lockout protection
  - "sshd/auth_unix"            # Password required
  - "sshd/auth_totp"            # OTP required
  - "sshd/account_unix"         # Account checking
  - "sshd/account_access"       # Access restrictions
  - "sshd/session_limits"       # Resource limits
  - "sshd/session_namespace"    # Private /tmp
tags:
  - "ssh"
  - "network"
  - "critical"
  - "mfa"
  - "high-security"
created: "2026-08-16T11:00:00"
modified: "2026-08-16T11:00:00"
```

**Generated configuration**:
```
auth required pam_faillock.so preauth silent deny=5 unlock_time=1800
auth required pam_unix.so try_first_pass nullok=no
auth required pam_google_authenticator.so window_size=1 disallow_reuse=yes
account required pam_faillock.so
account required pam_unix.so
account required pam_access.so
session required pam_limits.so
session required pam_namespace.so
```

### Example 3: Console Login with Session Setup

```yaml
id: "login"
description: "Console login with authentication, account checks, and desktop environment setup"
elements:
  - "login/auth_faillock"       # Faillock preauth check
  - "login/auth_unix"           # Unix password
  - "login/auth_fingerprint"    # Fingerprint (optional)
  - "login/account_unix"        # Account checking
  - "login/account_lastlog"     # Last login info
  - "login/session_limits"      # Set resource limits
  - "login/session_env"         # Set environment
  - "login/session_namespace"   # Private namespace
tags:
  - "login"
  - "local"
  - "console"
  - "desktop"
created: "2026-08-16T12:00:00"
modified: "2026-08-16T12:00:00"
```

### Example 4: Sudo Configuration

```yaml
id: "sudo"
description: "Sudo privilege elevation with user re-authentication and audit logging"
elements:
  - "sudo/auth_unix"            # Re-authenticate user
  - "sudo/account_unix"         # Verify sudo access
  - "sudo/session_audit"        # Log sudo usage
tags:
  - "sudo"
  - "privilege"
  - "audit"
  - "critical"
created: "2026-08-16T13:00:00"
modified: "2026-08-16T13:00:00"
```

### Example 5: Shared Authentication Configuration

```yaml
id: "common-auth"
description: "Shared authentication module providing Unix and LDAP authentication"
elements:
  - "common/auth_unix"          # Local Unix password
  - "common/auth_ldap"          # LDAP directory fallback
tags:
  - "shared"
  - "authentication"
  - "directory"
created: "2026-08-16T14:00:00"
modified: "2026-08-16T14:00:00"
```

## Service Composition Guidelines

### Interface Coverage

**Complete service typically includes**:

1. **auth interface** (at least one)
   - Primary authentication method
   - Optional secondary methods
   - Fallback options

2. **account interface** (optional but recommended)
   - Account validity checks
   - Expiration checks
   - Access control checks

3. **session interface** (optional)
   - Environment setup
   - Resource limit setting
   - Audit logging

4. **password interface** (optional, if service allows password changes)
   - Password quality checks
   - Password update
   - History validation

### Ordering Strategies

**Fast-to-slow ordering**:
- Local checks before network checks
- In-memory before disk I/O
- Disk I/O before network

**Critical-to-optional ordering**:
- Required checks first
- Requisite before required
- Optional last

**User experience ordering**:
- Likely success first (fewer prompts)
- Fallback methods after primary

### Control Flag Patterns

**Standard pattern** (most common):
```yaml
elements:
  - element1  # required
  - element2  # required
  - element3  # required
```
Result: All must succeed

**Fallback pattern**:
```yaml
elements:
  - element_primary      # sufficient
  - element_fallback     # required
```
Result: Primary succeeds = done. Otherwise fallback required

**Optional info pattern**:
```yaml
elements:
  - element_info         # optional
  - element_auth         # required
```
Result: Info logged but doesn't affect outcome

**Multi-factor pattern**:
```yaml
elements:
  - element_factor1      # required
  - element_factor2      # required
  - element_factor3      # required
```
Result: All factors must succeed

## Service Validation

When creating or modifying services:

1. **Element existence** - Verify all referenced elements exist
2. **Interface coherence** - Ensure elements from different interfaces don't conflict
3. **Control flow** - Verify control flags create intended logic
4. **Element order** - Check elements are in logical order
5. **Platform support** - Verify all fragments support target platforms
6. **Security review** - Ensure proper security level for service type
7. **Testing** - Test authentication flow with real logins
8. **Compatibility** - Check compatibility with system services

## Deployment Considerations

### Pre-Deployment Checklist

- [ ] All referenced elements exist
- [ ] All fragments exist and are available on platform
- [ ] Control flow logic tested
- [ ] Service description complete
- [ ] Tags appropriate for filtering
- [ ] Backup of existing PAM configuration made
- [ ] Test account available for validation
- [ ] Fallback access method documented

### Deployment Steps

1. Export service configuration to PAM format
2. Validate syntax with pam-auth-update (Debian) or similar
3. Backup existing /etc/pam.d/service
4. Copy new configuration to /etc/pam.d/service
5. Test with standard login attempts
6. Test with edge cases (locked account, expired password, etc.)
7. Verify audit logging
8. Monitor for issues
9. Document configuration rationale

### Rollback Procedures

1. Keep backup of original configuration
2. Document changes made
3. Have test account with sudo access
4. Test rollback procedure
5. Keep clear rollback instructions

## Service Dependencies

Some services depend on others via include directives.

**Example dependency chain**:
```
sshd -> common-auth -> unix, ldap
     -> common-account -> unix, access
     -> common-session -> limits, env, namespace
```

**Considerations**:
- Verify included services exist
- Avoid circular dependencies
- Document inclusion chain
- Test complete chain

## Best Practices

1. **Clear naming** - Use standard service names when possible
2. **Complete configuration** - Include all relevant interfaces
3. **Security-first** - Use "required" for security-critical modules
4. **User experience** - Balance security with usability
5. **Documentation** - Provide clear descriptions
6. **Modularity** - Reuse elements across services
7. **Testing** - Validate before deployment
8. **Monitoring** - Track configuration changes
9. **Backward compatibility** - Consider legacy systems
10. **Regular review** - Update configurations as needed

## Common Service Definitions

### SSH (sshd)
- auth: unix + faillock + optional OTP
- account: unix + access
- session: limits + env

### Login Console (login)
- auth: unix + optional biometric
- account: unix + lastlog
- session: limits + env + namespace

### Sudo
- auth: unix (re-authenticate)
- account: unix
- session: audit logging

### GNOME Display Manager (gdm)
- auth: optional biometric + unix
- account: unix
- session: gnome-keyring setup

### Common Shared (common-auth)
- auth: unix + optional ldap/kerberos
- account: unix
- session: none (handled by including service)

---

For element specifications, see Element.template.md.
For fragment specifications, see Fragment.template.md.
For module information, see Module.md.
For pre-built templates, see Generic.template.md.
For deployment procedures, see Readme.md.
