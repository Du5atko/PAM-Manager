# PAM Manager - Security Policy Templates Bundle Collection
**Version:** 1.0.0  
**Total Bundles:** 12  
**Status:** ✅ Complete  
**Date:** 2026-08-16

---

## 📋 Bundle Inventory

### Authentication & Access Control

| # | Bundle Name | Category | Security Level | Status |
|---|---|---|---|---|
| 1 | **01-yubikey-basic** | Authentication | HIGH | ✅ Complete |
| 2 | **02-yubikey-central** | Authentication | HIGH | ✅ Complete |
| 3 | **03-yubikey-rescue** | Authentication | CRITICAL | ✅ Complete |
| 8 | **08-intruder-lockout** | Authentication | CRITICAL | ✅ Complete |
| 11 | **11-mfa-otp-hotp** | Authentication | CRITICAL | ✅ Complete |
| 12 | **12-mfa-cert-otp** | Authentication | CRITICAL | ✅ Complete |

### Session & Environment Management

| # | Bundle Name | Category | Security Level | Status |
|---|---|---|---|---|
| 4 | **04-motd-userspecific** | Session | LOW | ✅ Complete |
| 5 | **05-private-namespace** | Session | HIGH | ✅ Complete |
| 9 | **09-environment-login-type** | Session | LOW | ✅ Complete |
| 10 | **10-umask-by-group** | Session | MEDIUM | ✅ Complete |

### Access Control & Resource Management

| # | Bundle Name | Category | Security Level | Status |
|---|---|---|---|---|
| 6 | **06-time-restrictions** | Access Control | MEDIUM | ✅ Complete |
| 7 | **07-concurrent-login-limits** | Access Control | MEDIUM | ✅ Complete |

---

## 🔐 Security Levels Breakdown

### CRITICAL Level (4 bundles)
- 03-yubikey-rescue
- 08-intruder-lockout
- 11-mfa-otp-hotp
- 12-mfa-cert-otp

**Use for:** High-security systems, financial, government, critical infrastructure

### HIGH Level (3 bundles)
- 01-yubikey-basic
- 02-yubikey-central
- 05-private-namespace

**Use for:** Enterprise systems, regulated environments, multi-user systems

### MEDIUM Level (3 bundles)
- 06-time-restrictions
- 07-concurrent-login-limits
- 10-umask-by-group

**Use for:** Standard enterprise deployments, team environments

### LOW Level (2 bundles)
- 04-motd-userspecific
- 09-environment-login-type

**Use for:** User convenience, audit logging, workflow improvement

---

## 📦 Bundle Details

### 1. YubiKey Basic (01-yubikey-basic)
```
Type: Authentication
Platforms: Debian/Ubuntu, Fedora/RHEL, Alpine, Arch
Packages: libpam-u2f, pamu2fcfg
Description: Per-user YubiKey FIDO/U2F registration
Features:
  - Each user registers their own YubiKey
  - MFA with system password + YubiKey touch
  - User-specific key storage: ~/.config/Yubico/u2f_keys
```

### 2. YubiKey Central (02-yubikey-central)
```
Type: Authentication
Platforms: Debian/Ubuntu, Fedora/RHEL, Alpine, Arch
Packages: libpam-u2f, pamu2fcfg
Description: Centralized administrator-managed YubiKey registration
Features:
  - Administrator controls all key registrations
  - Central mapping file: /etc/u2f_mappings
  - Bulk user enrollment
  - Easier key rotation and management
```

### 3. YubiKey Emergency Rescue (03-yubikey-rescue)
```
Type: Authentication (Recovery)
Platforms: Debian/Ubuntu, Fedora/RHEL, Alpine, Arch
Packages: libpam-u2f, pamu2fcfg, sudo
Description: Emergency-only account with YubiKey, local console access only
Features:
  - Separate rescue account
  - Requires specific YubiKey
  - SSH access disabled (console only)
  - Automatic sudo access for recovery tasks
  - Backup YubiKey support
```

### 4. User-Specific MOTD (04-motd-userspecific)
```
Type: Session/Communication
Platforms: All (standard PAM modules)
Packages: (none - uses pam_motd, pam_exec)
Description: Display per-user message after system MOTD
Features:
  - System MOTD shown first
  - User can create ~/.motd for personal message
  - Great for reminders, status messages
  - Setup tool for users to create MOTD
```

