# PAM Module Element Templates Catalog

**Version:** 1.0.0  
**Created:** 2026-08-16  
**Location:** `/home/ghost/scripty/PAM-config/pam.modules/Element.Templates/`

---

## 📋 Element Overview

Element templates are composite PAM configurations combining multiple fragments into complete functional solutions. Each element represents a complete feature implementation.

**Total Elements:** 12 (one per bundle)

---

## 🔐 Available Elements

### Authentication Elements

#### 1. **element-yubikey-basic-mfa** - YubiKey Basic MFA
```
Category: Authentication
Security Level: HIGH
Fragments: pam_unix, pam_u2f
Services: login, sshd, sudo
```
- Per-user YubiKey FIDO/U2F registration
- Each user maintains own key file: ~/.config/Yubico/u2f_keys
- Strong second factor authentication

#### 2. **element-yubikey-central-mfa** - YubiKey Central MFA
```
Category: Authentication
Security Level: HIGH
Fragments: pam_unix, pam_u2f
Services: login, sshd, sudo
```
- Centralized administrator-managed registration
- All keys in: /etc/u2f_mappings
- Easier key rotation and management

#### 3. **element-yubikey-emergency-rescue** - Emergency Rescue Account
```
Category: Authentication
Security Level: CRITICAL
Fragments: pam_succeed_if, pam_deny, pam_u2f
Services: login (local console only)
```
- Emergency recovery account with specific YubiKey
- Local console access only (no SSH)
- Automatic sudo access

#### 4. **element-otp-mfa** - OTP/HOTP Two-Factor Authentication
```
Category: Authentication
Security Level: CRITICAL
Fragments: pam_unix, pam_oath
Services: login, sshd
```
- Mobile authenticator apps (Google, Microsoft, Aegis, FreeOTP)
- Password + 6-digit OTP code
- No hardware required, highly scalable

#### 5. **element-certificate-otp-3fa** - Certificate + OTP 3FA
```
Category: Authentication
Security Level: CRITICAL
Fragments: pam_unix, pam_pkcs11, pam_oath
Services: login (local only)
```
- Smart card certificate + password + OTP
- Maximum security for government/military
- Most complex to setup and manage

---

### Session Management Elements

#### 6. **element-user-messaging** - User-Specific Messages
```
Category: Session
Security Level: LOW
Fragments: pam_motd, pam_exec
Services: login, sshd
```
- System MOTD + per-user ~/.motd
- Useful for announcements, reminders, status

#### 7. **element-session-isolation** - Session Namespace Isolation
```
Category: Session
Security Level: HIGH
Fragments: pam_namespace
Services: login, sshd
```
- Private /tmp and /var/tmp per user
- Prevents access to other users' files
- Works with containers and VMs

#### 8. **element-environment-configuration** - Login Environment
```
Category: Session
Security Level: LOW
Fragments: pam_env
Services: login, sshd
```
- Set environment variables by login origin
- Detects local vs SSH access
- Enables conditional shell behavior

#### 9. **element-group-based-permissions** - Group Permissions
```
Category: Session
Security Level: MEDIUM
Fragments: pam_succeed_if, pam_umask
Services: login, sshd
```
- Different umask for developers vs regular users
- Enables team collaboration
- Automatic file permission settings

---

### Access Control Elements

#### 10. **element-access-time-control** - Time-Based Access
```
Category: Access Control
Security Level: MEDIUM
Fragments: pam_time
Services: login, sshd
```
- Restrict logins to specific days/hours
- Business hours, shift-based, contractor access
- Effective immediately

#### 11. **element-resource-limits** - Resource Limits
```
Category: Resource Control
Security Level: MEDIUM
Fragments: pam_limits
Services: login, sshd
```
- Concurrent login limits
- Process and file limits
- Protects against fork bombs

#### 12. **element-brute-force-protection** - Attack Prevention
```
Category: Security
Security Level: CRITICAL
Fragments: pam_faillock, pam_unix
Services: login, sshd
```
- Lock account after failed attempts
- Default: 5 failures → 20 minute lockout
- Essential for all systems

---

## 📊 Element Statistics

### By Security Level

| Level | Elements | Count |
|-------|----------|-------|
| CRITICAL | OTP MFA, Cert+OTP, Emergency Rescue, Brute Force | 4 |
| HIGH | YubiKey Basic, YubiKey Central, Session Isolation | 3 |
| MEDIUM | Time Control, Resource Limits, Group Permissions | 3 |
| LOW | User Messaging, Environment Config | 2 |

### By Category

| Category | Elements | Count |
|----------|----------|-------|
| Authentication | YubiKey Basic, YubiKey Central, Emergency, OTP, Cert+OTP | 5 |
| Session | User Messaging, Isolation, Environment, Group Permissions | 4 |
| Access Control | Time Control, Resource Limits | 2 |
| Security | Brute Force Protection | 1 |

