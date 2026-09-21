"""
mapping.redaction
~~~~~~~~~~~~~~~~~

Pre-LLM secret and credential redaction layer for ConfigSentinel.

Design Intent
-------------
Before any raw directive or section context is sent to an external LLM
provider for unknown pattern analysis, sensitive credential material
(passwords, hashes, community strings, API keys, private keys, shared secrets)
MUST be redacted.

Redaction MUST:
1. Replace secret material with a placeholder (e.g. ``[REDACTED_SECRET]``).
2. Preserve surrounding syntax so semantic analysis remains possible.
3. Be deterministic and fully testable.
"""

from __future__ import annotations

import re

# Compiled regex patterns for credential detection across network vendors and standard formats
_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Private keys
    (
        re.compile(r"-----BEGIN (?:RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----[\s\S]*?-----END (?:RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----", re.IGNORECASE),
        "[REDACTED_PRIVATE_KEY]",
    ),
    # Cisco / Arista / EOS enable secret / password hashes (type 5, 8, 9, 7)
    (
        re.compile(r"(\benable\s+(?:secret|password)\s+(?:\d+\s+)?)[^\s\"'\\]+", re.IGNORECASE),
        r"\1[REDACTED_SECRET]",
    ),
    # User credential definitions: "username admin password SuperSecret123", "user foo secret bar"
    (
        re.compile(r"(\b(?:username|user)\s+[^\s]+\s+(?:privilege\s+\d+\s+)?(?:secret|password)\s+(?:\d+\s+)?)[^\s\"'\\]+", re.IGNORECASE),
        r"\1[REDACTED_SECRET]",
    ),
    # Generic password / secret lines: "password 7 0822455D0A16", "auth-pass secret"
    (
        re.compile(r"(\b(?:password|secret|preshared-key|pre-shared-key|auth-pass|key|md5-key)\s+(?:\d+\s+)?)[^\s\"'\\]+", re.IGNORECASE),
        r"\1[REDACTED_SECRET]",
    ),
    # SNMP Community strings: "snmp-server community public RW", "community secret-key"
    (
        re.compile(r"(\bsnmp-server\s+community\s+)[^\s\"'\\]+", re.IGNORECASE),
        r"\1[REDACTED_COMMUNITY]",
    ),
    (
        re.compile(r"(\bcommunity\s+)[^\s]+(\s+(?:RO|RW|read-only|read-write))?", re.IGNORECASE),
        r"\1[REDACTED_COMMUNITY]\2",
    ),
    # UNIX / Crypt password hashes (e.g. $1$..., $5$..., $6$...)
    (
        re.compile(r"\$(?:1|5|6|8|9)\$[a-zA-Z0-9./]+\$[a-zA-Z0-9./]+"),
        "[REDACTED_HASH]",
    ),
    # Authorization headers & Bearer tokens
    (
        re.compile(r"(Authorization:\s*(?:Bearer|Basic)?\s*)[a-zA-Z0-9_\-\.]{6,}", re.IGNORECASE),
        r"\1[REDACTED_TOKEN]",
    ),
    (
        re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{6,}", re.IGNORECASE),
        r"\1[REDACTED_TOKEN]",
    ),
    # Key-value pairs in JSON/YAML or API payloads: "secret_key": "cisco123", "password": "...", "token": "..."
    (
        re.compile(r"([\"']?(?:api[_-]?key|secret[_-]?key|token|auth[_-]?token|access[_-]?key|credential|password|secret)[\"']?\s*[:=]\s*[\"'])[^\s\"']+([\"'])", re.IGNORECASE),
        r"\1[REDACTED_SECRET]\2",
    ),
    (
        re.compile(r"(\b(?:api[_-]?key|secret[_-]?key|token|auth[_-]?token|access[_-]?key|credential)\s*[:=]\s*)[^\s\"',}]+", re.IGNORECASE),
        r"\1[REDACTED_SECRET]",
    ),
]


def redact_secrets(text: str | None) -> str:
    """Redact passwords, hashes, keys, and tokens from *text*.

    Returns the sanitized text with sensitive credentials replaced by
    structural placeholders. If *text* is empty or None, returns empty string.
    """
    if not text:
        return ""

    sanitized = text
    for pattern, replacement in _SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    return sanitized