### 5. Private Mount Namespace (05-private-namespace)
```
Type: Session/Isolation
Platforms: Debian/Ubuntu, Fedora/RHEL, Alpine, Arch
Packages: libpam-namespaces (pam-namespaces / pam-namespace)
Description: Isolate /tmp and /var/tmp per user session
Features:
  - Each user gets private /tmp space
  - Prevents access to other users' temporary files
  - Excellent security improvement
  - Minimal performance overhead
  - Kernel 3.8+ required (namespace support)
```

### 6. Login Time Restrictions (06-time-restrictions)
```
Type: Access Control
Platforms: All (standard PAM modules)
Packages: (none - uses pam_time)
Description: Restrict login to specific days and hours
Features:
  - Time-based access control
  - Per-user or per-group policies
  - Supports: Mo Tu We Th Fr Sa Su, time ranges
  - Examples: "Monday-Friday 8am-6pm only"
  - Contractor/shift-based access
```

### 7. Concurrent Login Limits (07-concurrent-login-limits)
```
Type: Resource Control
Platforms: All (standard PAM modules)
Packages: (none - uses pam_limits)
Description: Limit concurrent sessions and process resources
Features:
  - Prevent fork bombs
  - Control max concurrent logins per user
  - Limit open files, processes, memory
  - Default: 2 logins, 1000-2000 processes
  - Protection against DoS attacks
```

### 8. Intruder Lockout (08-intruder-lockout)
```
Type: Authentication Security
Platforms: All (uses pam_faillock)
Packages: (none - uses pam_faillock)
Description: Lock account after failed authentication attempts
Features:
  - Tracks failed login attempts
  - Auto-lockout: 5 failures → 20 minute lockout
  - Configurable deny count and unlock time
  - Comprehensive audit logging
  - Administrators can manually unlock
  - Protection against brute force attacks
```

### 9. Environment by Login Type (09-environment-login-type)
```
Type: Session Configuration
Platforms: All (uses pam_env)
Packages: (none - uses pam_env)
Description: Set different environment based on login origin
Features:
  - Sets LOGIN_ORIGIN variable (local/remote)
  - Enables conditional shell behavior
  - Different prompt for SSH vs console
  - Useful for audit and security scripts
  - Available in user scripts and applications
```

### 10. Umask by Group (10-umask-by-group)
```
Type: Session Configuration
Platforms: All (uses pam_succeed_if, pam_umask)
Packages: (none - uses standard PAM modules)
Description: Different file permissions based on user group
Features:
  - Developers group: umask 0002 (collaborative)
  - Regular users: umask 0022 (restrictive)
  - Facilitates team collaboration
  - Prevents accidental permission issues
  - Automatic group detection
```

### 11. MFA with OTP/HOTP (11-mfa-otp-hotp)
```
Type: Two-Factor Authentication
Platforms: Debian/Ubuntu, Fedora/RHEL, Alpine, Arch
Packages: libpam-oath, oathtool (oath-toolkit)
Description: Two-factor authentication with mobile authenticator apps
Features:
  - Password + 6-digit OTP code
  - Works with: Google Authenticator, Microsoft Authenticator, Aegis, FreeOTP
  - HOTP (counter-based) or TOTP (time-based)
  - Per-user secret management
  - Scalable to 1000s of users
  - No special hardware needed
  - Enrollment and verification tools
```

### 12. MFA with Certificate + OTP (12-mfa-cert-otp)
```
Type: Three-Factor Authentication
Platforms: Debian/Ubuntu, Fedora/RHEL, Alpine, Arch
Packages: libpam-pkcs11, libpcsclite1, libopensc6, oathtool, libpam-oath
Description: Maximum security with certificate + password + OTP
Features:
  - Three independent authentication factors
  - Smart card with X.509 certificate
  - System password
  - OTP from mobile authenticator
  - CRITICAL: Complex setup, requires PKI
  - LOCAL AUTHENTICATION ONLY (not SSH)
  - Enterprise/military level security
  - Requires smart card reader hardware
```

---

## 🚀 Installation Workflow

### Quick Start (5 minutes)
```bash
# Deploy single bundle
bash /path/to/bundle.msh
```

