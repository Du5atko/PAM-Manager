# Generic Template Specification

This document describes Generic Templates - pre-built, ready-to-deploy PAM policy bundles for common security scenarios.

## Overview

Generic Templates are complete policy packages that combine Fragments, Elements, and Services for specific security use cases. Templates provide a starting point for deployment and can be customized for specific organizational needs.

**Key Features**:
- Pre-built security policies
- Tested configurations
- Documentation and deployment scripts
- Compliance mapping
- Platform-specific support
- Management tools included

## Template Structure

### Bundle Components

Each template bundle contains:

1. **Template Metadata** (`XXXXXX-name.json`)
   - Description and purpose
   - Security level
   - Prerequisites
   - Component list

2. **Installation Script** (`XXXXXX-name.msh`)
   - Automated deployment
   - Package detection
   - Configuration generation
   - Backup handling

3. **Documentation**
   - Detailed README
   - Configuration explanation
   - Troubleshooting guide
   - Compliance information

### Template Metadata Schema

```json
{
  "id": "01-yubikey-basic",
  "name": "YubiKey Basic MFA",
  "version": "1.0.0",
  "description": "Per-user YubiKey FIDO/U2F multi-factor authentication",
  "category": "authentication",
  "security_level": "high",
  "platforms": ["Debian", "Fedora", "Alpine", "Arch"],
  "prerequisites": {
    "packages": ["libpam-yubico", "pam_yubico"],
    "services": ["sshd"],
    "capabilities": ["mfa", "u2f"]
  },
  "components": {
    "fragments": [
      "pam_yubico/auth/u2f-strict"
    ],
    "elements": [
      "sshd/auth_yubikey"
    ],
    "services": [
      "sshd-yubikey"
    ]
  },
  "use_cases": [
    "SSH key-based MFA",
    "Remote access protection",
    "Phishing-resistant authentication"
  ],
  "compliance": [
    "FIPS 140-2",
    "NIST SP 800-63B",
    "PCI-DSS 8.3"
  ]
}
```

## Available Templates

### Authentication Templates

#### 01 - YubiKey Basic MFA

**Purpose**: Per-user YubiKey FIDO/U2F multi-factor authentication

**Description**: Adds YubiKey support for SSH login as secondary factor after password. Each user manages their own YubiKey.

**Components**:
- Fragment: pam_yubico/auth/u2f-strict
- Element: sshd/auth_yubikey
- Service: sshd-yubikey

**Use Cases**:
- Remote SSH access protection
- Developer/admin secure access
- Phishing-resistant MFA
- Hardware security key deployment

**Security Level**: HIGH

**Compliance**:
- FIPS 140-2 (cryptographic key)
- NIST SP 800-63 (out-of-band verification)
- PCI-DSS (MFA requirement)

**Installation**:
```bash
./01-yubikey-basic.msh install
```

**Configuration**:
- User enrollment: `ykpersonalize` tool
- Mapping: /etc/security/yubikey_mapping
- Timeout: 30 seconds per attempt

**Troubleshooting**:
- No device detected: Check USB permissions
- Authentication fails: Verify yubikey_mapping
- Timeout issues: Adjust timeout parameter

**Performance Impact**: Minimal (local USB check)

---

#### 02 - YubiKey Central Management

**Purpose**: Centralized YubiKey management for enterprise deployments

**Description**: Manages YubiKeys through central directory with LDAP attribute mapping. Supports key revocation and audit logging.

**Components**:
- Fragment: pam_yubico/auth/u2f-directory-aware
- Element: sshd/auth_yubikey_central
- Service: sshd-yubikey-central

**Use Cases**:
- Enterprise SSH access control
- Centralized key lifecycle management
- Compliance reporting
- Large-scale deployments

**Security Level**: CRITICAL

**Compliance**:
- FIPS 140-2
- NIST SP 800-63
- PCI-DSS
- SOC 2 (key management)

**Installation**:
```bash
./02-yubikey-central.msh install --ldap-server ldap.example.com
```

**Configuration**:
- LDAP mapping: yubiKeyId attribute
- Revocation list: /etc/security/yubikey_revoked
- Audit logging: syslog or central logging

**Management Tools**:
- yubikey-register - Enroll new key
- yubikey-revoke - Deactivate key
- yubikey-audit - List active keys
- yubikey-backup - Export key mappings

---

#### 03 - YubiKey Rescue Account

**Purpose**: Emergency recovery account with YubiKey protection

**Description**: Provides emergency access mechanism protected with YubiKey. For critical system access when regular authentication fails.

**Components**:
- Fragment: pam_yubico/auth/u2f-emergency
- Element: rescue/auth_emergency
- Service: rescue-account

