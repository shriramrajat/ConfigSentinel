from typing import Literal


Vendor = Literal["cisco", "juniper", "arista", "panos", "fortinet", "unknown"]

# ---------------------------------------------------------------------------
# Juniper JunOS marker patterns
# ---------------------------------------------------------------------------
#
# JunOS-specific markers used for detection.  All are checked against the
# stripped, lowercased version of each line unless noted.
#
# Chosen markers and their rationale:
#   "## "     – JunOS file-level comment header (double-hash); extremely rare
#               in non-JunOS configs.  Checked on the raw (non-lowercased)
#               stripped line because the prefix is case-sensitive in practice.
#   "system {" – The root-level system block opener.  Present in virtually
#               every JunOS config.  The brace distinguishes it from a Cisco
#               "system" keyword (which Cisco IOS does not use at global scope).
#   "interfaces {" – Juniper top-level interfaces block.  Not used by Cisco
#               at global scope in the same brace-delimited syntax.
#   "security {" – Juniper top-level security block.  Same rationale.
#
# Markers deliberately NOT used:
#   "version X;" – The semicolon-terminated form could overlap with IOS banners
#               or other configs; excluded to avoid false positives.
# ---------------------------------------------------------------------------

_JUNIPER_RAW_MARKERS = (
    "## ",   # JunOS double-hash file comment (raw prefix, case-sensitive)
)

_JUNIPER_LOWER_MARKERS = (
    "system {",
    "interfaces {",
    "security {",
    "routing-options {",
    "protocols {",
    "authentication-order",
    "root-authentication",
)

# ---------------------------------------------------------------------------
# Cisco IOS / IOS-XE marker patterns
# ---------------------------------------------------------------------------
#
# The existing first-match behavior is preserved.  Cisco markers are checked
# before Juniper ones so that a config with both (ambiguous) resolves to Cisco,
# consistent with the prior implementation.
# ---------------------------------------------------------------------------

_CISCO_LOWER_MARKERS = (
    "version ",       # IOS version header: "version 17.9" (no semicolon)
    "hostname ",      # Global hostname directive
    "enable secret ", # Privileged credential
    "ip ssh version ",# SSH version directive
)



# ---------------------------------------------------------------------------
# Arista EOS marker patterns
# ---------------------------------------------------------------------------
#
# EOS uses IOS-like flat config syntax but has distinct markers:
#   "eos sdk" / "aaa root" / "daemon"
# We check for patterns that unambiguously identify EOS.
# ---------------------------------------------------------------------------

_ARISTA_LOWER_MARKERS = (
    "aaa root secret",       # EOS-specific privileged credential format
    "management api http-commands",  # EOS REST API management block
    "daemon ",               # EOS extensibility daemon directive
    "event-handler ",        # EOS event-handler
    "on-startup",            # EOS event-handler sub-command
)

# ---------------------------------------------------------------------------
# Palo Alto PAN-OS marker patterns
# ---------------------------------------------------------------------------
#
# PAN-OS configuration uses XML or a set-command format with distinctive
# prefixes not found in other vendors.
# ---------------------------------------------------------------------------

_PANOS_LOWER_MARKERS = (
    "set deviceconfig system hostname",  # PAN-OS set-command form
    "set address ",          # PAN-OS address object
    "set security policy ",  # PAN-OS security policy
    "set network interface ethernet",
    "<config version=",      # PAN-OS XML config
    "<mgt-config>",
    "<deviceconfig>",
)

# ---------------------------------------------------------------------------
# Fortinet FortiOS marker patterns
# ---------------------------------------------------------------------------
#
# FortiOS uses a block-based config with distinctive 'config' / 'set' / 'end'
# keywords in a non-IOS context.
# ---------------------------------------------------------------------------

_FORTIOS_LOWER_MARKERS = (
    "config system global",  # FortiOS global config block
    "config system interface",
    "config firewall policy",
    "config vpn ssl settings",
    "set admintimeout ",     # FortiOS-specific admin timeout
    "set admin-sport ",      # FortiOS HTTPS admin port
)



def detect_vendor(config: str) -> Vendor:
    """Detect the vendor from configuration content.

    Uses a first-match scan over all lines.  Order of evaluation:
    1. Cisco (most common, checked first)
    2. Juniper JunOS
    3. Arista EOS
    4. Palo Alto PAN-OS
    5. Fortinet FortiOS

    An ambiguous config that matches multiple vendors resolves to the first
    matched vendor — this is a documented, accepted trade-off.

    Parameters
    ----------
    config:
        Raw configuration text.

    Returns
    -------
    Vendor
        One of ``"cisco"``, ``"juniper"``, ``"arista"``, ``"panos"``,
        ``"fortinet"``, or ``"unknown"``.
    """
    lines = config.splitlines()

    for line in lines:
        stripped = line.strip()
        normalized = stripped.lower()

        # ---- Cisco checks (evaluated first) --------------------------------
        for marker in _CISCO_LOWER_MARKERS:
            if normalized.startswith(marker) and normalized[len(marker):].strip():
                return "cisco"

        # ---- Juniper raw-prefix checks (case-sensitive) --------------------
        for marker in _JUNIPER_RAW_MARKERS:
            if stripped.startswith(marker):
                return "juniper"

        # ---- Juniper lowercased marker checks ------------------------------
        for marker in _JUNIPER_LOWER_MARKERS:
            if normalized == marker.rstrip() or normalized.startswith(marker):
                return "juniper"

        if normalized.startswith("host-name ") and normalized.endswith(";"):
            return "juniper"

        # ---- Arista EOS checks ---------------------------------------------
        for marker in _ARISTA_LOWER_MARKERS:
            if normalized.startswith(marker):
                return "arista"

        # ---- Palo Alto PAN-OS checks ---------------------------------------
        for marker in _PANOS_LOWER_MARKERS:
            if normalized.startswith(marker):
                return "panos"

        # ---- Fortinet FortiOS checks ---------------------------------------
        for marker in _FORTIOS_LOWER_MARKERS:
            if normalized.startswith(marker):
                return "fortinet"

    return "unknown"