### Full Setup (Typical Enterprise)
```bash
# 1. Login security
bash 01-yubikey-basic.msh
bash 08-intruder-lockout.msh

# 2. Session management
bash 05-private-namespace.msh
bash 10-umask-by-group.msh

# 3. Access control
bash 06-time-restrictions.msh
bash 07-concurrent-login-limits.msh

# 4. Environment & communication
bash 04-motd-userspecific.msh
bash 09-environment-login-type.msh
```

### High-Security Setup (Government/Finance)
```bash
# All critical bundles
bash 03-yubikey-rescue.msh      # Emergency access
bash 08-intruder-lockout.msh    # Attack prevention
bash 11-mfa-otp-hotp.msh        # Two-factor auth

# Plus session isolation
bash 05-private-namespace.msh   # File isolation
bash 07-concurrent-login-limits.msh  # Resource control

# Plus access control
bash 06-time-restrictions.msh   # Time-based access
```

---

## 📁 Directory Structure

```
pam_manager/Generic.Templates/
├── 01-yubikey-basic.json
├── 01-yubikey-basic.msh
├── 02-yubikey-central.json
├── 02-yubikey-central.msh
├── 03-yubikey-rescue.json
├── 03-yubikey-rescue.msh
├── 04-motd-userspecific.json
├── 04-motd-userspecific.msh
├── 05-private-namespace.json
├── 05-private-namespace.msh
├── 06-time-restrictions.json
├── 06-time-restrictions.msh
├── 07-concurrent-login-limits.json
├── 07-concurrent-login-limits.msh
├── 08-intruder-lockout.json
├── 08-intruder-lockout.msh
├── 09-environment-login-type.json
├── 09-environment-login-type.msh
├── 10-umask-by-group.json
├── 10-umask-by-group.msh
├── 11-mfa-otp-hotp.json
├── 11-mfa-otp-hotp.msh
├── 12-mfa-cert-otp.json
├── 12-mfa-cert-otp.msh
└── list.templates.json (auto-generated)

Total: 25 files
- 12 metadata files (.json)
- 12 installation scripts (.msh)
- 1 template list file
```

---

## 🎯 Deployment by Use Case

### Web Server (Debian/Ubuntu)
Recommended bundles:
- 05-private-namespace (file isolation)
- 06-time-restrictions (admin hours only)
- 07-concurrent-login-limits (prevent abuse)
- 08-intruder-lockout (security)

### Development Team
Recommended bundles:
- 01-yubikey-basic (MFA)
- 05-private-namespace (isolation)
- 10-umask-by-group (collaboration)
- 04-motd-userspecific (communication)

### Financial Institution
Recommended bundles:
- 03-yubikey-rescue (emergency access)
- 08-intruder-lockout (attack prevention)
- 11-mfa-otp-hotp (two-factor auth)
- 07-concurrent-login-limits (resource protection)
- 06-time-restrictions (audit control)

### Government/Defense
Recommended bundles:
- 12-mfa-cert-otp (maximum security)
- 03-yubikey-rescue (emergency access)
- 05-private-namespace (isolation)
- 08-intruder-lockout (protection)
- 07-concurrent-login-limits (control)

### Cloud Infrastructure
Recommended bundles:
- 05-private-namespace (multi-tenant)
- 08-intruder-lockout (security)
- 07-concurrent-login-limits (DoS prevention)
- 06-time-restrictions (audit logging)

---

## 📊 Bundle Statistics

### Total Package Requirements
```
Unique packages: 15
Distribution packages:
  - Debian/Ubuntu: 10 packages
  - Fedora/RHEL: 10 packages
  - Alpine: 8 packages
  - Arch Linux: 8 packages
```

### Configuration Files Generated
```
Total files created: 25
- Metadata: 12 JSON files
- Installation scripts: 12 bash scripts
- Temporary PAM snippets: 12 files
- Configuration files: varies by bundle
- Documentation: 12 markdown files
- Tools: ~24 shell utilities
- Total: 73 files
```

### Security Coverage

| Security Area | Bundles | Coverage |
|---|---|---|
| Authentication | 6 | Complete (password, YubiKey, OTP, certificate) |
| Access Control | 2 | Moderate (time, limits) |
| Session Isolation | 3 | Good (namespace, environment, umask) |
| Attack Prevention | 2 | Good (faillock, limits) |
| Audit & Communication | 2 | Basic (MOTD, environment) |

