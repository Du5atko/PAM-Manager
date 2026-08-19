# PAM Module Fragment Templates Catalog

**Version:** 1.0.0  
**Created:** 2026-08-16  
**Location:** `/home/ghost/scripty/PAM-config/pam.modules/Fragment.Templates/`

---

## 📋 Fragment Overview

Individual fragment templates extracted from the 12 PAM policy bundles. Each fragment represents configuration for a single PAM module.

**Total Fragments:** 15 (one unique module per fragment)

---

## 🔐 Available Fragments

### Authentication Modules

#### 1. **pam_unix-basic** - Standard Unix Authentication
```
Module: pam_unix
Interface: auth, account, password, session
Security Level: HIGH
Used in bundles: 01, 02, 08, 11, 12
```
- Traditional /etc/passwd, /etc/shadow authentication
- Foundation for most PAM configurations
- Supports SHA512 encryption
- Parameters: sha512, shadow, try_first_pass

#### 2. **pam_u2f-yubikey** - YubiKey U2F Authentication
```
Module: pam_u2f
Interface: auth
Security Level: HIGH
Used in bundles: 01, 02, 03
```
- FIDO/U2F authentication with YubiKey hardware tokens
- Per-user (~/.config/Yubico/u2f_keys) or central (/etc/u2f_mappings) configuration
- Parameters: authfile, nouserok, openasuser

#### 3. **pam_succeed_if-conditional** - Conditional User Checks
```
Module: pam_succeed_if
Interface: auth, account
Security Level: MEDIUM
Used in bundles: 03, 10
```
- Branch authentication based on username or group membership
- Used with pam_deny for exclusive access rules
- Parameters: user, notingroup, quiet

#### 4. **pam_deny-denial** - Explicit Denial
```
Module: pam_deny
Interface: auth, account
Security Level: HIGH
Used in bundles: 03
```
- Always denies access (no parameters)
- Used as safety net in authentication flow
- Typical usage: after pam_succeed_if to ensure secure fallthrough

#### 5. **pam_oath-otp** - One-Time Password Authentication
```
Module: pam_oath
Interface: auth
Security Level: CRITICAL
Used in bundles: 11, 12
```
- HOTP/TOTP two-factor authentication
- Works with Google Authenticator, Microsoft Authenticator, Aegis, FreeOTP
- Users authenticate with password + 6-digit code
- Parameters: usersfile, window

#### 6. **pam_pkcs11-smartcard** - Smart Card Authentication
```
Module: pam_pkcs11
Interface: auth
Security Level: CRITICAL
Used in bundles: 12
```
- X.509 certificate-based authentication via smart card
- Requires PKCS#11 middleware and card reader hardware
- Highest security factor available
- Parameters: pkcs11_module, config_file

---

### Session & Configuration Modules

#### 7. **pam_namespace-isolation** - Private Mount Namespace
```
Module: pam_namespace
Interface: session
Security Level: HIGH
Used in bundles: 05
```
- Creates isolated /tmp and /var/tmp per user session
- Each user gets private temporary directory space
- Prevents access to other users' temporary files
- Requires Linux 3.8+ (namespace support)
- Parameters: conffile, debug

#### 8. **pam_motd-display** - Message of the Day
```
Module: pam_motd
Interface: session
Security Level: LOW
Used in bundles: 04
```
- Display system Message of the Day at login
- Standard method for informing users
- Often combined with pam_exec for dynamic messages
- Parameters: motd, noupdate

#### 9. **pam_exec-command** - External Command Execution
```
Module: pam_exec
Interface: auth, session, account
Security Level: MEDIUM
Used in bundles: 04
```
- Execute external scripts during PAM processing
- Flexible for custom authentication/session logic
- Used with pam_motd for per-user messages
- Parameters: command, env_file

#### 10. **pam_env-variables** - Environment Variables
```
Module: pam_env
Interface: session
Security Level: LOW
Used in bundles: 09
```
- Set environment variables based on login context
- Enables detection of login origin (local vs remote)
- Available in shell scripts as $VARIABLE_NAME
- Parameters: conffile, readenv

#### 11. **pam_umask-permissions** - File Permission Masks
```
Module: pam_umask
Interface: session
Security Level: MEDIUM
Used in bundles: 10
```
- Set file creation permissions based on group membership
- Different umask for developers (0002) vs regular users (0022)
- Enables team collaboration without permission issues
- Usually combined with pam_succeed_if
- Parameters: umask, umask_min

---

### Access Control & Resource Modules

