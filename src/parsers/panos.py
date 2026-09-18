"""
parsers.panos
~~~~~~~~~~~~~

Minimal structural parser for Palo Alto PAN-OS device configurations.

Design Intent
-------------
PAN-OS uses set-command CLI format ('set deviceconfig system hostname PAN-01')
or XML element format. This parser extracts hostname, directives, items,
and line numbers into a vendor-neutral ``NormalizedConfig`` with ``vendor="panos"``.
"""

from __future__ import annotations

import re
from src.normalization.model import ConfigItem, ConfigSection, NormalizedConfig


def parse_panos(config_text: str) -> NormalizedConfig:
    """Parse Palo Alto PAN-OS configuration text into a NormalizedConfig object."""
    global_items: list[ConfigItem] = []
    sections: list[ConfigSection] = []
    hostname: str | None = None

    lines = config_text.splitlines()

    for idx, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()

        # Skip blank lines and comments
        if not stripped or stripped.startswith("<!--") or stripped.startswith("#"):
            continue

        # Check for hostname setting in set-format or XML-format
        if "hostname" in stripped.lower():
            set_match = re.search(r'set\s+deviceconfig\s+system\s+hostname\s+["\']?([^"\']+)["\']?', stripped, re.IGNORECASE)
            xml_match = re.search(r'<hostname>([^<]+)</hostname>', stripped, re.IGNORECASE)
            if set_match:
                hostname = set_match.group(1).strip()
            elif xml_match:
                hostname = xml_match.group(1).strip()

        parts = stripped.split(maxsplit=1)
        key = parts[0]
        value = parts[1] if len(parts) > 1 else None

        item = ConfigItem(key=key, value=value, raw_line=raw_line, line_number=idx)

        # Categorize into sections if prefix indicates object section (e.g. set address, set security policy)
        if stripped.lower().startswith("set security policy"):
            _get_or_create_section(sections, "security-policy").items.append(item)
        elif stripped.lower().startswith("set address"):
            _get_or_create_section(sections, "address-objects").items.append(item)
        elif stripped.lower().startswith("set network"):
            _get_or_create_section(sections, "network").items.append(item)
        else:
            global_items.append(item)

    return NormalizedConfig(
        vendor="panos",
        hostname=hostname,
        global_items=global_items,
        sections=sections,
    )


def _get_or_create_section(sections: list[ConfigSection], name: str) -> ConfigSection:
    for s in sections:
        if s.name == name:
            return s
    new_sec = ConfigSection(name=name, items=[])
    sections.append(new_sec)
    return new_sec
