# PAM Bundle Templates for pam.modules

**Version:** 1.0.0  
**Location:** `/home/ghost/scripty/PAM-config/pam.modules/Generic.Templates/`  
**Created:** 2026-08-16

---

## 🎯 Quick Start

### What are Bundle Templates?

Bundle templates are composite PAM configurations that combine multiple elements into complete, deployable security policies. Each bundle provides a complete solution for a specific authentication or access control requirement.

### How to Use

1. **Explore available bundles:**
   ```bash
   cd /home/ghost/scripty/PAM-config/pam.modules/Generic.Templates
   cat BUNDLE-CATALOG.md
   ```

2. **Select a bundle:**
   ```bash
   # Example: Deploy YubiKey MFA
   cat bundle-yubikey-basic-auth.json
   ```

3. **Review requirements:**
   ```bash
   jq '.deployment_requirements' bundle-yubikey-basic-auth.json
   ```

4. **Install bundle:**
   ```bash
   # Get installation script name
   SCRIPT=$(jq -r '.installation_script' bundle-yubikey-basic-auth.json)
   
   # Run installer
   bash ../../pam_manager/Generic.Templates/$SCRIPT
   ```

---

## 📚 Documentation

### Main Documents

1. **BUNDLE-CATALOG.md** (Start here!)
   - Complete list of all 12 bundles
   - Security levels and descriptions
   - Use case scenarios
   - Deployment recommendations

2. **BUNDLE-INTEGRATION-GUIDE.md** (Technical details)
   - Architecture and design
   - File structure and organization
   - Bundle processing workflow
   - Code examples and usage patterns

3. **README.md** (This file)
   - Quick start guide
   - File organization
   - Common tasks

### Related Documentation

- [Element Catalog](../Element.Templates/ELEMENT-CATALOG.md) - Features
- [Fragment Catalog](../Fragment.Templates/FRAGMENT-CATALOG.md) - Modules
- [Generic Bundles](../../pam_manager/Generic.Templates/PAM-POLICY-BUNDLES-INDEX.md) - Source docs

---

## 📁 File Organization

```
pam.modules/
├── Generic.Templates/          ← Bundle Templates (CURRENT)
│   ├── bundle-*.json           (12 templates)
│   ├── BUNDLE-CATALOG.md       (index + descriptions)
│   ├── BUNDLE-INTEGRATION-GUIDE.md (technical guide)
│   └── README.md               (this file)
│
├── Element.Templates/          ← Composite Features
│   ├── element-*.json          (12 elements)
│   └── ELEMENT-CATALOG.md
│
├── Fragment.Templates/         ← Individual PAM Modules
│   ├── fragment.*.json         (14 fragments)
│   └── FRAGMENT-CATALOG.md
│
└── Service.Templates/          ← Reserved for service configs
    └── (Currently empty)
```

---

## 🔐 Available Bundles

| # | Bundle | Security | Purpose |
|---|--------|----------|---------|
| 1 | yubikey-basic-auth | HIGH | Per-user YubiKey MFA |
| 2 | yubikey-central-auth | HIGH | Admin-managed YubiKey |
| 3 | yubikey-emergency | CRITICAL | Emergency recovery account |
| 4 | user-messaging | LOW | System + user MOTD |
| 5 | session-isolation | HIGH | Private /tmp per user |
| 6 | access-time-control | MEDIUM | Restrict login hours |
| 7 | resource-limits | MEDIUM | Concurrent session limits |
| 8 | brute-force-protection | CRITICAL | Account lockout |
| 9 | environment-config | LOW | Login-origin detection |
| 10 | group-permissions | MEDIUM | Group-based umask |
| 11 | otp-mfa | CRITICAL | Mobile authenticator MFA |
| 12 | certificate-otp-3fa | CRITICAL | Smart card + password + OTP |

---

## 🚀 Common Tasks

### Find a Bundle

```bash
# List all bundles
ls -1 bundle-*.json

# Search by keyword
grep -l "YubiKey" bundle-*.json
grep -l "critical" *CATALOG.md

# Find by security level
jq -r 'select(.security_level == "critical") | .bundle_name' bundle-*.json
```

### View Bundle Details

