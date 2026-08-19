# PAM Module Bundle Templates Catalog

**Version:** 1.0.0  
**Created:** 2026-08-16  
**Location:** `/home/ghost/scripty/PAM-config/pam.modules/Generic.Templates/`

---

## 📋 Bundle Overview

Bundle templates in `/pam.modules/Generic.Templates/` are composite templates that combine elements from `/pam.modules/Element.Templates/` into complete deployable solutions.

**Total Bundles:** 12 (one per high-level security policy)

---

## 🔐 Available Bundles

### Authentication Bundles

#### 1. **bundle-yubikey-basic-auth** - YubiKey Basic MFA
```
Security Level: HIGH
Element: element-yubikey-basic-mfa
Services: login, sshd, sudo
Installation Script: 01-yubikey-basic.msh
```
- Per-user YubiKey FIDO/U2F registration
- Each user manages own key in ~/.config/Yubico/u2f_keys
- User self-enrollment workflow

#### 2. **bundle-yubikey-central-auth** - YubiKey Central MFA
```
Security Level: HIGH
Element: element-yubikey-central-mfa
Services: login, sshd, sudo
Installation Script: 02-yubikey-central.msh
```
- Administrator-managed YubiKey registration
- Central key mapping file: /etc/u2f_mappings
- Easier key rotation and bulk enrollment

#### 3. **bundle-yubikey-emergency** - YubiKey Emergency Recovery
```
Security Level: CRITICAL
Element: element-yubikey-emergency-rescue
Services: login (console only)
Installation Script: 03-yubikey-rescue.msh
```
- Emergency account for system recovery
- Specific YubiKey + backup YubiKey storage
- Local console access only (no SSH)

#### 4. **bundle-otp-mfa** - OTP/HOTP MFA
```
Security Level: CRITICAL
Element: element-otp-mfa
Services: login, sshd
Installation Script: 11-mfa-otp-hotp.msh
```
- Mobile authenticator apps (Google, Microsoft, Aegis, FreeOTP)
- Password + 6-digit OTP code
- No hardware required, highly scalable

#### 5. **bundle-certificate-otp-3fa** - Certificate + OTP 3FA
```
Security Level: CRITICAL
Element: element-certificate-otp-3fa
Services: login (local only)
Installation Script: 12-mfa-cert-otp.msh
```
- Smart card certificate + password + OTP
- Maximum security for government/military
- Most complex to setup

---

### Session Management Bundles

#### 6. **bundle-user-messaging** - User Messages and MOTD
```
Security Level: LOW
Element: element-user-messaging
Services: login, sshd
Installation Script: 04-motd-userspecific.msh
```
- System MOTD + per-user ~/.motd
- Useful for announcements and reminders

#### 7. **bundle-session-isolation** - Session Namespace Isolation
```
Security Level: HIGH
Element: element-session-isolation
Services: login, sshd
Installation Script: 05-private-namespace.msh
```
- Private /tmp and /var/tmp per user
- Prevents access to other users' files
- Linux 3.8+ with namespace support

#### 8. **bundle-environment-config** - Environment Configuration
```
Security Level: LOW
Element: element-environment-configuration
Services: login, sshd
Installation Script: 09-environment-login-type.msh
```
- Login origin detection (local vs SSH)
- Environment variables for shell detection
- Enables conditional behavior

#### 9. **bundle-group-permissions** - Group-Based File Permissions
```
Security Level: MEDIUM
Element: element-group-based-permissions
Services: login, sshd
Installation Script: 10-umask-by-group.msh
```
- Different umask per group (developers vs regular)
- Enables team collaboration
- Automatic file permission control

---

### Access Control and Security Bundles

#### 10. **bundle-access-time-control** - Time-Based Access
```
Security Level: MEDIUM
Element: element-access-time-control
Services: login, sshd
Installation Script: 06-time-restrictions.msh
```
- Restrict logins to business hours or shifts
- Contractor access control
- Effective immediately without restart

#### 11. **bundle-resource-limits** - Resource Limits
```
Security Level: MEDIUM
Element: element-resource-limits
Services: login, sshd
Installation Script: 07-concurrent-login-limits.msh
```
- Concurrent login limits
- Process and file limits
- Protection against fork bombs

#### 12. **bundle-brute-force-protection** - Attack Prevention
```
Security Level: CRITICAL
Element: element-brute-force-protection
Services: login, sshd
Installation Script: 08-intruder-lockout.msh
```
- Account lockout after failed attempts
- Default: 5 failures → 20 minute lockout
- Essential for all systems

