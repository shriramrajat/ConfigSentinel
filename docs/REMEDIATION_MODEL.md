# Remediation & Verification Architecture

## Multi-Vendor Remediation Catalog
Provides structured, verified remediation syntax across 5 supported network vendors:
- Cisco IOS / IOS-XE
- Juniper JunOS
- Arista EOS
- Fortinet FortiOS
- Palo Alto PAN-OS

## Post-Remediation Verification Comparator
Executes deterministic compliance evaluation on updated configuration text following external remediation application:
- **`FIX VERIFIED`**: Control transitions to PASS state.
- **`FIX NOT VERIFIED`**: Control remains in non-compliant state.
