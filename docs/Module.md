# PAM Module Specification Reference

This document describes the JSON schema for PAM module definitions and the extended PAM control syntax.

## Table of Contents

1. Module JSON Schema
2. PAM Interfaces
3. Control Flags
4. Extended Control Syntax
5. Return Values and Actions
6. Module Database Organization
7. Examples

## Module JSON Schema

Each PAM module in the pam.modules/ directory is defined as a JSON file containing comprehensive module information.

### Root Structure

```json
{
  "name": "pam_unix",
  "description": "Traditional password authentication module",
  "category": "authentication",
  "interfaces": ["auth", "account", "password", "session"],
  "module_path": "/lib/x86_64-linux-gnu/security/pam_unix.so",
  "availability": ["Linux", "FreeBSD"],
  "parameters": {...},
  "return_values": {...},
  "use_cases": [...],
  "security_notes": "...",
  "man_page": "pam_unix(8)"
}
```

### Properties

#### name (string, required)
The name of the PAM module (without .so extension).

Example: `"pam_unix"`

#### description (string, required)
Human-readable description of the module purpose.

Example: `"Traditional password authentication module using system shadow database"`

#### category (string, required)
Module category for organization:
- `"authentication"` - Handle user login and password verification
- `"authorization"` - Control access based on attributes
- `"account"` - Check account/password expiration
- `"session"` - Setup/teardown user environment
- `"password"` - Change passwords and update credentials
- `"mfa"` - Multi-factor authentication methods
- `"audit"` - Security logging and audit

#### interfaces (array of strings)
List of PAM interfaces supported by this module:
- `"auth"` - Authentication interface (login verification)
- `"account"` - Account interface (expiration checks)
- `"session"` - Session interface (environment setup)
- `"password"` - Password interface (password changes)

#### module_path (string)
Full path to the module binary in the filesystem.

Example: `"/lib/x86_64-linux-gnu/security/pam_unix.so"`

#### availability (array of strings)
Platforms where module is available:
- `"Linux"` - Available on Linux systems
- `"FreeBSD"` - Available on FreeBSD
- `"Debian"` - Debian/Ubuntu specific
- `"Fedora"` - Fedora/RHEL specific
- `"Alpine"` - Alpine Linux

#### parameters (object)
Module parameters defined as key-value pairs.

```json
"parameters": {
  "nullok": {
    "type": "flag",
    "default": false,
    "description": "Allow authentication with empty password"
  },
  "try_first_pass": {
    "type": "flag",
    "default": false,
    "description": "Try user-supplied password before prompting"
  },
  "use_authtok": {
    "type": "flag",
    "default": false,
    "description": "Use password from earlier module in stack"
  }
}
```

##### Parameter Structure

Each parameter is an object with:

- `type` (string): `"flag"`, `"string"`, `"integer"`, `"path"`, `"choice"`
- `default` (any): Default value if not specified
- `description` (string): Parameter explanation
- `valid_values` (array): For "choice" type, list of valid values
- `required` (boolean): Whether parameter is mandatory
- `security_level` (string): `"low"`, `"medium"`, `"high"`, `"critical"`

#### return_values (object)
Possible return values and their meanings.

```json
"return_values": {
  "success": "Authentication successful",
  "auth_err": "Authentication failed",
  "user_unknown": "User does not exist",
  "maxtries": "Maximum authentication attempts exceeded"
}
```

#### use_cases (array of objects)
Common deployment scenarios and configurations.

```json
"use_cases": [
  {
    "title": "Standard password authentication",
    "description": "Basic password verification against system database",
    "parameters": {
      "try_first_pass": true,
      "nullok": false
    },
    "control_flags": ["required"],
    "notes": "Most common configuration for login service"
  }
]
```

#### security_notes (string)
Important security considerations when using this module.

Example: `"Ensure pam_unix is not used alone for MFA deployments. Always stack with additional authentication modules for enhanced security."`

#### man_page (string)
Reference to manual page (man 8 pam_module_name).

Example: `"pam_unix(8)"`

## PAM Interfaces

### auth - Authentication Interface