```bash
# See full bundle configuration
cat bundle-yubikey-basic-auth.json | jq '.'

# Just the summary
jq '{id, bundle_name, security_level, pam_services}' bundle-*.json

# Installation requirements
jq '.deployment_requirements' bundle-*.json
```

### Deploy a Bundle

```bash
# Get the script name
SCRIPT=$(jq -r '.installation_script' bundle-yubikey-basic-auth.json)
SCRIPT_PATH="../../pam_manager/Generic.Templates/$SCRIPT"

# Review the script
less $SCRIPT_PATH

# Run it
sudo bash $SCRIPT_PATH
```

### Combine Multiple Bundles

```bash
# Security-focused deployment
BUNDLES=(
    "bundle-brute-force-protection.json"
    "bundle-session-isolation.json"
    "bundle-otp-mfa.json"
)

for bundle in "${BUNDLES[@]}"; do
    script=$(jq -r '.installation_script' "$bundle")
    echo "Installing $bundle..."
    sudo bash "../../pam_manager/Generic.Templates/$script"
done
```

### Backup Before Deployment

```bash
# Recommended before any PAM changes
sudo cp -r /etc/pam.d /etc/pam.d.backup.$(date +%Y%m%d_%H%M%S)

# Then deploy your bundle
sudo bash installation_script.msh
```

---

## 🎯 Deployment Scenarios

### Scenario 1: Small Business
```
Recommended:
- bundle-brute-force-protection ← Essential
- bundle-session-isolation      ← Recommended
```

### Scenario 2: Medium Enterprise
```
Recommended:
- bundle-brute-force-protection ← Essential
- bundle-yubikey-central-auth   ← MFA
- bundle-session-isolation      ← Isolation
- bundle-access-time-control    ← Policies
- bundle-resource-limits        ← Protection
```

### Scenario 3: High Security
```
Recommended:
- bundle-brute-force-protection ← Essential
- bundle-otp-mfa                ← Strong MFA
- bundle-yubikey-emergency      ← Recovery
- bundle-session-isolation      ← Isolation
- bundle-access-time-control    ← Policies
```

---

## 📊 Bundle Properties

### Every Bundle Includes

```json
{
  "id": "Unique identifier",
  "bundle_name": "Human-readable name",
  "version": "Semantic version",
  "title": "Short description",
  "description": "Full description",
  "category": "authentication|session|access_control|security",
  "security_level": "low|medium|high|critical",
  "pam_services": ["login", "sshd", "sudo"],
  "type": "Bundle",
  "elements": [{"id": "...", "import": "..."}],
  "services": [{"name": "...", "config_file": "/etc/pam.d/..."}],
  "platforms": {
    "debian_ubuntu": {"packages": [...], "package_manager": "apt"},
    "fedora_rhel": {"packages": [...], "package_manager": "dnf"},
    ...
  },
  "installation_script": "XX-name.msh",
  "deployment_requirements": [...],
  "management_tools": [...],
  "configuration_files": [...],
  "testing_steps": [...]
}
```

---

## 🔍 Understanding the Architecture

### Template Hierarchy

```
Bundle Template
  └─ Orchestrates complete policy
     └─ Combines multiple Elements
        └─ Each Element uses Fragments
           └─ Each Fragment is a PAM module
```

### Example: YubiKey MFA Bundle

```
bundle-yubikey-basic-auth.json
  └─ Uses element-yubikey-basic-mfa.json
     ├─ Uses fragment.pam_unix-basic.json
     │  └─ Provides password authentication
     └─ Uses fragment.pam_u2f-yubikey.json
        └─ Provides YubiKey FIDO/U2F
```

---

## 🛠️ Management Tools

### Per-Bundle Tools

Each bundle includes specific management tools:

- **YubiKey Basic**: `yubikey-u2f-init.sh` (user enrollment)
- **YubiKey Central**: `yubikey-central-register-user.sh` (admin enrollment)
- **Brute Force**: `show-locked-accounts.sh`, `unlock-user.sh`
- **OTP MFA**: `otp-user-enroll.sh`, `otp-verify-enrollment.sh`
- **Session Isolation**: `check-namespace.sh`, `verify-namespace-isolation.sh`

Located in: `/home/ghost/scripty/PAM-config/pam_manager/Generic.Templates/`

---

## 🧪 Testing Deployed Bundles

### General Testing

