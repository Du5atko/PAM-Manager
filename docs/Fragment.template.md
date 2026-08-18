# Policy Fragment Template Specification

This document describes Policy Fragments - the atomic building blocks of PAM policies.

## Overview

A Policy Fragment represents a single PAM module invocation with its configuration. Fragments encapsulate a module name, interface type, and parameters, making them reusable across different PAM services.

**Key Concept**: Fragments define WHAT module to use and HOW to configure it. Elements define WHEN and in WHAT ORDER to use them.

## Fragment Structure

### Root Properties

```yaml
id: "pam_unix/auth/standard"
description: "Standard Unix password authentication"
module: "pam_unix.so"
interface: "auth"
parameters:
  nullok: "yes"
  try_first_pass: "yes"
parameter_help:
  nullok: "Allow login with empty password"
  try_first_pass: "Use password entered in previous module"
platform_support:
  Linux: true
  FreeBSD: true
  Alpine: false
tags:
  - "authentication"
  - "password"
  - "system"
created: "2026-08-16T10:30:00"
modified: "2026-08-16T10:30:00"
```

### Property Definitions

#### id (string, required)

Unique identifier for the fragment. Used to reference this fragment from elements.

**Naming conventions**:
- Pattern: `{module}/{interface}/{variant}`
- Examples:
  - `pam_unix/auth/standard`
  - `pam_google_authenticator/auth/totp-strict`
  - `pam_faillock/auth/lockout-5min`

**Guidelines**:
- Use lowercase with hyphens for readability
- Include interface in name for clarity
- Add variant suffix for different configurations
- Make names self-documenting

#### description (string, required)

Human-readable description of what this fragment does.

**Requirements**:
- One sentence preferred (can be longer for complex modules)
- Describe the functional behavior
- Explain why this configuration exists
- Include any caveats or limitations

**Examples**:
- "Standard Unix password authentication via shadow database"
- "TOTP-based MFA with 30-second time window and reuse protection"
- "Account lockout after 5 failed attempts, 30 minute lockout duration"

#### module (string, required)

The PAM module name (without .so extension).

**Format**: `pam_modulename`

**Examples**:
- `pam_unix`
- `pam_google_authenticator`
- `pam_faillock`
- `pam_access`

**Validation**:
- Must match a module in pam.modules/ directory
- .so extension must not be included
- Must be the actual module filename

#### interface (string, required)

The PAM interface this fragment uses.

**Valid values**:
- `auth` - Authentication interface
- `account` - Account/authorization interface
- `session` - Session management interface
- `password` - Password change interface

**Rules**:
- Must match an interface supported by the module
- Elements referencing this fragment must use compatible interfaces
- One interface per fragment

#### parameters (object, optional)

Module configuration parameters as key-value pairs.

**Structure**:
```yaml
parameters:
  param_name: "value"
  flag_param: "yes"
  numeric_param: "5"
  path_param: "/path/to/file"
```

**Types**:
- **String values**: Quoted or unquoted text
- **Boolean flags**: `yes`, `no`, `true`, `false`
- **Numeric values**: Integer or float
- **Paths**: Absolute or relative file/directory paths

**Special cases**:
- Empty parameters dict `{}` for modules with no configuration
- Parameters are module-specific (see Module.md for each module)

**Examples**:
```yaml
# pam_unix parameters
parameters:
  nullok: "yes"
  try_first_pass: "yes"

# pam_faillock parameters
parameters:
  deny: "5"
  unlock_time: "1800"

# pam_google_authenticator parameters
parameters:
  window_size: "3"
  disallow_reuse: "yes"
```

#### parameter_help (object, optional)

Documentation for each parameter.

**Structure**:
```yaml
parameter_help:
  param_name: "Description of what this parameter does"
  another_param: "Explanation of parameter behavior"
```

**Content**:
- One sentence or short paragraph per parameter
- Explain functional impact on module behavior
- Note security implications if relevant
- Reference valid values for choice parameters

**Example**:
```yaml
parameter_help:
  nullok: "Allow authentication with empty password. Security risk - disable for production."
  try_first_pass: "Attempt using password entered by user before prompting."
  use_first_pass: "Requires password from previous authentication module in stack."
```

#### platform_support (object, required)

Supported platforms for this fragment.

**Structure**:
```yaml
platform_support:
  Linux: true
  FreeBSD: true
  Alpine: false
```

**Supported platforms**:
- `Linux` - Generic Linux support
- `FreeBSD` - FreeBSD systems
- `Debian` - Debian/Ubuntu specific
- `Fedora` - Fedora/RHEL/CentOS specific
- `Alpine` - Alpine Linux
- `Arch` - Arch/Manjaro
- `OpenBSD` - OpenBSD systems
- `NetBSD` - NetBSD systems

