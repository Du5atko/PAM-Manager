# Policy Element Template Specification

This document describes Policy Elements - the composable building blocks that combine fragments with control logic.

## Overview

A Policy Element is a collection of Policy Fragments assembled with control flags that define how PAM processes them. Elements are the bridge between individual module configurations (Fragments) and complete service definitions (Services).

**Key Concept**: Elements define WHEN and in WHAT ORDER to use fragments (modules), and HOW to handle their results.

## Element Structure

### Root Properties

```yaml
id: "sshd/auth_1"
description: "SSH authentication with password and MFA fallback"
service_name: "sshd"
config_file: null
fragments:
  - fragment_ref: "pam_unix/auth/standard"
    interface: "auth"
    control_flag: "required"
    extended_control: null
    line_type: "module_line"
tags:
  - "ssh"
  - "authentication"
created: "2026-08-16T10:30:00"
modified: "2026-08-16T10:30:00"
```

### Property Definitions

#### id (string, required)

Unique identifier for the element. Used to reference this element from services.

**Naming conventions**:
- Pattern: `{service}/{interface}_{sequence}`
- Examples:
  - `sshd/auth_1`
  - `login/account_2`
  - `sudo/session_3`

**Guidelines**:
- Use lowercase service names
- Use interface name (auth, account, session, password)
- Add sequence number for multiple elements per interface
- Start sequence at 1 for first element of each interface

#### description (string, required)

Human-readable description of what this element does.

**Requirements**:
- Describe the combined behavior of all fragments
- Explain the control flow logic
- Note any special handling or fallbacks
- Include purpose in security context

**Examples**:
- "SSH authentication requiring both Unix password and TOTP OTP"
- "Account expiration and lockout checking for login service"
- "Session setup with private namespace and environment variables"

#### service_name (string, required)

The PAM service this element belongs to.

**Common services**:
- `sshd` - SSH login
- `login` - Console/terminal login
- `sudo` - Sudo privilege elevation
- `gdm` - GNOME Display Manager login
- `lightdm` - LightDM login
- `common-auth` - Shared authentication
- `common-account` - Shared account checking
- `common-session` - Shared session setup

**Format**: Lowercase service identifier

**Validation**: Elements referencing non-standard services should document the service definition.

#### config_file (string, optional)

Original configuration file path (if imported from system).

**Usage**:
- Set when importing from /etc/pam.d
- Tracks source of element
- Used for audit trail
- Set to null for manually created elements

**Example**: `/etc/pam.d/sshd`

#### fragments (array of objects, required)

List of fragment references in order.

**Each fragment reference contains**:
- `fragment_ref` - Reference to a Policy Fragment
- `interface` - Interface type (auth, account, session, password)
- `control_flag` - How PAM processes this module
- `extended_control` - Advanced control syntax (optional)
- `line_type` - Type of line (module_line or directive_include)
- `include_target` - Target for include directives (optional)

**Array order matters**: Fragments are processed in array order by PAM.

**Minimum**: At least one fragment required

**Structure**:
```yaml
fragments:
  - fragment_ref: "pam_unix/auth/standard"
    interface: "auth"
    control_flag: "required"
    extended_control: null
    line_type: "module_line"
    include_target: ""
  - fragment_ref: "pam_google_authenticator/auth/totp-strict"
    interface: "auth"
    control_flag: "required"
    extended_control: null
    line_type: "module_line"
    include_target: ""
```

#### Fragment Reference Properties

##### fragment_ref (string, required)

Reference to a Policy Fragment by ID.

**Format**: Must match exact fragment ID
**Example**: `pam_unix/auth/standard`

**Validation**:
- Fragment must exist in configuration
- Fragment interface must match element fragment interface
- Fragment module must be available on target platform

##### interface (string, required)

PAM interface type.

**Valid values**:
- `auth` - Authentication interface
- `account` - Account/authorization interface
- `session` - Session management interface
- `password` - Password change interface

**Rules**:
- Must match fragment interface
- Defines module category in stack
- Elements typically contain one interface type (or mixed for complex scenarios)

##### control_flag (string, required)

Determines how PAM processes this fragment's result.

**Standard flags**:
- `required` - Module must succeed
- `requisite` - Module must succeed, fail immediately on error
- `sufficient` - If succeeds (and no required failed), skip rest
- `optional` - Result usually ignored
- `include` - Include configuration from file
- `substack` - Include with different return handling

**Selection guide**:
- Use `required` for mandatory authentication methods
- Use `requisite` for fast-fail checks
- Use `sufficient` for early exit on success
- Use `optional` for informational checks
- Use `include`/`substack` for modularization

**See Module.md** for detailed control flag semantics.

##### extended_control (object or null, optional)

Advanced control syntax for fine-grained return value handling.

**Structure**:
```yaml
extended_control:
  success: "ok"
  user_unknown: "ignore"
  auth_err: "die"
  default: "continue"
```

**Keys** (PAM return values):
- Success conditions: `success`
- Failure conditions: `auth_err`, `user_unknown`, `perm_denied`, etc.
- Default: `default` (applies to any unmatched return)