Verifies user identity (password, biometric, OTP, etc.).

**Typical stack order**:
1. Initial authentication (pam_unix, pam_sss, pam_ldap)
2. Secondary authentication (pam_google_authenticator, pam_oath)
3. Late checks (pam_cracklib, pam_pwquality)

**Common modules**:
- pam_unix.so - Local system authentication
- pam_sss.so - System Security Services (LDAP/Kerberos)
- pam_ldap.so - LDAP authentication
- pam_google_authenticator.so - TOTP MFA
- pam_fprintd.so - Fingerprint authentication

### account - Account Interface

Checks account validity, expiration, and access restrictions.

**Typical stack order**:
1. Check account status (pam_unix, pam_sss)
2. Check restrictions (pam_access, pam_faillock)
3. Check expiration (pam_lastlog)

**Common modules**:
- pam_unix.so - System account verification
- pam_sss.so - System Security Services checks
- pam_access.so - /etc/security/access.conf checking
- pam_faillock.so - Failed login tracking
- pam_lastlog.so - Last login time checking

### session - Session Interface

Manages user environment and session lifecycle.

**Typical stack order**:
1. Mount private namespace (pam_namespace)
2. Setup environment (pam_env)
3. Log session start (pam_lastlog)
4. Cleanup on logout (pam_lastlog as optional)

**Common modules**:
- pam_env.so - Set environment variables
- pam_namespace.so - Create private /tmp
- pam_lastlog.so - Log login/logout times
- pam_mkhomedir.so - Create home directory
- pam_limits.so - Set resource limits

### password - Password Interface

Handles password changes and credential updates.

**Typical stack order**:
1. Check password quality (pam_cracklib, pam_pwquality)
2. Update password (pam_unix)
3. Update other backends (pam_sss, pam_ldap)

**Common modules**:
- pam_unix.so - Update system password
- pam_cracklib.so - Password strength checking
- pam_pwquality.so - Password quality checking
- pam_sss.so - Update LDAP/Kerberos password
- pam_pwhistory.so - Prevent password reuse

## Control Flags

Control flags determine how PAM processes module results.

### Standard Control Flags

#### required

Module must succeed for authentication to continue. If module fails, PAM continues processing the stack but marks the overall result as failure.

**Semantics**:
- Success: Noted, continue processing
- Failure: Noted, mark as failed, continue processing
- Return: Failure (unless subsequent "sufficient" succeeds)

**Usage**: Use for modules that must not fail silently
```
auth required pam_unix.so try_first_pass
```

#### requisite

Module must succeed. On failure, PAM terminates immediately with failure.

**Semantics**:
- Success: Noted, continue processing
- Failure: Mark as failed, return immediately (FAIL)
- Return: Failure

**Usage**: Protect against obvious attacks, fail fast
```
auth requisite pam_permit_nohostname.so
```

#### sufficient

If module succeeds and no prior "required" has failed, PAM returns success immediately (no further modules processed).

**Semantics**:
- Success: Return immediately (SUCCESS) if no prior required failures
- Failure: Noted, continue processing
- Return: Success (if no prior failures), else continue

**Usage**: Early exit on successful authentication
```
auth sufficient pam_unix.so use_first_pass
```

#### optional

Module result is usually ignored. Only matters if it is the sole module in the facility.

**Semantics**:
- Success: Noted, continue processing
- Failure: Noted, continue processing
- Return: Based on other modules (or success if alone)

**Usage**: Non-critical checks, information gathering
```
session optional pam_lastlog.so silent
```

#### include

Include configuration from another PAM config file.

**Semantics**:
- Includes all modules from referenced file at this point
- Module/parameter restrictions don't apply to included modules
- Can be used to modularize complex configurations

**Usage**: Organize large configurations
```
auth include common-auth
account include common-account
```

#### substack

Similar to "include" but return values are handled differently.

**Semantics**:
- Includes modules from referenced file
- Substack return treated as module return
- Return value mapping applies to entire stack

**Usage**: Organize with different return semantics
```
auth substack pam_polkit.so
```

### Control Flag Decision Tree

