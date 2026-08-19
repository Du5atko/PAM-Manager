# Bundle Templates Integration Guide

**Version:** 1.0.0  
**Created:** 2026-08-16  
**Location:** `/home/ghost/scripty/PAM-config/pam.modules/Generic.Templates/`

---

## 📌 Overview

Bundle templates in `/pam.modules/Generic.Templates/` provide the **composite configuration** layer for PAM deployments. They orchestrate elements, manage dependencies, and define deployment procedures.

---

## 🎯 Architecture

### Three-Tier Template Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│  Bundle Template (pam.modules/Generic.Templates/)           │
│  ├─ Combines multiple elements                              │
│  ├─ Defines service mappings                                │
│  ├─ Lists platform requirements                             │
│  └─ References installation scripts                         │
└──────────────────────────────────────────────────────────────┘
                         ↓ Uses
┌──────────────────────────────────────────────────────────────┐
│  Element Templates (pam.modules/Element.Templates/)          │
│  ├─ Combines 1-3 fragments                                  │
│  ├─ Defines feature-level PAM configuration                 │
│  ├─ Specifies PAM service requirements (login, sshd, etc)  │
│  └─ Lists management tools                                  │
└──────────────────────────────────────────────────────────────┘
                         ↓ Assembles
┌──────────────────────────────────────────────────────────────┐
│  Fragment Templates (pam.modules/Fragment.Templates/)        │
│  ├─ Single PAM module definition                            │
│  ├─ Module parameters and options                           │
│  ├─ Control flags and ordering                              │
│  └─ Platform-specific package information                   │
└──────────────────────────────────────────────────────────────┘
```

---

## 📂 File Organization

### Bundle Template Components

Each bundle in `/pam.modules/Generic.Templates/` consists of:

1. **JSON metadata file**
   - Location: `bundle-{name}.json`
   - Contains: Configuration, dependencies, requirements
   - Size: 3-8 KB per bundle
   - Format: Standardized JSON schema

### Directory Structure

```
/home/ghost/scripty/PAM-config/
├── pam_manager/
│   └── Generic.Templates/
│       ├── 01-yubikey-basic.msh (installation script)
│       ├── 02-yubikey-central.msh
│       ├── ... (12 .msh scripts)
│       └── COMPLETION-REPORT.txt
│
├── pam.modules/
│   ├── Generic.Templates/ ← Bundle templates (composite)
│   │   ├── bundle-*.json (12 bundles)
│   │   └── BUNDLE-CATALOG.md (this documentation)
│   │
│   ├── Element.Templates/ ← Feature templates
│   │   ├── element-*.json (12 elements)
│   │   └── ELEMENT-CATALOG.md
│   │
│   ├── Fragment.Templates/ ← Module templates
│   │   ├── fragment.*.json (14 fragments)
│   │   └── FRAGMENT-CATALOG.md
│   │
│   └── Service.Templates/
│       └── (Reserved for service-specific configs)
```

---

## 🔗 Bundle-to-Element Mapping

### One-to-One Mappings (10 bundles)

```
bundle-yubikey-basic-auth.json
  └─ element-yubikey-basic-mfa.json

bundle-yubikey-central-auth.json
  └─ element-yubikey-central-mfa.json

bundle-yubikey-emergency.json
  └─ element-yubikey-emergency-rescue.json

bundle-user-messaging.json
  └─ element-user-messaging.json

bundle-session-isolation.json
  └─ element-session-isolation.json

bundle-access-time-control.json
  └─ element-access-time-control.json

bundle-resource-limits.json
  └─ element-resource-limits.json

bundle-environment-config.json
  └─ element-environment-configuration.json

bundle-group-permissions.json
  └─ element-group-based-permissions.json

bundle-otp-mfa.json
  └─ element-otp-mfa.json
```

### Multi-Element Mapping (2 bundles with potential multi-element support)

```
bundle-brute-force-protection.json
  └─ element-brute-force-protection.json
     (Could combine with element-emergency-rescue for emergency+brute-force)

bundle-certificate-otp-3fa.json
  └─ element-certificate-otp-3fa.json
     (Could be extended with additional elements)