**Values** (actions):
- `ok` - Mark success, continue
- `done` - End successfully (if no prior failures)
- `bad` - Mark failure, continue
- `die` - End with failure immediately
- `ignore` - Ignore result, continue
- `reset` - Reset state, continue

**Usage**:
```yaml
# Skip to next module if OTP not configured
extended_control:
  user_unknown: "ignore"
  success: "ok"
  default: "continue"

# Fail immediately on any error
extended_control:
  default: "die"
```

**Note**: Set to `null` for standard control flag behavior (no extended syntax).

##### line_type (string, required)

Type of PAM configuration line.

**Valid values**:
- `module_line` - Standard PAM module line
- `directive_include` - Include directive

**Default**: `module_line`

**Usage**:
- `module_line`: For normal module invocations
- `directive_include`: For @include directives

##### include_target (string, optional)

Target file for include directives.

**Required if**: `line_type` is `directive_include`

**Format**: Filename or path
**Examples**:
- `common-auth`
- `common-account`
- `/etc/pam.d/common-password`

**Default**: Empty string for module_line

##### include_format (string, optional)

Format of include directive.

**Valid values**:
- `at_include` - Use @include format (modern)
- `include` - Use include format (standard)
- Empty string for module_line

**Usage**:
```yaml
# @include format (preferred)
include_format: "at_include"
line: "@include common-auth"

# include format
include_format: "include"
line: "auth include common-auth"
```

#### tags (array of strings, optional)

Classification tags for organization.

**Predefined tags**:
- By interface: `auth`, `account`, `session`, `password`
- By service: `ssh`, `login`, `sudo`, `desktop`
- By function: `mfa`, `security`, `audit`, `setup`
- By criticality: `critical`, `important`, `optional`

**Usage**:
```yaml
tags:
  - "auth"
  - "ssh"
  - "critical"
  - "mfa"
```

#### created (string, required)

ISO 8601 timestamp when element was created.

**Format**: `YYYY-MM-DDTHH:MM:SS`

**Rules**:
- Set automatically on creation
- Do not manually edit

#### modified (string, required)

ISO 8601 timestamp of last modification.

**Format**: `YYYY-MM-DDTHH:MM:SS`

**Rules**:
- Updated automatically on changes
- Do not manually edit

## Element Types

### Authentication Element

Handles user identity verification.

**Typical interface**: `auth`

**Common fragments**:
- pam_unix/auth/standard
- pam_google_authenticator/auth/totp
- pam_faillock/auth/lockout
- pam_ldap/auth/directory

**Example**:
```yaml
id: "sshd/auth_1"
description: "SSH password authentication with lockout protection"
service_name: "sshd"
fragments:
  - fragment_ref: "pam_faillock/auth/lockout-5attempts"
    control_flag: "required"
    interface: "auth"
  - fragment_ref: "pam_unix/auth/standard"
    control_flag: "required"
    interface: "auth"
```

**Flow**:
1. Check account not locked (faillock)
2. Verify password (unix)
3. If both succeed, user authenticated

### Account Element

Checks account validity and access restrictions.

**Typical interface**: `account`

**Common fragments**:
- pam_unix/account/standard
- pam_access/account/restrictions
- pam_lastlog/account/tracking
- pam_faillock/account/unlock

**Example**:
```yaml
id: "login/account_1"
description: "Account expiration and access control checking"
service_name: "login"
fragments:
  - fragment_ref: "pam_unix/account/standard"
    control_flag: "required"
    interface: "account"
  - fragment_ref: "pam_access/account/restrictions"
    control_flag: "required"
    interface: "account"
```

**Flow**:
1. Check account not expired (unix)
2. Check access restrictions (access)
3. If both pass, account valid

### Session Element

Manages user environment and session lifecycle.

**Typical interface**: `session`

**Common fragments**:
- pam_env/session/standard-vars
- pam_namespace/session/private-tmp
- pam_mkhomedir/session/create-home
- pam_limits/session/resource-limits

**Example**:
```yaml
id: "login/session_1"
description: "Session setup with environment and private namespace"
service_name: "login"
fragments:
  - fragment_ref: "pam_namespace/session/private-tmp"
    control_flag: "required"
    interface: "session"
  - fragment_ref: "pam_env/session/standard-vars"
    control_flag: "required"
    interface: "session"
  - fragment_ref: "pam_limits/session/resource-limits"
    control_flag: "required"
    interface: "session"
```

**Flow**:
1. Create private /tmp namespace
2. Set environment variables
3. Apply resource limits

### Password Element

Handles password changes and updates.

**Typical interface**: `password`

**Common fragments**:
- pam_cracklib/password/strength-check
- pam_unix/password/update-unix
- pam_pwhistory/password/check-history

**Example**:
```yaml
id: "common/password_1"
description: "Password change with quality checking and history"
service_name: "common-password"
fragments:
  - fragment_ref: "pam_cracklib/password/strength-check"
    control_flag: "required"
    interface: "password"
  - fragment_ref: "pam_unix/password/update-unix"
    control_flag: "required"
    interface: "password"
  - fragment_ref: "pam_pwhistory/password/check-history"
    control_flag: "required"
    interface: "password"
```

