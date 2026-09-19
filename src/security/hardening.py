"""
security.hardening
~~~~~~~~~~~~~~~~~~

Production Security Hardening Utilities.

Protections:
- Path Traversal / Zip Slip extraction boundaries
- Configuration upload size enforcement
- Maximum archive file count limits
- Malformed input sanitization
"""

from __future__ import annotations

import os
from pathlib import Path
import zipfile


MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit per file
MAX_ARCHIVE_FILE_COUNT = 100            # Max 100 files per upload archive


class SecurityHardeningError(ValueError):
    """Raised when an operation violates production security bounds."""


def validate_file_size(content: bytes | str) -> None:
    """Enforce strict upper bound on configuration file size."""
    size = len(content.encode("utf-8")) if isinstance(content, str) else len(content)
    if size > MAX_FILE_SIZE_BYTES:
        raise SecurityHardeningError(
            f"File size ({size} bytes) exceeds maximum allowable limit of {MAX_FILE_SIZE_BYTES} bytes."
        )


def safe_extract_zip(zip_path: str, extract_dir: str) -> list[str]:
    """Safely extract zip archive preventing Zip Slip path traversal vulnerabilities."""
    target_dir = Path(extract_dir).resolve()
    extracted_files: list[str] = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.infolist()
        if len(members) > MAX_ARCHIVE_FILE_COUNT:
            raise SecurityHardeningError(
                f"Archive contains {len(members)} files, exceeding limit of {MAX_ARCHIVE_FILE_COUNT}."
            )

        for member in members:
            # Resolve destination path
            member_path = (target_dir / member.filename).resolve()

            # Prevent Zip Slip / Path Traversal: ensure member_path is inside target_dir
            if not str(member_path).startswith(str(target_dir)):
                raise SecurityHardeningError(
                    f"Path traversal attempt detected in archive entry: '{member.filename}'"
                )

            if member.is_dir():
                os.makedirs(member_path, exist_ok=True)
            else:
                os.makedirs(member_path.parent, exist_ok=True)
                with zf.open(member) as source, open(member_path, "wb") as target:
                    content = source.read()
                    validate_file_size(content)
                    target.write(content)
                extracted_files.append(str(member_path))

    return extracted_files