---

## 📊 Bundle Statistics

### By Security Level

| Level | Bundles | Count |
|-------|---------|-------|
| CRITICAL | OTP MFA, Cert+OTP, Emergency, Brute Force | 4 |
| HIGH | YubiKey Basic, YubiKey Central, Session Isolation | 3 |
| MEDIUM | Time Control, Resource Limits, Group Permissions | 3 |
| LOW | User Messaging, Environment Config | 2 |

### By Category

| Category | Bundles | Count |
|----------|---------|-------|
| Authentication | YubiKey Basic, YubiKey Central, Emergency, OTP, Cert+OTP | 5 |
| Session | User Messaging, Isolation, Environment, Group Permissions | 4 |
| Access Control | Time Control, Resource Limits | 2 |
| Security | Brute Force Protection | 1 |

### Element Composition

| Bundles | Element Count |
|---------|---------------|
| Single Element | 10 bundles |
| Multiple Elements | 2 bundles (Brute Force has 2) |

---

## 🔗 Bundle Structure

Each bundle JSON contains:

```json
{
  "id": "bundle-unique-id",
  "bundle_name": "Human-readable name",
  "version": "1.0.0",
  "title": "Short title",
  "description": "Full description",
  "category": "authentication|session|access_control|security",
  "security_level": "low|medium|high|critical",
  "pam_services": ["login", "sshd"],
  "type": "Bundle",
  "elements": [
    {
      "id": "element-id",
      "import": "../Element.Templates/element-file.json",
      "required": true
    }
  ],
  "services": [
    {
      "name": "login",
      "type": "standard",
      "config_file": "/etc/pam.d/login"
    }
  ],
  "platforms": { ... },
  "installation_script": "XX-bundle-name.msh",
  "deployment_requirements": [],
  "management_tools": [],
  "configuration_files": [],
  "testing_steps": []
}
```

---

## 🎯 Deployment Scenarios

### Small Business (5-20 users)
```
1. bundle-brute-force-protection (CRITICAL)
2. bundle-session-isolation (HIGH)
```

### Medium Enterprise (20-500 users)
```
1. bundle-brute-force-protection (CRITICAL)
2. bundle-yubikey-central-auth (HIGH)
3. bundle-session-isolation (HIGH)
4. bundle-access-time-control (MEDIUM)
5. bundle-resource-limits (MEDIUM)
```

### Large Enterprise (500+ users)
```
1. bundle-brute-force-protection (CRITICAL)
2. bundle-otp-mfa (CRITICAL)
3. bundle-session-isolation (HIGH)
4. bundle-access-time-control (MEDIUM)
5. bundle-resource-limits (MEDIUM)
6. bundle-environment-config (LOW)
```

### High-Security (Finance/Government)
```
1. bundle-brute-force-protection (CRITICAL)
2. bundle-otp-mfa (CRITICAL)
3. bundle-yubikey-emergency (CRITICAL)
4. bundle-session-isolation (HIGH)
5. bundle-resource-limits (MEDIUM)
6. bundle-access-time-control (MEDIUM)
```

### Maximum Security (Military/Defense)
```
1. bundle-certificate-otp-3fa (CRITICAL)
2. bundle-yubikey-emergency (CRITICAL)
3. bundle-brute-force-protection (CRITICAL)
4. bundle-session-isolation (HIGH)
5. bundle-resource-limits (MEDIUM)
6. bundle-access-time-control (MEDIUM)
```

### Development Team
```
1. bundle-brute-force-protection (CRITICAL)
2. bundle-yubikey-basic-auth (HIGH)
3. bundle-group-permissions (MEDIUM)
4. bundle-session-isolation (HIGH)
```

---

## 📂 File Organization

```
/home/ghost/scripty/PAM-config/
├── pam_manager/Generic.Templates/
│   ├── 01-yubikey-basic.json
│   ├── 01-yubikey-basic.msh
│   ├── ... (12 bundles with scripts)
│   └── COMPLETION-REPORT.txt
│
├── pam.modules/
│   ├── Generic.Templates/
│   │   ├── bundle-yubikey-basic-auth.json
│   │   ├── bundle-yubikey-central-auth.json
│   │   ├── ... (12 bundles)
│   │   └── BUNDLE-CATALOG.md (This file)
│   │
│   ├── Element.Templates/
│   │   ├── element-yubikey-basic-mfa.json
│   │   ├── ... (12 elements)
│   │   └── ELEMENT-CATALOG.md
│   │
│   ├── Fragment.Templates/
│   │   ├── fragment.pam_unix-basic.json
│   │   ├── ... (14 fragments)
│   │   └── FRAGMENT-CATALOG.md
│   │
│   └── Service.Templates/
│       └── (Service templates if needed)
```