#### 12. **pam_time-access** - Time-Based Access Control
```
Module: pam_time
Interface: account
Security Level: MEDIUM
Used in bundles: 06
```
- Restrict user logins to specific days and time windows
- Enforces business hours, shift-based access, contractor access
- Configuration: /etc/security/time.conf
- Format: service;user;tty;day-of-week HH:MM-HH:MM
- Parameters: conffile

#### 13. **pam_limits-resource** - Resource Limits
```
Module: pam_limits
Interface: session
Security Level: MEDIUM
Used in bundles: 07
```
- Limit system resources per user
- Controls: concurrent logins, processes, open files, memory
- Prevents fork bombs and resource exhaustion
- Configuration: /etc/security/limits.conf
- Parameters: conffile

#### 14. **pam_faillock-lockout** - Intruder Lockout
```
Module: pam_faillock
Interface: auth
Security Level: CRITICAL
Used in bundles: 08
```
- Lock account after N failed authentication attempts
- Protects against brute force attacks
- Default: 5 failures → 20 minute lockout
- Tracks failures in /var/run/faillock/
- Parameters: preauth, authfail, authsucc, deny, fail_interval, unlock_time

---

## 📊 Fragment Statistics

### By Security Level

| Level | Fragments | Modules |
|-------|-----------|---------|
| CRITICAL | 3 | pam_oath, pam_pkcs11, pam_faillock |
| HIGH | 4 | pam_unix, pam_u2f, pam_namespace, pam_deny |
| MEDIUM | 5 | pam_succeed_if, pam_umask, pam_time, pam_limits, pam_exec |
| LOW | 2 | pam_motd, pam_env |

### By Interface

| Interface | Fragments | Modules |
|-----------|-----------|---------|
| auth | 6 | pam_unix, pam_u2f, pam_succeed_if, pam_deny, pam_oath, pam_pkcs11 |
| session | 6 | pam_namespace, pam_motd, pam_exec, pam_env, pam_umask, pam_limits |
| account | 4 | pam_unix, pam_succeed_if, pam_deny, pam_time |
| password | 1 | pam_unix |

### By Category

| Category | Fragments | Modules |
|----------|-----------|---------|
| Authentication | 6 | pam_unix, pam_u2f, pam_oath, pam_pkcs11, pam_succeed_if, pam_deny |
| Session/Configuration | 4 | pam_namespace, pam_motd, pam_exec, pam_env |
| Resource/Access Control | 3 | pam_umask, pam_time, pam_limits |
| Security/Attack Prevention | 2 | pam_faillock, pam_namespace |

---

## 🔧 Fragment Template Structure

Each fragment JSON contains:

```json
{
  "id": "Human-readable name",
  "description": "Short description",
  "module": "pam_module_name",
  "interface": "auth|session|account|password",
  "parameters": {
    "param_name": "param_description"
  },
  "parameter_help": {
    "param_name": "Detailed parameter explanation"
  },
  "platform_support": {
    "debian_ubuntu": "package_name",
    "fedora_rhel": "package_name",
    "alpine": "package_name",
    "arch": "package_name"
  },
  "tags": ["tag1", "tag2"],
  "bundle_source": ["bundle-id"],
  "pam_stack_examples": ["example_pam_config"],
  "security_level": "low|medium|high|critical",
  "notes": "Additional information"
}
```

---

## 🎯 Usage by Scenario

### Security-First (Government/Finance)

Use fragments:
1. **pam_faillock-lockout** (CRITICAL) - Attack prevention
2. **pam_oath-otp** (CRITICAL) - 2FA
3. **pam_unix-basic** (HIGH) - Foundation
4. **pam_pkcs11-smartcard** (CRITICAL) - Local auth only
5. **pam_limits-resource** (MEDIUM) - Resource control
6. **pam_namespace-isolation** (HIGH) - Session isolation

### Enterprise (Mid-Size)

Use fragments:
1. **pam_unix-basic** (HIGH) - Password auth
2. **pam_u2f-yubikey** (HIGH) - Centralized MFA
3. **pam_faillock-lockout** (CRITICAL) - Attack prevention
4. **pam_namespace-isolation** (HIGH) - Multi-user isolation
5. **pam_time-access** (MEDIUM) - Business hours
6. **pam_limits-resource** (MEDIUM) - Resource control

### Development Team

Use fragments:
1. **pam_unix-basic** (HIGH) - Password auth
2. **pam_u2f-yubikey** (HIGH) - Basic MFA
3. **pam_umask-permissions** (MEDIUM) - Collaborative umask
4. **pam_namespace-isolation** (HIGH) - File isolation
5. **pam_env-variables** (LOW) - Login type detection
6. **pam_motd-display** (LOW) - Team communication

