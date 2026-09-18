"""
tests.unit.test_fortios_parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for Fortinet FortiOS structural parser.
"""

from src.parsers.fortios import parse_fortios


def test_parse_fortios_basic() -> None:
    config = (
        "# FortiOS Config\n"
        "config system global\n"
        '    set hostname "FORTIGATE-FW-01"\n'
        "    set admin-sport 443\n"
        "end\n"
        "config system ntp\n"
        "    set status disable\n"
        "end\n"
    )
    norm = parse_fortios(config)
    assert norm.vendor == "fortinet"
    assert norm.hostname == "FORTIGATE-FW-01"
    assert len(norm.sections) == 2
    assert norm.sections[0].name == "config system global"
    assert len(norm.sections[0].items) == 2
    assert norm.sections[0].items[0].line_number == 3
