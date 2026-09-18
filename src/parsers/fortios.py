"""
parsers.fortios
~~~~~~~~~~~~~~~

Minimal structural parser for Fortinet FortiOS device configurations.

Design Intent
-------------
FortiOS uses block configuration delimited by ``config <block>`` and ``end``.
Inner directives use ``set <key> <value>``, ``edit <id>``, and ``next``.
This parser extracts hostname, configuration blocks, items, and line numbers
into a vendor-neutral ``NormalizedConfig`` with ``vendor="fortinet"``.
"""

from __future__ import annotations

import re
from src.normalization.model import ConfigItem, ConfigSection, NormalizedConfig


def parse_fortios(config_text: str) -> NormalizedConfig:
    """Parse Fortinet FortiOS configuration text into a NormalizedConfig object."""
    global_items: list[ConfigItem] = []
    sections: list[ConfigSection] = []
    current_section: ConfigSection | None = None
    hostname: str | None = None

    lines = config_text.splitlines()

    for idx, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()

        # Skip blank lines and comments (FortiOS uses #)
        if not stripped or stripped.startswith("#"):
            continue

        # Check for hostname setting: 'set hostname "FORTIGATE-FW-01"'
        if "set hostname" in stripped.lower():
            match = re.search(r'set\s+hostname\s+["\']?([^"\']+)["\']?', stripped, re.IGNORECASE)
            if match:
                hostname = match.group(1).strip()

        lower = stripped.lower()

        if lower.startswith("config "):
            # Start of a FortiOS block section (e.g., 'config system global')
            if current_section is not None:
                sections.append(current_section)
            current_section = ConfigSection(name=stripped, items=[])
        elif lower == "end" or lower == "next":
            # End of block or edit context
            if current_section is not None and lower == "end":
                sections.append(current_section)
                current_section = None
        else:
            # Item line (e.g. 'set admin-sport 443' or 'edit 1')
            parts = stripped.split(maxsplit=1)
            key = parts[0]
            value = parts[1] if len(parts) > 1 else None

            item = ConfigItem(key=key, value=value, raw_line=raw_line, line_number=idx)
            if current_section is not None:
                current_section.items.append(item)
            else:
                global_items.append(item)

    if current_section is not None:
        sections.append(current_section)

    return NormalizedConfig(
        vendor="fortinet",
        hostname=hostname,
        global_items=global_items,
        sections=sections,
    )