```
1. Check all "required" and "requisite" modules
   - If any requisite fails: FAIL immediately
   - If any required fails: Mark failed, continue

2. Check "sufficient" modules
   - If any sufficient succeeds (and no required failed): SUCCESS immediately

3. If no sufficient succeeded or any required failed:
   - Return FAIL if any required failed
   - Return SUCCESS if no required failures and at least one module succeeded
   - Return FAILURE if no modules succeeded
```

## Extended Control Syntax

Extended control syntax provides fine-grained control over return value handling.

### Syntax

```
auth [return1=action1 return2=action2 ...] pam_module.so params
```

### Return Value Conditions

Return values from modules that can be mapped:

- `success` - Module returned PAM_SUCCESS
- `open_err` - Error opening module
- `symbol_err` - Module symbol not found
- `service_err` - Service error
- `system_err` - System error
- `buf_err` - Memory buffer error
- `perm_denied` - Permission denied
- `auth_err` - Authentication error
- `cred_insufficient` - Insufficient credentials
- `authinfo_unavail` - Auth info not available
- `user_unknown` - User not found
- `maxtries` - Maximum tries exceeded
- `new_authtok_reqd` - New auth token required
- `acct_expired` - Account expired
- `session_err` - Session error
- `cred_unavail` - Credentials unavailable
- `cred_expired` - Credentials expired
- `cred_err` - Credential error
- `no_module_data` - No module data
- `conv_err` - Conversation error
- `authtok_err` - Auth token error
- `authtok_recover_err` - Can't recover auth token
- `authtok_lock_busy` - Auth token locked
- `authtok_disable_aging` - Can't disable aging
- `try_again` - Try again
- `ignore` - Ignore result
- `abort` - Abort
- `authtok_expired` - Auth token expired
- `module_unknown` - Module not found
- `bad_item` - Bad item
- `conv_again` - Conversation again
- `incomplete` - Incomplete
- `default` - All other return values

### Actions

- `ok` - Mark as success, continue processing
- `done` - Terminate immediately as success (if no prior failures)
- `bad` - Mark as failure, continue processing
- `die` - Terminate immediately with failure
- `ignore` - Ignore this return value (continue processing)
- `reset` - Reset state and continue from clean slate

### Examples

**Handle specific failure gracefully**:
```
auth [success=1 default=ignore] pam_google_authenticator.so
auth required pam_unix.so use_authtok
```
Result: If Google Authenticator succeeds, skip pam_unix. Otherwise try pam_unix.

**Require both methods**:
```
auth [success=ok default=die] pam_google_authenticator.so
auth required pam_unix.so use_authtok
```
Result: Both must succeed.

**Try multiple methods**:
```
auth [success=ok default=continue] pam_google_authenticator.so
auth [success=ok default=continue] pam_unix.so
auth required pam_oauth2.so
```
Result: Try each in order, require at least one success plus final oauth2.

## Module Database Organization

### Directory Structure

```
pam.modules/
  pam_unix.json
  pam_sss.json
  pam_ldap.json
  pam_google_authenticator.json
  pam_fprintd.json
  pam_oauth2.json
  pam_access.json
  pam_faillock.json
  ... (53+ module files)
```

### Naming Convention

Module JSON files are named after the module:
- Filename: `pam_modulename.json`
- Matches: `/lib/.../security/pam_modulename.so`

### Module Categories

- **Core**: pam_unix, pam_permit, pam_deny, pam_env
- **LDAP/Directory**: pam_ldap, pam_sss, pam_krb5
- **MFA**: pam_google_authenticator, pam_oath, pam_duo
- **Biometric**: pam_fprintd, pam_face
- **Access Control**: pam_access, pam_faillock, pam_limits
- **Session**: pam_namespace, pam_mkhomedir, pam_lastlog
- **Security**: pam_cracklib, pam_pwquality, pam_pwhistory
- **Network**: pam_http, pam_radius, pam_openvpn

## Examples

### Example 1: Simple SSH Configuration