```bash
# Check if PAM was modified correctly
cat /etc/pam.d/login | grep pam_

# List locked accounts (for brute force bundle)
/usr/local/bin/show-locked-accounts.sh

# Check current limits (for resource bundle)
/usr/local/bin/show-current-limits.sh
```

### Service-Specific Testing

```bash
# Test login authentication
ssh -vvv testuser@localhost

# Test sudo access
sudo -l

# Test su switching
su - testuser
```

---

## ⚠️ Important Notes

### Before Deployment

1. **Backup PAM config:**
   ```bash
   sudo cp -r /etc/pam.d /etc/pam.d.backup
   ```

2. **Keep sudo access open:**
   ```bash
   # Never lock yourself out!
   sudo su -
   ```

3. **Test in VM first:**
   - Deploy in test environment
   - Verify all services work
   - Then deploy to production

### Common Issues

**Issue:** "Installation script not found"
```bash
# Solution: Check script path
ls -la ../../pam_manager/Generic.Templates/01-*.msh
```

**Issue:** "Element file not found"
```bash
# Solution: Verify element path
ls -la ../Element.Templates/element-*.json
```

**Issue:** "PAM configuration failed"
```bash
# Solution: Check /etc/pam.d/ was backed up
ls -la /etc/pam.d.backup*
```

---

## 📞 Getting Help

### Documentation Resources

1. Start with: `BUNDLE-CATALOG.md` (overview)
2. Then read: `BUNDLE-INTEGRATION-GUIDE.md` (technical details)
3. Reference: Individual bundle JSON files
4. Details: Related Element and Fragment catalogs

### Troubleshooting

```bash
# Validate bundle JSON
jq . bundle-yubikey-basic-auth.json

# Check element reference
ls -la $(jq -r '.elements[0].import' bundle-yubikey-basic-auth.json)

# Verify installation script
ls -la $(jq -r '.installation_script | "../../pam_manager/Generic.Templates/" + .' bundle-yubikey-basic-auth.json)
```

---

## 📈 Bundle Statistics

- **Total Bundles:** 12
- **Security Levels:** CRITICAL (4), HIGH (3), MEDIUM (3), LOW (2)
- **Categories:** Authentication (5), Session (4), Access Control (2), Security (1)
- **Platform Support:** 5 major distributions
- **Total Elements:** 12 (one per bundle, or shared)
- **Total Fragments:** 14 (reused across elements)

---

## 🎓 Learning Path

### For Beginners
1. Read this README
2. Browse BUNDLE-CATALOG.md
3. Pick one bundle to deploy
4. Follow its testing steps
5. Try another bundle

### For Administrators
1. Read BUNDLE-INTEGRATION-GUIDE.md
2. Create deployment plan
3. Test in VM environment
4. Combine bundles as needed
5. Monitor after deployment

### For Developers
1. Study bundle JSON schema
2. Review element templates
3. Understand fragment composition
4. Examine installation scripts
5. Extend with custom fragments

---

## 📝 Version Information

**Bundle Template Version:** 1.0.0  
**Created:** 2026-08-16  
**Status:** Production Ready  
**Total Files:** 12 bundles + 2 documentation files

---

## 🔗 Quick Links

- [Bundle Catalog (Full List)](./BUNDLE-CATALOG.md)
- [Integration Guide (Technical)](./BUNDLE-INTEGRATION-GUIDE.md)
- [Element Templates](../Element.Templates/ELEMENT-CATALOG.md)
- [Fragment Templates](../Fragment.Templates/FRAGMENT-CATALOG.md)
- [PAM Manager Home](../../PAMManager.py)

---

## ✅ Checklist for First Deployment

Before deploying any bundle:

- [ ] Read bundle description and requirements
- [ ] Backup `/etc/pam.d/` directory
- [ ] Ensure sudo access is available
- [ ] Review installation script
- [ ] Test in virtual machine first
- [ ] Have rollback procedure ready
- [ ] Keep console access open
- [ ] Document any customizations
- [ ] Plan monitoring strategy
- [ ] Schedule deployment during maintenance window

---

**Disclaimer:** PAM configuration changes can affect system access. Always test thoroughly before production deployment. Keep backups and rollback procedures ready.

---

**Last Updated:** 2026-08-16  
**Status:** ✅ Complete and Ready for Use