```

---

## 📊 Bundle Metadata Structure

### Required Fields

Every bundle JSON includes:

```json
{
  "id": "bundle-unique-identifier",
  "bundle_name": "Human-readable name for administrators",
  "version": "1.0.0",
  "title": "Short descriptive title",
  "description": "Full description of what this bundle does",
  "category": "authentication|session|access_control|security",
  "security_level": "low|medium|high|critical",
  "pam_services": ["login", "sshd"],
  "type": "Bundle",
  "elements": [
    {
      "id": "element-unique-id",
      "import": "../Element.Templates/element-name.json",
      "required": true
    }
  ]
}
```

### Service Configuration

```json
"services": [
  {
    "name": "login",
    "type": "standard",
    "config_file": "/etc/pam.d/login"
  },
  {
    "name": "sshd",
    "type": "standard",
    "config_file": "/etc/pam.d/sshd"
  }
]
```

### Platform Support

```json
"platforms": {
  "debian_ubuntu": {
    "packages": ["libpam-u2f", "pamu2fcfg"],
    "package_manager": "apt"
  },
  "fedora_rhel": {
    "packages": ["pam-u2f", "pamu2fcfg"],
    "package_manager": "dnf"
  },
  "alpine": {
    "packages": ["pam-u2f"],
    "package_manager": "apk"
  },
  "arch": {
    "packages": ["pam-u2f"],
    "package_manager": "pacman"
  }
}
```

### Deployment Information

```json
"installation_script": "01-yubikey-basic.msh",
"deployment_requirements": [
  "YubiKey device for each user",
  "pamu2fcfg enrollment tool"
],
"management_tools": [
  "yubikey-u2f-init.sh"
],
"configuration_files": [
  "~/.config/Yubico/u2f_keys (per-user)"
],
"testing_steps": [
  "1. User enrollment: pamu2fcfg",
  "2. Test login with password + YubiKey"
]
```

---

## 🚀 How to Use Bundle Templates

### Step 1: Load Bundle

```bash
# Load bundle template
PAM_BUNDLE="/home/ghost/scripty/PAM-config/pam.modules/Generic.Templates/bundle-yubikey-basic-auth.json"

# Parse metadata
bundle_name=$(jq -r '.bundle_name' "$PAM_BUNDLE")
elements=$(jq -r '.elements[].import' "$PAM_BUNDLE")
```

### Step 2: Import Elements

```bash
# For each element referenced in bundle
for element_ref in $elements; do
    element_file="/home/ghost/scripty/PAM-config/pam.modules/Generic.Templates/../Element.Templates/$(basename "$element_ref")"
    
    # Load element configuration
    element_config=$(cat "$element_file")
done
```

### Step 3: Extract PAM Configuration

```bash
# From elements, extract PAM rules
pam_rules=$(echo "$element_config" | jq -r '.pam_configuration.auth[]')

# Apply to services
for service in login sshd sudo; do
    # Update /etc/pam.d/$service with rules
done
```

### Step 4: Install Dependencies

```bash
# Get platform type
if [ -f /etc/os-release ]; then
    . /etc/os-release
fi

# Extract packages from bundle
packages=$(jq -r ".platforms.${OS}.packages[]" "$PAM_BUNDLE")
pkg_manager=$(jq -r ".platforms.${OS}.package_manager" "$PAM_BUNDLE")

# Install
$pkg_manager install -y $packages
```

### Step 5: Deploy

```bash
# Run installation script
script=$(jq -r '.installation_script' "$PAM_BUNDLE")
bash "/home/ghost/scripty/PAM-config/pam_manager/Generic.Templates/$script"
```

---

## 🔄 Bundle Processing Workflow

### Bundle Initialization

```
┌─────────────────────────────────┐
│  Load Bundle JSON               │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│  Parse Metadata                 │
│  - ID, Name, Version            │
│  - Category, Security Level     │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│  Resolve Elements               │
│  - Load Element Templates       │
│  - Validate References          │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│  Extract Requirements           │
│  - Packages                     │
│  - Configuration Files          │
│  - Management Tools             │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│  Generate Deployment Plan       │
│  - Installation Steps           │
│  - Testing Procedures           │
│  - Rollback Strategy            │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│  Execute Deployment             │
│  - Install Packages             │
│  - Configure PAM                │
│  - Run Tests                    │
└─────────────────────────────────┘
```

---

## 🎯 Use Cases

### Scenario 1: Deploy Single Bundle

```bash
#!/bin/bash

# Load bundle
BUNDLE="bundle-brute-force-protection.json"

# Extract information
SCRIPT=$(jq -r '.installation_script' "$BUNDLE")

# Run installer
bash "$SCRIPT"
```

### Scenario 2: Deploy Multiple Bundles

```bash
#!/bin/bash

