"""
parsers.arista
~~~~~~~~~~~~~~

Minimal structural parser for Arista EOS device configurations.

Design Intent
-------------
Arista EOS uses a Cisco IOS-like syntax with EOS-specific directives.
This parser extracts hostname, global items, block sections, and line numbers
into a vendor-neutral ``NormalizedConfig`` with ``vendor="arista"``.
"""

from __future__ import annotations

from src.normalization.model import ConfigItem, ConfigSection, NormalizedConfig


def parse_arista(config_text: str) -> NormalizedConfig:
    """Parse Arista EOS configuration text into a NormalizedConfig object."""
    global_items: list[ConfigItem] = []
    sections: list[ConfigSection] = []
    current_section: ConfigSection | None = None
    hostname: str | None = None

    lines = config_text.splitlines()

    for idx, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()

        # Skip blank lines and full-line comments
        if not stripped or stripped.startswith("!") or stripped.startswith("#"):
            continue

        # Check for hostname
        if stripped.lower().startswith("hostname "):
            parts = stripped.split(maxsplit=1)
            if len(parts) > 1:
                hostname = parts[1].strip()

        # Check if indented item inside a block section
        is_indented = raw_line.startswith(" ") or raw_line.startswith("\t")

        if is_indented and current_section is not None:
            # Sub-item inside current section block
            parts = stripped.split(maxsplit=1)
            key = parts[0]
            value = parts[1] if len(parts) > 1 else None
            item = ConfigItem(key=key, value=value, raw_line=raw_line, line_number=idx)
            current_section.items.append(item)
        else:
            # End previous section if any
            if current_section is not None:
                sections.append(current_section)
                current_section = None

            # Check if this line starts a block section (e.g., interface, router, aaa, etc.)
            if _is_block_header(stripped):
                current_section = ConfigSection(name=stripped, items=[])
            else:
                # Top-level global directive
                parts = stripped.split(maxsplit=1)
                key = parts[0]
                value = parts[1] if len(parts) > 1 else None
                item = ConfigItem(key=key, value=value, raw_line=raw_line, line_number=idx)
                global_items.append(item)

    if current_section is not None:
        sections.append(current_section)

    return NormalizedConfig(
        vendor="arista",
        hostname=hostname,
        global_items=global_items,
        sections=sections,
    )


def _is_block_header(line: str) -> bool:
    """Return True if line opens a multi-line block section in Arista EOS."""
    block_prefixes = (
        "interface ",
        "router ",
        "vlan ",
        "management api ",
        "daemon ",
        "event-handler ",
        "line ",
        "aaa ",
    )
    lower = line.lower()
    return any(lower.startswith(prefix) for prefix in block_prefixes)