**Use Cases**:
- Disaster recovery
- Emergency access
- System maintenance
- Security incident response

**Security Level**: CRITICAL

**Compliance**:
- FIPS 140-2
- Disaster recovery requirements
- Audit trail requirement

**Installation**:
```bash
./03-yubikey-rescue.msh create-rescue-account --username rescue-admin
```

**Management Tools**:
- create-rescue-account - Setup rescue account
- test-rescue-access - Verify recovery access
- revoke-rescue-access - Disable rescue account
- rescue-audit-log - Review access history

---

#### 11 - MFA OTP/HOTP (Mobile Authenticator)

**Purpose**: Mobile authenticator two-factor authentication

**Description**: Time-based or event-based OTP (TOTP/HOTP) authentication using smartphone authenticator apps (Google Authenticator, Authy, FreeOTP).

**Components**:
- Fragment: pam_google_authenticator/auth/totp-standard
- Element: sshd/auth_totp
- Service: sshd-mfa-totp

**Use Cases**:
- Remote SSH access
- VPN authentication
- Web application access
- User-friendly MFA

**Security Level**: HIGH

**Compliance**:
- NIST SP 800-63 (OTP)
- HIPAA (MFA requirement)
- SOC 2 (authentication)

**Installation**:
```bash
./11-mfa-otp-hotp.msh install
```

**Configuration**:
- Secret file: ~/.google_authenticator
- Window size: 1 (strict) or 3 (permissive)
- Recovery codes: Generated per user
- Disallow reuse: Enabled by default

**Enrollment Process**:
1. User runs: `google-authenticator`
2. QR code scanned with smartphone
3. Recovery codes saved
4. First OTP entered for verification

**Management Tools**:
- enroll-otp - Register new user
- test-otp - Verify OTP setup
- view-recovery-codes - Display backup codes
- reset-otp - Re-generate secrets

---

#### 12 - MFA Certificate + OTP (Smart Card + Authenticator)

**Purpose**: Three-factor authentication combining certificate, OTP, and password

**Description**: Requires smart card (certificate) AND OTP AND password for highest security. For critical system access.

**Components**:
- Fragment: pam_pkcs11/auth/smartcard-strict
- Fragment: pam_google_authenticator/auth/totp-strict
- Fragment: pam_unix/auth/password
- Element: critical/auth_3fa
- Service: critical-access

**Use Cases**:
- Privileged system access
- High-security environments
- Financial systems
- Government/defense deployments

**Security Level**: CRITICAL

**Compliance**:
- FIPS 140-2 (cryptographic modules)
- PCI-DSS (MFA for privileged access)
- HIPAA (strong authentication)
- SOC 2 (multi-factor auth)

**Installation**:
```bash
./12-mfa-cert-otp.msh install --certificate-ca /path/to/ca.crt
```

**Configuration**:
- Certificate CA: Root certificate path
- Certificate revocation: CRL or OCSP
- OTP settings: Strict time window
- Audit logging: All authentication attempts

**Management Tools**:
- enroll-certificate - Issue user certificate
- enroll-otp - Setup OTP alongside certificate
- check-certificate-expiry - Verify certificate validity
- audit-access - Review all authentication attempts

---

### Access Control Templates

#### 06 - Time-Based Login Restrictions

**Purpose**: Restrict login by time of day or day of week

**Description**: Allow authentication only during specific business hours or days. Useful for shift-based access control and security policies.

**Components**:
- Fragment: pam_time/auth/business-hours
- Element: login/time_restricted
- Service: login-time-restricted

**Use Cases**:
- Shift-based access
- Secure facility access
- Business hours enforcement
- Compliance requirements

**Security Level**: MEDIUM

**Configuration**:
- Business hours: 8:00-18:00 weekdays
- Override mechanism: sudo access only
- Logging: syslog entries
- Time source: System NTP

**Management Tools**:
- list-time-restrictions - View current rules
- update-time-policy - Modify restrictions
- test-time-access - Verify policy

---

#### 07 - Concurrent Login Limits

**Purpose**: Limit concurrent sessions and resource usage per user

**Description**: Restrict number of concurrent logins and resource consumption (CPU, memory, file descriptors) per user.

**Components**:
- Fragment: pam_limits/session/resource-constraints
- Fragment: pam_lastlog/session/concurrent-check
- Element: login/limits_enforced
- Service: login-limited

**Use Cases**:
- Multi-user system protection
- Resource fairness
- DoS prevention
- Shared system management

**Security Level**: MEDIUM