# Deploy combination
declare -a BUNDLES=(
    "bundle-brute-force-protection.json"
    "bundle-session-isolation.json"
    "bundle-otp-mfa.json"
)

for bundle in "${BUNDLES[@]}"; do
    script=$(jq -r '.installation_script' "$bundle")
    echo "Deploying $bundle..."
    bash "$script"
done
```

### Scenario 3: Create Custom Policy

```bash
#!/bin/bash

# Build policy from specific bundles
POLICY_BUNDLES=(
    "bundle-brute-force-protection.json"
    "bundle-yubikey-central-auth.json"
    "bundle-access-time-control.json"
)

# Extract all elements
for bundle_file in "${POLICY_BUNDLES[@]}"; do
    elements=$(jq -r '.elements[].import' "$bundle_file")
    echo "Elements from $bundle_file: $elements"
done
```

---

## 📋 Deployment Checklist

For each bundle deployment:

- [ ] Read bundle metadata
- [ ] Verify platform support
- [ ] Check system requirements
- [ ] Install packages
- [ ] Review configuration changes
- [ ] Backup existing PAM config
- [ ] Apply new configuration
- [ ] Test login via each service
- [ ] Run diagnostic tools
- [ ] Document changes
- [ ] Store rollback procedure

---

## 🔍 Bundle Validation

### Pre-Deployment Checks

```bash
# Verify bundle JSON syntax
jq empty bundle-*.json

# Check element references
jq '.elements[].import' bundle-*.json | while read ref; do
    test -f "${ref//../$(dirname $0)/..}" && echo "✓ $ref" || echo "✗ $ref"
done

# Verify installation scripts exist
jq -r '.installation_script' bundle-*.json | while read script; do
    test -f "../../pam_manager/Generic.Templates/$script" && echo "✓ $script" || echo "✗ $script"
done
```

---

## 🔐 Security Considerations

### Bundle Security Levels

| Level | Deployment | Use Case |
|-------|-----------|----------|
| CRITICAL | Mandatory for all systems | Brute force, emergency access |
| HIGH | Required for secure systems | MFA, session isolation |
| MEDIUM | Recommended | Access control, resource limits |
| LOW | Optional | Messaging, environment config |

### Security Best Practices

1. **Always include** CRITICAL bundles
2. **Deploy in order** (security → functionality → convenience)
3. **Test each** before production
4. **Monitor for issues** after deployment
5. **Keep backups** of original PAM configs

---

## 📞 Support and Troubleshooting

### Common Issues

#### Bundle not loading
```bash
# Check JSON syntax
jq . bundle-yubikey-basic-auth.json
```

#### Element reference broken
```bash
# Verify element exists
ls -la ../Element.Templates/element-yubikey-basic-mfa.json
```

#### Installation script missing
```bash
# Find available scripts
ls -la ../../pam_manager/Generic.Templates/*.msh
```

---

## 📊 Statistics

- **Total Bundles:** 12
- **Total Elements Referenced:** 12
- **Total Fragments Used:** 14
- **Supported Platforms:** 5 (Debian, Fedora, Alpine, Arch, FreeBSD mention)
- **PAM Services Covered:** login, sshd, sudo, su

---

## 🔄 Workflow Summary

```
User Request (e.g., "Enable YubiKey MFA")
           ↓
Load Bundle Template
  ├─ bundle-yubikey-basic-auth.json
  └─ Reads: metadata, elements, platforms
           ↓
Resolve Elements
  ├─ element-yubikey-basic-mfa.json
  └─ Gets: fragments, PAM rules, packages
           ↓
Extract Configuration
  ├─ pam_unix (authentication)
  ├─ pam_u2f (YubiKey)
  └─ Installation requirements
           ↓
Execute Deployment
  ├─ Install packages
  ├─ Configure PAM services
  ├─ Create user tools
  └─ Test functionality
           ↓
Complete
  └─ YubiKey MFA enabled
```

---

## 📝 Version History

**v1.0.0** (2026-08-16)
- Created 12 bundle templates
- Documented architecture and workflow
- Provided usage examples
- Added deployment checklists

---

## 🔗 Related Files

- [Bundle Catalog](./BUNDLE-CATALOG.md)
- [Element Catalog](../Element.Templates/ELEMENT-CATALOG.md)
- [Fragment Catalog](../Fragment.Templates/FRAGMENT-CATALOG.md)

---

**Last Updated:** 2026-08-16  
**Status:** ✅ Complete with documentation