**Rules**:
- At least one platform must be true
- Set to false if module not available on platform
- Can include multiple platform specifications
- Affects fragment deployment validation

**Example**:
```yaml
platform_support:
  Linux: true        # Available on all Linux
  Debian: true       # Specifically available on Debian
  Fedora: false      # Not in Fedora repositories
  FreeBSD: true      # Also works on FreeBSD
```

#### tags (array of strings, optional)

Classification tags for organizing and searching fragments.

**Predefined tags**:
- **By function**: `authentication`, `authorization`, `session`, `password`
- **By category**: `mfa`, `biometric`, `network`, `local`, `ldap`, `kerberos`
- **By security level**: `high-security`, `medium-security`, `legacy`
- **By deployment**: `recommended`, `experimental`, `deprecated`
- **By use case**: `ssh`, `login`, `sudo`, `desktop`

**Usage**:
```yaml
tags:
  - "authentication"
  - "password"
  - "ssh"
  - "recommended"
```

**Guidelines**:
- Use 2-5 tags per fragment
- Use predefined tags when available
- Create new tags for specialized use cases
- Enable filtering and discovery

#### created (string, required)

ISO 8601 timestamp when fragment was created.

**Format**: `YYYY-MM-DDTHH:MM:SS`

**Example**: `"2026-08-16T10:30:00"`

**Rules**:
- Set automatically on fragment creation
- Should not be manually edited
- Enables audit trail

#### modified (string, required)

ISO 8601 timestamp of last modification.

**Format**: `YYYY-MM-DDTHH:MM:SS`

**Example**: `"2026-08-16T14:45:30"`

**Rules**:
- Updated automatically on any change
- Should not be manually edited
- Enables change tracking

## Fragment Lifecycle

### Creation

1. Determine module and interface
2. Research module parameters from documentation
3. Test parameter values in non-production
4. Document parameters and behavior
5. Create fragment with proper ID naming
6. Tag appropriately for discovery

### Usage

1. Fragment is referenced from Policy Elements
2. Element defines control flag and order
3. Element is used in Service Definition
4. Service definition generates PAM configuration
5. Configuration is deployed to /etc/pam.d

### Modification

1. Update parameters based on deployment feedback
2. Update description to document changes
3. Automatic timestamp update on save
4. Review impact on all referencing elements
5. Retest in affected services

### Deprecation

1. Keep fragment but mark as deprecated in tags
2. Document reason in description
3. Point to replacement fragment in comments
4. Don't delete - maintain backward compatibility

## Fragment Examples

### Example 1: Standard Unix Authentication

```yaml
id: "pam_unix/auth/standard"
description: "Standard Unix password authentication using system shadow database"
module: "pam_unix"
interface: "auth"
parameters:
  nullok: "no"
  try_first_pass: "yes"
  use_first_pass: "no"
parameter_help:
  nullok: "Do NOT allow empty passwords"
  try_first_pass: "Use user-entered password before prompting"
  use_first_pass: "Require password from stacked module"
platform_support:
  Linux: true
  FreeBSD: true
tags:
  - "authentication"
  - "password"
  - "system"
  - "recommended"
created: "2026-08-16T10:00:00"
modified: "2026-08-16T10:00:00"
```

### Example 2: TOTP Multi-Factor Authentication

```yaml
id: "pam_google_authenticator/auth/totp-strict"
description: "Time-based OTP (TOTP) authentication with reuse protection and narrow time window"
module: "pam_google_authenticator"
interface: "auth"
parameters:
  window_size: "1"
  disallow_reuse: "yes"
  force_otp: "no"
parameter_help:
  window_size: "Only accept codes from current 30-second window (strict)"
  disallow_reuse: "Prevent use of any code that has already been used"
  force_otp: "Allow fallback to recovery codes if OTP fails"
platform_support:
  Linux: true
  FreeBSD: false
  Alpine: false
tags:
  - "authentication"
  - "mfa"
  - "totp"
  - "high-security"
created: "2026-08-16T11:00:00"
modified: "2026-08-16T11:00:00"
```

### Example 3: Account Lockout Protection