```json
{
  "name": "pam_unix",
  "description": "Traditional password authentication using system shadow database",
  "category": "authentication",
  "interfaces": ["auth", "account", "password"],
  "module_path": "/lib/x86_64-linux-gnu/security/pam_unix.so",
  "availability": ["Linux", "FreeBSD"],
  "parameters": {
    "nullok": {
      "type": "flag",
      "default": false,
      "description": "Allow empty password"
    },
    "try_first_pass": {
      "type": "flag",
      "default": false,
      "description": "Try user password first"
    },
    "use_first_pass": {
      "type": "flag",
      "default": false,
      "description": "Use password from first module"
    },
    "use_authtok": {
      "type": "flag",
      "default": false,
      "description": "Use token from previous module"
    }
  },
  "return_values": {
    "success": "Authentication successful",
    "auth_err": "Authentication failed",
    "user_unknown": "User not found",
    "maxtries": "Too many login attempts"
  },
  "use_cases": [
    {
      "title": "SSH password authentication",
      "parameters": {
        "try_first_pass": true
      },
      "control_flags": ["required"],
      "notes": "Standard SSH password login"
    }
  ],
  "security_notes": "pam_unix relies on weak password storage. Use with pam_cracklib for password change enforcement.",
  "man_page": "pam_unix(8)"
}
```

### Example 2: MFA Module Configuration

```json
{
  "name": "pam_google_authenticator",
  "description": "Time-based one-time password (TOTP) multi-factor authentication",
  "category": "mfa",
  "interfaces": ["auth"],
  "module_path": "/lib/x86_64-linux-gnu/security/pam_google_authenticator.so",
  "availability": ["Linux", "FreeBSD"],
  "parameters": {
    "secret": {
      "type": "path",
      "default": "~/.google_authenticator",
      "description": "Path to TOTP secret file"
    },
    "window_size": {
      "type": "integer",
      "default": 3,
      "description": "Time window tolerance in 30-second intervals"
    },
    "disallow_reuse": {
      "type": "flag",
      "default": false,
      "description": "Prevent reuse of recent codes"
    },
    "force_otp": {
      "type": "flag",
      "default": false,
      "description": "Require OTP even if recovery codes used"
    }
  },
  "return_values": {
    "success": "OTP code verified",
    "auth_err": "Invalid OTP code",
    "user_unknown": "No TOTP secret found"
  },
  "use_cases": [
    {
      "title": "TOTP as secondary factor",
      "parameters": {
        "window_size": 3,
        "disallow_reuse": true
      },
      "control_flags": ["required"],
      "notes": "Combine with pam_unix for two-factor auth"
    }
  ],
  "security_notes": "Ensure TOTP secrets are protected. Use with hardware security keys for critical accounts.",
  "man_page": "pam_google_authenticator(8)"
}
```

## Best Practices

### Module Stacking

1. **Authentication order matters** - Stack password methods before optional biometric
2. **Use control flags correctly** - Don't overuse "required"
3. **Plan for fallback** - Include alternative auth methods
4. **Test configuration** - Validate with login attempts
5. **Document rationale** - Record why each module is present

### Security Considerations

1. **Least privilege** - Only include necessary modules
2. **Strong defaults** - Use secure parameter values
3. **Rate limiting** - Combine with pam_faillock
4. **Audit logging** - Enable PAM logging for compliance
5. **MFA when critical** - Use for sensitive accounts/systems

### Performance

1. **Avoid network calls in auth** - LDAP can cause delays
2. **Cache results** - Use pam_sss for directory caching
3. **Timeout settings** - Prevent hanging on unavailable services
4. **Profile configurations** - Measure login times

## Compliance

Modules and configurations can be validated against:
- **NIST SP 800-63** - Authentication requirements
- **PCI-DSS** - Multi-factor authentication (requirement 8.3)
- **FIPS 140-2** - Cryptographic module requirements
- **HIPAA** - Access control and audit requirements
- **SOC 2** - Authentication and access control

---

For additional information, see:
- PAM Manual: `man 5 pam.conf`
- Module documentation: `man 8 pam_modulename`
- System PAM configuration: `/etc/pam.d/`
