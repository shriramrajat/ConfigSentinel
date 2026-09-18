"""
tests.unit.test_panos_parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for Palo Alto PAN-OS structural parser.
"""

from src.parsers.panos import parse_panos


def test_parse_panos_set_format() -> None:
    config = (
        "set deviceconfig system hostname PAN-FW-01\n"
        "set deviceconfig system service disable-telnet yes\n"
        "set security policy rule1 from any to any action allow\n"
    )
    norm = parse_panos(config)
    assert norm.vendor == "panos"
    assert norm.hostname == "PAN-FW-01"
    assert len(norm.global_items) == 2
    assert len(norm.sections) == 1
    assert norm.sections[0].name == "security-policy"


def test_parse_panos_xml_format() -> None:
    config = (
        "<config version=\"10.0\">\n"
        "  <deviceconfig>\n"
        "    <system>\n"
        "      <hostname>SECURE-PAN-01</hostname>\n"
        "    </system>\n"
        "  </deviceconfig>\n"
        "</config>\n"
    )
    norm = parse_panos(config)
    assert norm.vendor == "panos"
    assert norm.hostname == "SECURE-PAN-01"
