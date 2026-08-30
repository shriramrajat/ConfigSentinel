"""src.api — FastAPI transport layer for ConfigSentinel.

This package exposes the existing compliance pipeline over HTTP.
It contains ONLY transport concerns: routing, serialisation, error handling.

All compliance logic lives in src.compliance.
All parser logic lives in src.parsers.
This package MUST NOT duplicate either.
"""