**Flow**:
1. Check password quality (cracklib)
2. Update system password (unix)
3. Check password history (pwhistory)

## Element Examples

### Example 1: Simple SSH Authentication

```yaml
id: "sshd/auth_1"
description: "SSH authentication with Unix password"
service_name: "sshd"
config_file: null
fragments:
  - fragment_ref: "pam_unix/auth/standard"
    interface: "auth"
    control_flag: "required"
    extended_control: null
    line_type: "module_line"
tags:
  - "auth"
  - "ssh"
  - "authentication"
created: "2026-08-16T10:00:00"
modified: "2026-08-16T10:00:00"
```

### Example 2: MFA Authentication with Fallback

```yaml
id: "sshd/auth_2"
description: "MFA with OTP and password fallback using extended control"
service_name: "sshd"
config_file: null
fragments:
  - fragment_ref: "pam_google_authenticator/auth/totp-strict"
    interface: "auth"
    control_flag: null
    extended_control:
      success: "ok"
      user_unknown: "continue"
      default: "continue"
    line_type: "module_line"
  - fragment_ref: "pam_unix/auth/standard"
    interface: "auth"
    control_flag: "required"
    extended_control: null
    line_type: "module_line"
tags:
  - "auth"
  - "ssh"
  - "mfa"
  - "critical"
created: "2026-08-16T11:00:00"
modified: "2026-08-16T11:00:00"
```

**Flow**:
1. Try TOTP: If successful, done. If user_unknown, try unix. Otherwise continue.
2. Unix password: Must succeed.

### Example 3: Account Checking with Lockout

```yaml
id: "login/account_1"
description: "Account validation with lockout check and expiration"
service_name: "login"
config_file: null
fragments:
  - fragment_ref: "pam_faillock/account/unlock-check"
    interface: "account"
    control_flag: "required"
    extended_control: null
    line_type: "module_line"
  - fragment_ref: "pam_unix/account/expiration-check"
    interface: "account"
    control_flag: "required"
    extended_control: null
    line_type: "module_line"
tags:
  - "account"
  - "login"
  - "security"
created: "2026-08-16T12:00:00"
modified: "2026-08-16T12:00:00"
```

### Example 4: Session with Include Directive

```yaml
id: "common/session_1"
description: "Include common session configuration"
service_name: "common-session"
config_file: null
fragments:
  - fragment_ref: "common-session-noninteractive"
    interface: "session"
    control_flag: "include"
    extended_control: null
    line_type: "directive_include"
    include_target: "common-session-noninteractive"
    include_format: "include"
tags:
  - "session"
  - "shared"
created: "2026-08-16T13:00:00"
modified: "2026-08-16T13:00:00"
```

## Control Flow Logic

### Required + Required
```yaml
fragments:
  - fragment_ref: "auth1"
    control_flag: "required"
  - fragment_ref: "auth2"
    control_flag: "required"
```
**Result**: Both must succeed

### Required + Sufficient
```yaml
fragments:
  - fragment_ref: "auth1"
    control_flag: "required"
  - fragment_ref: "auth2"
    control_flag: "sufficient"
```
**Result**: auth1 must succeed, auth2 can end stack if succeeds

### Optional + Required
```yaml
fragments:
  - fragment_ref: "info"
    control_flag: "optional"
  - fragment_ref: "auth"
    control_flag: "required"
```
**Result**: Info is logged but doesn't affect outcome, auth must succeed

### Requisite (Fast Fail)
```yaml
fragments:
  - fragment_ref: "check"
    control_flag: "requisite"
  - fragment_ref: "auth"
    control_flag: "required"
```
**Result**: Check fails immediately, auth never runs

## Element Validation

When creating or modifying elements:

1. **Fragment existence** - Verify fragment IDs exist
2. **Interface compatibility** - Ensure fragment interfaces match
3. **Control flag validity** - Verify control flags are standard or extended
4. **Return value mapping** - For extended_control, validate return values
5. **Action validity** - Verify actions are valid for extended syntax
6. **Service name** - Verify service exists or document custom service
7. **Ordering** - Consider fragment order and control flags
8. **Logical flow** - Test control flow logic matches intent

## Best Practices

1. **One interface per element** - Don't mix auth/account/session in same element
2. **Clear sequencing** - Use sequence numbers (auth_1, auth_2) logically
3. **Document flow** - Explain control flag logic in description
4. **Test combinations** - Verify all fragment combinations work
5. **Progressive security** - Stack optional checks before required ones
6. **Error handling** - Use extended_control for graceful degradation
7. **Reuse elements** - Reference same element from multiple services when possible
8. **Platform consistency** - Verify all fragments support same platforms
9. **Performance** - Order fast checks before slow network checks
10. **Audit trail** - Keep config_file for imported elements

---

For fragment specifications, see Fragment.template.md.
For service definitions using elements, see Service.template.md.
For module information, see Module.md.
For complete configuration examples, see Generic.template.md.
