"""
tests.unit.test_arista_parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for Arista EOS structural parser.
"""

from src.parsers.arista import parse_arista


def test_parse_arista_basic() -> None:
    config = (
        "! Arista EOS config\n"
        "hostname SECURE-EOS-01\n"
        "ip ssh version 2\n"
        "interface Ethernet1\n"
        "   description Uplink to Core\n"
        "   ip address 10.0.0.1/24\n"
    )
    norm = parse_arista(config)
    assert norm.vendor == "arista"
    assert norm.hostname == "SECURE-EOS-01"
    assert len(norm.global_items) >= 2
    assert len(norm.sections) == 1
    assert norm.sections[0].name == "interface Ethernet1"
    assert len(norm.sections[0].items) == 2
    # Verify line numbers preserved
    assert norm.global_items[0].line_number is not None