### By Fragment Count

| Fragments | Elements | Count |
|-----------|----------|-------|
| 1 Fragment | Isolation, Time Control, Resource Limits, Environment | 4 |
| 2 Fragments | YubiKey Basic, YubiKey Central, OTP MFA, User Messaging, Brute Force | 5 |
| 3 Fragments | Emergency Rescue, Group Permissions, Cert+OTP | 3 |

---

## 🔗 Fragment Composition

### Element Hierarchy

```
Element (Complete Solution)
  ├─ Fragment (Individual Module Configuration)
  │  ├─ Module (pam_*.so)
  │  ├─ Parameters
  │  ├─ Platform Support
  │  └─ Documentation
  └─ Service Specific Rules
```

### Element to Fragment Mapping

| Element | Fragments Used |
|---------|-----------------|
| YubiKey Basic | pam_unix, pam_u2f |
| YubiKey Central | pam_unix, pam_u2f |
| Emergency Rescue | pam_succeed_if, pam_deny, pam_u2f |
| User Messaging | pam_motd, pam_exec |
| Session Isolation | pam_namespace |
| Time Control | pam_time |
| Resource Limits | pam_limits |
| Brute Force | pam_faillock, pam_unix |
| Environment | pam_env |
| Group Permissions | pam_succeed_if, pam_umask |
| OTP MFA | pam_unix, pam_oath |
| Cert+OTP 3FA | pam_unix, pam_pkcs11, pam_oath |

---

## 💼 Element Features

Each element JSON includes:

```json
{
  "id": "element-unique-id",
  "name": "Human-readable name",
  "description": "What it does",
  "category": "authentication|session|access_control|security",
  "security_level": "low|medium|high|critical",
  "pam_services": ["login", "sshd"],
  "fragments": [
    {
      "module": "module_name",
      "id": "fragment-id",
      "interface": "auth|session|account",
      "config": { "param": "value" },
      "control_flag": "required|optional",
      "ordering": 1
    }
  ],
  "pam_configuration": {
    "auth": ["full pam stack example"],
    "session": ["session stack"]
  },
  "packages": {
    "debian_ubuntu": ["package1", "package2"]
  },
  "deployment_requirements": [],
  "management_tools": [],
  "bundle_source": "XX-bundle-name",
  "testing_steps": []
}
```

---

## 🎯 Deployment Scenarios

### Basic Security (Small Business)
```
1. element-brute-force-protection (CRITICAL)
2. element-session-isolation (HIGH)
3. element-otp-mfa (CRITICAL) - optional
```

### Enterprise Standard
```
1. element-brute-force-protection (CRITICAL)
2. element-yubikey-central-mfa (HIGH)
3. element-session-isolation (HIGH)
4. element-access-time-control (MEDIUM)
5. element-resource-limits (MEDIUM)
```

### High-Security (Finance/Government)
```
1. element-brute-force-protection (CRITICAL)
2. element-otp-mfa (CRITICAL)
3. element-session-isolation (HIGH)
4. element-resource-limits (MEDIUM)
5. element-access-time-control (MEDIUM)
6. element-yubikey-emergency-rescue (CRITICAL)
```

### Maximum Security (Government/Military)
```
1. element-certificate-otp-3fa (CRITICAL)
2. element-yubikey-emergency-rescue (CRITICAL)
3. element-brute-force-protection (CRITICAL)
4. element-session-isolation (HIGH)
5. element-resource-limits (MEDIUM)
6. element-access-time-control (MEDIUM)
```

### Development Team
```
1. element-brute-force-protection (CRITICAL)
2. element-yubikey-basic-mfa (HIGH)
3. element-group-based-permissions (MEDIUM)
4. element-session-isolation (HIGH)
5. element-user-messaging (LOW)
```

---

## 📚 Element Relationships

### Authentication Options (Choose One or Combine)
- **Basic:** None (just system password via pam_unix)
- **2FA Hardware:** element-yubikey-basic-mfa or element-yubikey-central-mfa
- **2FA Software:** element-otp-mfa
- **3FA Maximum:** element-certificate-otp-3fa

### Emergency Access
- **YubiKey:** element-yubikey-emergency-rescue
- **Certificate:** Included in element-certificate-otp-3fa setup

### Session Security (Combine As Needed)
- element-session-isolation (file isolation)
- element-group-based-permissions (team collaboration)
- element-environment-configuration (context detection)
- element-user-messaging (communication)

### Access Control (Combine As Needed)
- element-access-time-control (time restrictions)
- element-resource-limits (resource protection)
- element-brute-force-protection (attack prevention)

---

## 🔧 Integration Methods

### Method 1: Individual Element Deployment
```bash
# Import element into PAM Manager GUI
- Load element JSON
- Configure parameters
- Deploy to system
```