---

## 🔄 Template Hierarchy

```
Generic.Templates Bundle (pam_manager/)
    ↓
pam.modules Bundle Template
    ↓
Element Template (combines fragments)
    ├─ Fragment 1 (single PAM module)
    ├─ Fragment 2 (single PAM module)
    └─ Fragment 3 (single PAM module)
```

### Example Flow

```
01-yubikey-basic.json (Generic Template)
    ↓
bundle-yubikey-basic-auth.json (pam.modules Bundle)
    ↓
element-yubikey-basic-mfa.json (Element)
    ├─ fragment.pam_unix-basic.json
    └─ fragment.pam_u2f-yubikey.json
```

---

## 💼 Bundle Features

### Each Bundle Includes

- ✅ Element references and imports
- ✅ Complete PAM service configuration
- ✅ Multi-platform package requirements
- ✅ Installation script reference
- ✅ Management and diagnostic tools
- ✅ Configuration file locations
- ✅ Deployment requirements checklist
- ✅ Testing procedures
- ✅ Security level designation

---

## 🚀 Usage with PAM Manager

Bundles can be:

1. **Loaded** from pam.modules/Generic.Templates
2. **Combined** to create composite policies
3. **Customized** by overriding element parameters
4. **Deployed** via installation scripts
5. **Managed** with bundled tools

---

## 📊 Installation Script Mapping

| Bundle | Script | Installation Type |
|--------|--------|-------------------|
| bundle-yubikey-basic-auth | 01-yubikey-basic.msh | User self-enrollment |
| bundle-yubikey-central-auth | 02-yubikey-central.msh | Admin enrollment |
| bundle-yubikey-emergency | 03-yubikey-rescue.msh | Special emergency setup |
| bundle-user-messaging | 04-motd-userspecific.msh | Simple configuration |
| bundle-session-isolation | 05-private-namespace.msh | Namespace configuration |
| bundle-access-time-control | 06-time-restrictions.msh | ACL configuration |
| bundle-resource-limits | 07-concurrent-login-limits.msh | Limits configuration |
| bundle-brute-force-protection | 08-intruder-lockout.msh | Faillock setup |
| bundle-environment-config | 09-environment-login-type.msh | Environment setup |
| bundle-group-permissions | 10-umask-by-group.msh | Group management |
| bundle-otp-mfa | 11-mfa-otp-hotp.msh | OTP enrollment system |
| bundle-certificate-otp-3fa | 12-mfa-cert-otp.msh | PKI setup |

---

## ✅ Quality Assurance

Each bundle:
- ✅ References valid elements
- ✅ Includes all platform requirements
- ✅ Has installation script
- ✅ Lists management tools
- ✅ Provides deployment guide
- ✅ Includes testing steps
- ✅ Specifies configuration files
- ✅ Designates security level

---

## 🔐 Security Recommendations

### For New Deployments

1. **Always include** bundle-brute-force-protection
2. **Consider adding** bundle-session-isolation
3. **Add authentication** based on security needs
4. **Include access control** for regulated environments

### For Production Systems

1. Start with basic security (brute force + session isolation)
2. Add authentication based on security requirements
3. Layer access controls as needed
4. Monitor and adjust based on usage patterns

---

## 📝 Version History

**v1.0.0** (2026-08-16)
- Created 12 bundle templates
- Mapped to 12 elements
- Comprehensive documentation
- Installation script integration

---

## 🔗 Related Documentation

- [Fragment Catalog](../Fragment.Templates/FRAGMENT-CATALOG.md)
- [Element Catalog](../Element.Templates/ELEMENT-CATALOG.md)
- [Generic Bundle Documentation](/pam_manager/Generic.Templates/PAM-POLICY-BUNDLES-INDEX.md)

---

**Status:** ✅ All 12 bundles created and documented  
**Last Updated:** 2026-08-16  
**Total Files:** 12 bundle JSON files + 1 catalog