**Configuration**:
- Max logins per user: 2-5
- Max processes: 256
- Max open files: 2048
- Memory limits: Configurable

**Management Tools**:
- check-user-limits - View per-user limits
- update-limits - Modify limit values
- list-concurrent-sessions - Active sessions

---

#### 08 - Intruder Lockout

**Purpose**: Automatic account lockout after failed login attempts

**Description**: Lock account after N failed attempts for M minutes. Provides rate-limiting protection against brute-force attacks.

**Components**:
- Fragment: pam_faillock/auth/lockout-protection
- Element: login/auth_lockout
- Service: login-with-lockout

**Use Cases**:
- Attack prevention
- Compliance requirement
- Brute-force protection
- Standard security baseline

**Security Level**: HIGH

**Compliance**:
- PCI-DSS (account lockout)
- NIST SP 800-63 (rate limiting)
- SOC 2 (attack prevention)

**Configuration**:
- Failed attempts: 5
- Lockout duration: 30 minutes
- Silent mode: No user notification
- Audit logging: All lockouts

**Management Tools**:
- check-lockout-status - View locked accounts
- unlock-account - Manually unlock user
- view-lockout-log - Login attempt history
- reset-lockout-counters - Clear failed counts

---

### Session Management Templates

#### 04 - User-Specific MOTD Display

**Purpose**: Display personalized Message of The Day per user

**Description**: Show custom MOTD based on user, login type, or other attributes. Useful for compliance notices and user information.

**Components**:
- Fragment: pam_motd/session/user-aware
- Element: login/motd_display
- Service: login-with-motd

**Use Cases**:
- Compliance notices
- System information
- User-specific messages
- Security disclaimers

**Security Level**: LOW

**Configuration**:
- System MOTD: /etc/motd
- User MOTD: ~/motd
- Template: Customizable per organization

---

#### 05 - Private Namespace (Isolated /tmp)

**Purpose**: Create isolated temporary file namespace per user

**Description**: Each user gets private /tmp and /var/tmp. Prevents inter-user file access and improves security isolation.

**Components**:
- Fragment: pam_namespace/session/private-tmp
- Element: login/namespace_isolated
- Service: login-private-namespace

**Use Cases**:
- Multi-user system isolation
- Temporary file privacy
- Security hardening
- Compliance requirements

**Security Level**: HIGH

**Compliance**:
- NIST SP 800-171 (resource isolation)
- FedRAMP (data isolation)
- Government security requirements

**Configuration**:
- Namespace directory: /tmp/user-namespaces
- Cleanup policy: Auto-cleanup on logout
- Persistence: Session-based

---

#### 09 - Environment Based on Login Type

**Purpose**: Set environment variables based on login origin

**Description**: Apply different environment settings based on SSH vs. console vs. remote login. Useful for context-aware security policies.

**Components**:
- Fragment: pam_env/session/login-type-aware
- Element: login/env_context
- Service: login-context-aware

**Use Cases**:
- Context-aware security
- Environment differentiation
- Desktop vs. server distinction
- Remote access policies

**Security Level**: MEDIUM

---

#### 10 - File Permission Control by Group

**Purpose**: Set default file creation permissions (umask) based on group membership

**Description**: Apply different umask values based on user group. Restricts file access by default based on group policies.

**Components**:
- Fragment: pam_umask/session/group-based-umask
- Element: login/umask_enforced
- Service: login-umask-controlled

**Use Cases**:
- Group-based file sharing
- Compliance file permissions
- Default security settings
- Project isolation

**Security Level**: MEDIUM

---

## Template Installation

### System Requirements

**Before installing any template**:

1. **Supported Platform**
   - Verify platform in template metadata
   - Check distribution support (Debian, Fedora, Alpine, Arch)

2. **Required Packages**
   - Review prerequisite packages
   - Ensure repository access for packages

3. **System Access**
   - Root or sudo access required
   - Test account for validation
   - Rollback procedure prepared

### Installation Steps

**Standard template installation**:

```bash
# 1. Review template
cat XX-template-name.json

# 2. Run installation script
sudo ./XX-template-name.msh install

# 3. Test authentication
# Login with test account

# 4. Verify logging
grep "pam" /var/log/auth.log

# 5. If issues, rollback
sudo ./XX-template-name.msh rollback
```

**Custom parameter installation**:

```bash
sudo ./XX-template-name.msh install --parameter value
```

### Post-Installation

1. **Test Access**
   - Test with regular user account
   - Verify fallback methods
   - Check error messages

2. **Audit Logging**
   - Verify logs in /var/log/auth.log
   - Check for errors or warnings
   - Confirm event tracking

3. **Performance**
   - Measure login time
   - Check CPU/memory usage
   - Monitor for delays

