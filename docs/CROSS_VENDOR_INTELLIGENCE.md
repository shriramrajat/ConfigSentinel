# Cross-Vendor Security Intelligence Architecture

## Overview
ConfigSentinel normalizes vendor-specific syntax into canonical security intents.

### Supported Vendors
1. **Cisco IOS / IOS-XE**
2. **Juniper JunOS**
3. **Arista EOS**
4. **Fortinet FortiOS**
5. **Palo Alto PAN-OS**

### Core Security Intents
- `SSH_VERSION_ENFORCED`
- `TELNET_DISABLED`
- `EXEC_TIMEOUT_CONFIGURED`
- `PASSWORD_ENCRYPTION_ENABLED`
- `AAA_AUTHENTICATION_ENABLED`
- `HTTP_MANAGEMENT_DISABLED`
- `LOGGING_REMOTE_ENABLED`
- `NTP_AUTHENTICATION_ENABLED`
- `SNMP_COMMUNITY_SECURED`
- `UNNECESSARY_SERVICES_DISABLED`

### Policy Translation Engine
Allows security architects to define vendor-neutral policy requirements (e.g. "Disable Insecure Remote Management") and translate them into specific configuration directives across Cisco, Juniper, Arista, FortiOS, and PAN-OS.

### What-If Compliance Simulator
Evaluates the posture score and risk reduction resulting from fixing selected security intents without modifying persistent audit history or configurations.