### Web Server (Public-Facing)

Use fragments:
1. **pam_unix-basic** (HIGH) - Local admin auth
2. **pam_namespace-isolation** (HIGH) - File isolation
3. **pam_faillock-lockout** (CRITICAL) - Attack prevention
4. **pam_limits-resource** (MEDIUM) - DoS prevention
5. **pam_time-access** (MEDIUM) - Admin-hours only

---

## 📂 File Organization

```
pam.modules/Fragment.Templates/
├── fragment.pam_unix-basic.json
├── fragment.pam_u2f-yubikey.json
├── fragment.pam_succeed_if-conditional.json
├── fragment.pam_deny-denial.json
├── fragment.pam_oath-otp.json
├── fragment.pam_pkcs11-smartcard.json
├── fragment.pam_namespace-isolation.json
├── fragment.pam_motd-display.json
├── fragment.pam_exec-command.json
├── fragment.pam_env-variables.json
├── fragment.pam_umask-permissions.json
├── fragment.pam_time-access.json
├── fragment.pam_limits-resource.json
├── fragment.pam_faillock-lockout.json
├── template.Minimum password lenght.json (existing)
└── [This file]
```

---

## ✅ Quality Assurance

Each fragment includes:
- ✅ Complete parameter documentation
- ✅ Platform support information
- ✅ PAM stack examples
- ✅ Practical usage notes
- ✅ Security level designation
- ✅ Bundle source tracking
- ✅ Help text for each parameter

---

## 🔗 Relationship to Bundles

Fragments are extracted from bundles:

| Bundle | Fragments Used |
|--------|-----------------|
| 01-yubikey-basic | pam_unix, pam_u2f |
| 02-yubikey-central | pam_unix, pam_u2f |
| 03-yubikey-rescue | pam_succeed_if, pam_deny, pam_u2f |
| 04-motd-userspecific | pam_motd, pam_exec |
| 05-private-namespace | pam_namespace |
| 06-time-restrictions | pam_time |
| 07-concurrent-login-limits | pam_limits |
| 08-intruder-lockout | pam_faillock, pam_unix |
| 09-environment-login-type | pam_env |
| 10-umask-by-group | pam_succeed_if, pam_umask |
| 11-mfa-otp-hotp | pam_unix, pam_oath |
| 12-mfa-cert-otp | pam_unix, pam_pkcs11, pam_oath |

---

## 🎓 Fragment Combinations

### Basic Authentication Stack
```
auth required pam_unix.so sha512 shadow
```

### Two-Factor Authentication (YubiKey)
```
auth required pam_unix.so
auth required pam_u2f.so authfile=/etc/u2f_mappings
```

### Two-Factor Authentication (OTP)
```
auth required pam_unix.so
auth required pam_oath.so usersfile=/etc/users.oath window=10
```

### Three-Factor Authentication (Certificate + OTP)
```
auth required pam_unix.so
auth required pam_pkcs11.so
auth required pam_oath.so usersfile=/etc/users.oath window=10
```

### Secure Session
```
session required pam_namespace.so
session required pam_limits.so
session optional pam_env.so
session optional pam_motd.so
```

### Team Collaboration
```
session [success=1 default=ignore] pam_succeed_if.so quiet user notingroup developers
session optional pam_umask.so umask=0022
session optional pam_umask.so umask=0002
```

---

## 📖 Documentation Links

- **Bundle Documentation**: `/home/ghost/scripty/PAM-config/pam_manager/Generic.Templates/PAM-POLICY-BUNDLES-INDEX.md`
- **Bundle Completion**: `/home/ghost/scripty/PAM-config/pam_manager/Generic.Templates/COMPLETION-REPORT.txt`
- **PAM Module Info**: `/home/ghost/scripty/PAM-config/pam.modules/` (individual module JSONs)

---

## 🔄 Integration with PAM Manager

Fragments can be:
1. Used individually for custom PAM configuration
2. Combined to create new bundles
3. Extended for specific organizational requirements
4. Referenced in GUI for template selection

---

## 📝 Version History

**v1.0.0** (2026-08-16)
- Created 14 module fragments from 12 bundles
- Comprehensive documentation for each fragment
- Platform support information
- Security level designations
- Example PAM configurations

---

**Status:** ✅ All fragments created and documented  
**Last Updated:** 2026-08-16  
**Total Files:** 14 fragment files