4. **Documentation**
   - Document configuration
   - Record any customizations
   - Note rollback procedure

## Template Customization

### Modifying Template Configuration

1. **Edit Fragments** (in template):
   - Adjust parameters (strictness, timeouts)
   - Change platform support
   - Update documentation

2. **Edit Elements** (in template):
   - Change control flags
   - Add/remove fragments
   - Modify extended control syntax

3. **Edit Services** (in template):
   - Add/remove elements
   - Reorder elements
   - Change description

4. **Test Modified Template**:
   - Test on non-production first
   - Verify all changes
   - Document modifications

### Common Customizations

**Loosen security**:
- Change "required" to "optional"
- Extend time windows
- Increase attempt limits
- Remove secondary factors

**Tighten security**:
- Change "optional" to "required"
- Narrow time windows
- Reduce attempt limits
- Add additional factors

**Platform-specific**:
- Add/remove platform support
- Adjust package names
- Modify paths for platform

## Template Deployment Workflows

### Small Team (5-20 users)

**Recommended templates**:
1. YubiKey Basic (MFA)
2. Private Namespace (isolation)
3. Intruder Lockout (protection)

**Workflow**:
1. Install on development system
2. Test with pilot users
3. Deploy to production
4. Monitor for issues
5. Rollback if needed

### Mid-Size Enterprise (20-500 users)

**Recommended templates**:
1. YubiKey Central (managed MFA)
2. Private Namespace (isolation)
3. Time Restrictions (audit)
4. Concurrent Limits (fairness)
5. Intruder Lockout (protection)
6. MFA OTP (user-friendly backup)

**Workflow**:
1. Deploy via configuration management
2. Gradual rollout per department
3. Central monitoring
4. Regular audits
5. Update policies as needed

### Large Enterprise (500+ users)

**Recommended templates**:
- All templates as needed
- Central YubiKey management
- Private namespace everywhere
- Multiple MFA options
- Comprehensive audit logging
- Centralized policy management

**Workflow**:
1. Customize for organization
2. Deploy via configuration management
3. Phase-based rollout
4. Continuous monitoring
5. Regular compliance audits
6. Policy evolution

## Compliance and Security

### Compliance Coverage

Each template documents compliance with:
- NIST SP 800-63 (authentication guidelines)
- NIST SP 800-171 (government requirements)
- PCI-DSS (payment card security)
- HIPAA (healthcare requirements)
- SOC 2 (security controls)
- ISO 27001 (information security)
- GDPR (data protection)
- FIPS 140-2 (cryptographic modules)

### Security Best Practices

1. **Principle of Least Privilege**
   - Only enable required modules
   - Use minimal configuration
   - Restrict access appropriately

2. **Defense in Depth**
   - Stack multiple authentication factors
   - Combine different verification methods
   - Implement multiple access controls

3. **Audit and Monitoring**
   - Enable authentication logging
   - Monitor for suspicious patterns
   - Regular log review
   - Alerting on anomalies

4. **Regular Updates**
   - Keep PAM modules updated
   - Review policies regularly
   - Update as threats evolve
   - Test new templates

## Troubleshooting

### Common Issues

**Template won't install**:
- Check platform support
- Verify prerequisites installed
- Review installation logs
- Check filesystem permissions

**Authentication fails after install**:
- Test with simple login first
- Check /var/log/auth.log
- Verify fragments exist
- Review element configuration

**Performance degradation**:
- Profile which module is slow
- Check network connectivity
- Verify timeout settings
- Review caching configuration

**Audit logging not working**:
- Verify logging enabled in template
- Check syslog configuration
- Review log file permissions
- Ensure disk space available

### Rollback Procedures

If template installation causes issues:

```bash
# Automatic rollback
sudo ./XX-template-name.msh rollback

# Or manual rollback
sudo cp /etc/pam.d/service.bak /etc/pam.d/service
sudo systemctl restart ssh
```

## Best Practices

1. **Always test first** - Use non-production system
2. **Prepare rollback** - Know how to undo changes
3. **Document changes** - Record what was modified
4. **Gradual rollout** - Deploy to subset first
5. **Monitor closely** - Watch logs after deployment
6. **Get user feedback** - Verify usability
7. **Regular audits** - Review configurations
8. **Keep updated** - Apply security updates
9. **Plan succession** - Document for others
10. **Plan for emergencies** - Recovery procedures

---

For template installation details, see template documentation files.
For fragment specifications, see Fragment.template.md.
For element specifications, see Element.template.md.
For service definitions, see Service.template.md.
For overall PAM Manager information, see Readme.md.