### Method 2: Composite Element Stack
```bash
# Combine multiple elements
- Select multiple elements
- Resolve conflicts
- Merge configurations
- Deploy as single policy
```

### Method 3: Fragment-Level Customization
```bash
# Build custom element from fragments
- Select fragments manually
- Override parameters
- Create new element
- Store as template
```

---

## 📖 Documentation Levels

### Level 1: Element Overview
- Name and description
- Security level
- Typical use cases
- Fragment composition

### Level 2: Deployment Guide
- Package requirements
- Configuration files
- Deployment steps
- Testing procedures

### Level 3: Advanced Configuration
- Parameter details
- Fragment interactions
- Performance tuning
- Troubleshooting

### Level 4: Implementation Details
- PAM stack ordering
- Control flag meanings
- Failure scenarios
- Recovery procedures

---

## ✅ Quality Assurance

Each element includes:
- ✅ Complete PAM configuration examples
- ✅ All required packages listed
- ✅ Platform support information
- ✅ Deployment requirements
- ✅ Testing steps
- ✅ Management tools
- ✅ Security level designation
- ✅ Bundle source tracking

---

## 🔐 Security Best Practices

### Authentication Elements
1. Always include brute-force protection
2. Use pam_unix as foundation
3. Add MFA when possible
4. Test all authentication paths

### Session Elements
1. Enable session isolation (pam_namespace)
2. Configure resource limits
3. Set environment variables for audit
4. Enable time-based restrictions for sensitive roles

### Access Control
1. Implement time-based access
2. Set concurrent session limits
3. Monitor for anomalies
4. Regular security audits

---

## 📂 File Organization

```
pam.modules/Element.Templates/
├── element-yubikey-basic-mfa.json
├── element-yubikey-central-mfa.json
├── element-yubikey-emergency-rescue.json
├── element-user-messaging.json
├── element-session-isolation.json
├── element-access-time-control.json
├── element-resource-limits.json
├── element-brute-force-protection.json
├── element-environment-configuration.json
├── element-group-based-permissions.json
├── element-otp-mfa.json
├── element-certificate-otp-3fa.json
└── ELEMENT-CATALOG.md (This file)
```

---

## 🚀 Usage with PAM Manager

Elements can be:
1. **Loaded** into Template Manager GUI
2. **Previewed** before deployment
3. **Combined** with other elements
4. **Customized** by overriding parameters
5. **Stored** as new templates
6. **Applied** to systems

---

## 🔄 Relationships to Bundles

Elements map directly to bundles:

| Element | Bundle | Type |
|---------|--------|------|
| element-yubikey-basic-mfa | 01-yubikey-basic | 1:1 |
| element-yubikey-central-mfa | 02-yubikey-central | 1:1 |
| element-yubikey-emergency-rescue | 03-yubikey-rescue | 1:1 |
| element-user-messaging | 04-motd-userspecific | 1:1 |
| element-session-isolation | 05-private-namespace | 1:1 |
| element-access-time-control | 06-time-restrictions | 1:1 |
| element-resource-limits | 07-concurrent-login-limits | 1:1 |
| element-brute-force-protection | 08-intruder-lockout | 1:1 |
| element-environment-configuration | 09-environment-login-type | 1:1 |
| element-group-based-permissions | 10-umask-by-group | 1:1 |
| element-otp-mfa | 11-mfa-otp-hotp | 1:1 |
| element-certificate-otp-3fa | 12-mfa-cert-otp | 1:1 |

---

## 📊 Complexity Matrix

| Element | Setup Time | Complexity | Skill Required | Cost |
|---------|------------|-----------|-----------------|------|
| User Messaging | 30 min | Low | Basic | Free |
| Environment Config | 30 min | Low | Basic | Free |
| Time Control | 1 hour | Low | Basic | Free |
| Session Isolation | 1-2 hours | Medium | Intermediate | Free |
| Resource Limits | 1-2 hours | Medium | Intermediate | Free |
| Group Permissions | 1 hour | Medium | Intermediate | Free |
| Brute Force | 30 min | Low | Basic | Free |
| YubiKey Basic | 2-4 hours | Medium | Intermediate | $20-100/user |
| YubiKey Central | 2-4 hours | Medium | Intermediate | $20-100/user |
| OTP MFA | 1-2 hours | Low | Basic | Free |
| Emergency Rescue | 2-4 hours | Medium | Intermediate | $50-150 |
| Cert+OTP 3FA | 2-4 weeks | High | Expert | $5000-20000 |

---

## 📝 Version History

**v1.0.0** (2026-08-16)
- Created 12 element templates from bundles
- Comprehensive documentation for each
- Fragment composition details
- Deployment scenarios and best practices

---

**Status:** ✅ All elements created and documented  
**Last Updated:** 2026-08-16  
**Total Files:** 12 element JSON files