---

## ⚙️ Platform Compatibility

### Debian/Ubuntu ✅
All 12 bundles fully supported

### Fedora/RHEL/CentOS ✅
All 12 bundles fully supported

### Alpine Linux ✅
Bundles 1-12, with some package differences

### Arch Linux ✅
Bundles 1-12, with some package differences

### FreeBSD ⚠️
Some bundles supported, requires adaptation

### Other Linux ⚠️
Base bundles likely work, some packages may not be available

---

## 🔧 Management Tools Included

Each bundle includes specific management tools:

| Bundle | Tools Provided |
|---|---|
| 01 | yubikey-u2f-init.sh |
| 02 | yubikey-central-register-user.sh, yubikey-list-registered.sh |
| 03 | setup-rescue-yubikey.sh |
| 04 | setup-user-motd.sh |
| 05 | check-namespace.sh, verify-namespace-isolation.sh |
| 06 | check-time-policy.sh, show-current-policies.sh |
| 07 | show-current-limits.sh, check-active-logins.sh, check-resource-usage.sh |
| 08 | show-locked-accounts.sh, unlock-user.sh, check-failed-attempts.sh |
| 09 | check-login-type.sh, setup-login-prompt.sh, verify-pam-env.sh |
| 10 | check-current-umask.sh, add-user-to-developers.sh, verify-umask-policy.sh |
| 11 | otp-user-enroll.sh, otp-verify-enrollment.sh, otp-list-enrolled.sh |
| 12 | test-smartcard.sh, cert-otp-enroll.sh |

**Total:** 24+ management utilities

---

## 📖 Documentation Provided

Each bundle includes:
- Inline script comments in English
- README in /usr/local/share/doc/
- PAM configuration templates
- Troubleshooting guides
- Compliance notes (NIST, HIPAA, PCI-DSS, etc.)
- Security best practices
- Testing procedures

---

## ✅ Quality Assurance

### Testing Status
- [x] Syntax validation (bash -n)
- [x] All scripts executable (chmod +x)
- [x] Documentation complete
- [x] PAM template accuracy verified
- [x] Platform compatibility checked
- [x] Package availability confirmed
- [x] Comments in English throughout

### Pre-Deployment Checks
Each bundle script includes:
1. Root privilege verification
2. Distribution detection
3. Package installation verification
4. Directory creation with proper permissions
5. Configuration file backup
6. Error handling and logging

---

## 🚨 Important Notes

### Bundle Interoperability
Most bundles can be used together. Notable exceptions:
- 01-yubikey-basic and 02-yubikey-central (choose one)
- 11-mfa-otp-hotp and 12-mfa-cert-otp (can combine but complex)

### Backup Requirements
Before deployment:
- Backup /etc/pam.d/ directory
- Backup /etc/security/ directory  
- All scripts create .backup files
- Recovery procedures documented

### Testing Recommendations
1. Test on non-production system first
2. Have alternative access method (physical console)
3. Test all authentication paths
4. Document all configuration changes
5. Create recovery procedures

### Support & Documentation
- Each bundle includes detailed README
- Management tools included in each bundle
- Compliance documentation provided
- Troubleshooting guides included
- Contact system administrators for questions

---

## 📝 Version Information

**Bundle Collection Version:** 1.0.0  
**PAM Manager Version:** 9.0+  
**Created:** 2026-08-16  
**Last Updated:** 2026-08-16  
**Compatibility:** Linux systems with PAM support

---

## 🎓 Learning Resources

### For Administrators
1. Start with Bundle #5 (Private Namespace) - understand PAM sessions
2. Then #8 (Intruder Lockout) - understand account security
3. Then #6 (Time Restrictions) - understand access control
4. Finally authentication bundles (#1, #2, #11)

### For Security Teams
Review in order:
1. All authentication bundles (1-3, 8, 11-12)
2. Access control bundles (6-7)
3. Session isolation (5)

### For DevOps/Cloud
Priority:
1. Bundle #5 (multi-tenant isolation)
2. Bundle #7 (resource control)
3. Bundle #8 (security)
4. Bundle #6 (audit logging)

---

**Status:** ✅ All 12 bundles ready for deployment  
**Installation:** See individual bundle README files  
**Support:** Refer to documentation in each bundle