```yaml
id: "pam_faillock/auth/lockout-5attempts"
description: "Automatic account lockout after 5 failed login attempts for 30 minutes"
module: "pam_faillock"
interface: "auth"
parameters:
  deny: "5"
  unlock_time: "1800"
  fail_interval: "900"
  silent: "yes"
parameter_help:
  deny: "Number of failed attempts before lockout (5)"
  unlock_time: "Lockout duration in seconds (30 minutes)"
  fail_interval: "Time window for counting failures (15 minutes)"
  silent: "Do not display lockout message"
platform_support:
  Linux: true
  Fedora: true
  Debian: true
  FreeBSD: false
tags:
  - "authorization"
  - "security"
  - "attack-prevention"
  - "recommended"
created: "2026-08-16T12:00:00"
modified: "2026-08-16T12:00:00"
```

### Example 4: LDAP Authentication

```yaml
id: "pam_ldap/auth/directory-fallback"
description: "LDAP authentication with automatic fallback to local password if LDAP unavailable"
module: "pam_ldap"
interface: "auth"
parameters:
  use_first_pass: "no"
  try_first_pass: "yes"
  host: "ldap.example.com"
  port: "389"
  timeout: "5"
parameter_help:
  use_first_pass: "Do not require password from earlier module"
  try_first_pass: "Use user-entered password before prompting"
  host: "LDAP server hostname or IP"
  port: "LDAP server port (389 for cleartext, 636 for SSL)"
  timeout: "Connection timeout in seconds"
platform_support:
  Linux: true
  Debian: true
  Fedora: true
  FreeBSD: true
tags:
  - "authentication"
  - "ldap"
  - "directory"
  - "network"
  - "enterprise"
created: "2026-08-16T13:00:00"
modified: "2026-08-16T13:00:00"
```

### Example 5: Environment Setup

```yaml
id: "pam_env/session/standard-vars"
description: "Set standard environment variables for user session from /etc/environment and user files"
module: "pam_env"
interface: "session"
parameters:
  readenv: "1"
parameter_help:
  readenv: "Read /etc/security/pam_env.conf (1=yes, 0=no)"
platform_support:
  Linux: true
  FreeBSD: true
tags:
  - "session"
  - "environment"
  - "system"
  - "recommended"
created: "2026-08-16T14:00:00"
modified: "2026-08-16T14:00:00"
```

## Fragment Reusability

### Good Practices

1. **Parameterize variations** - Create fragments with parameters instead of copies
2. **Clear documentation** - Make parameters and behavior obvious
3. **Reasonable defaults** - Use conservative security settings
4. **Platform compatibility** - Ensure platform_support is accurate
5. **Semantic naming** - Make fragment ID self-explanatory

### Patterns

**Variant pattern**: Create variations for different security levels
```
pam_faillock/auth/lockout-3attempts      (high-security)
pam_faillock/auth/lockout-5attempts      (medium-security)
pam_faillock/auth/lockout-10attempts     (low-security)
```

**Configuration pattern**: Parameterize rather than duplicate
```
# Good: One fragment with parameters
pam_faillock/auth/configurable
parameters:
  deny: "5"  (can be changed)

# Bad: Multiple fragments with same module
pam_faillock/auth/strict
pam_faillock/auth/normal
pam_faillock/auth/lenient
```

## Fragment Validation

When creating or modifying fragments:

1. **Module existence** - Verify module is in pam.modules/
2. **Interface compatibility** - Check module supports interface
3. **Parameter validity** - Verify parameters are valid for module
4. **Platform availability** - Ensure module available on specified platforms
5. **Consistency** - Check for duplicate or conflicting fragments
6. **Documentation** - Ensure clear description and parameter help

## Integration with Elements

Elements reference fragments by ID:

```yaml
elements:
  - id: "sshd/auth_1"
    fragments:
      - fragment_ref: "pam_unix/auth/standard"      # References fragment
        control_flag: "required"
        interface: "auth"
```

Fragment and element interfaces must match:
- Fragment interface: Defines which interface type
- Element fragment_ref: Must specify same interface
- Validation: System checks compatibility

## Best Practices

1. **One module per fragment** - Don't try to stack in fragments
2. **Clear variant names** - Use suffixes like -strict, -standard, -permissive
3. **Document security** - Explain security implications of parameters
4. **Platform clarity** - Only mark platforms you've tested
5. **Reuse existing** - Check for similar fragments before creating new
6. **Version control** - Track changes through modified timestamp
7. **Parameter validation** - Test all parameter values before production
8. **Compatibility testing** - Verify on supported platforms
9. **Complete documentation** - Help others understand and reuse
10. **Organize with tags** - Enable effective fragment discovery

---

For information about modules and their parameters, see Module.md.
For information about using fragments in elements, see Element.template.md.
For complete configuration examples, see Service.template.md and Generic.template.md.
