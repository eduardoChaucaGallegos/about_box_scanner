"""
License information extractor.

Reads LICENSE files, detects license types, and extracts copyright statements.
"""

import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple

from .models import LicenseInfo

logger = logging.getLogger(__name__)

# Common license patterns for detection
# Based on SPDX identifiers and common license text patterns
LICENSE_PATTERNS = {
    "MIT": [
        r"MIT License",
        r"Permission is hereby granted, free of charge",
        r"THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND",
    ],
    "Apache-2.0": [
        r"Apache License[,\s]+Version 2\.0",
        r"www\.apache\.org/licenses/LICENSE-2\.0",
    ],
    "BSD-3-Clause": [
        r"BSD 3-Clause",
        r"Redistribution and use in source and binary forms.*with or without modification",
        r"THIS SOFTWARE IS PROVIDED.*\"AS IS\".*AND ANY EXPRESS OR IMPLIED WARRANTIES",
    ],
    "BSD-2-Clause": [
        r"BSD 2-Clause",
        r"Redistributions of source code must retain",
        r"Redistributions in binary form must reproduce",
    ],
    "GPL-2.0": [
        r"GNU GENERAL PUBLIC LICENSE[,\s]+Version 2",
        r"www\.gnu\.org/licenses/gpl-2\.0",
    ],
    "GPL-3.0": [
        r"GNU GENERAL PUBLIC LICENSE[,\s]+Version 3",
        r"www\.gnu\.org/licenses/gpl-3\.0",
    ],
    "LGPL-2.1": [
        r"GNU LESSER GENERAL PUBLIC LICENSE[,\s]+Version 2\.1",
        r"www\.gnu\.org/licenses/lgpl-2\.1",
    ],
    "LGPL-3.0": [
        r"GNU LESSER GENERAL PUBLIC LICENSE[,\s]+Version 3",
        r"www\.gnu\.org/licenses/lgpl-3\.0",
    ],
    "ISC": [
        r"ISC License",
        r"Permission to use, copy, modify, and/or distribute this software",
    ],
    "MPL-2.0": [
        r"Mozilla Public License Version 2\.0",
        r"mozilla\.org/MPL/2\.0",
    ],
    "PSF": [
        r"Python Software Foundation License",
        r"PSF LICENSE AGREEMENT FOR PYTHON",
    ],
}

# Copyright patterns
COPYRIGHT_PATTERNS = [
    r"Copyright\s+(?:\(c\)\s*)?(\d{4}(?:\s*-\s*\d{4})?)\s+(.+?)(?:\n|$)",
    r"Copyright\s+(?:\(c\)\s*)?(.+?)\s+(\d{4}(?:\s*-\s*\d{4})?)",
    r"©\s*(\d{4}(?:\s*-\s*\d{4})?)\s+(.+?)(?:\n|$)",
    r"Copyrights?\s*:?\s*(.+?)(?:\n|$)",
]


def read_license_file(file_path: Path) -> Optional[str]:
    """
    Read a license file and return its contents.
    
    Args:
        file_path: Path to license file
    
    Returns:
        License file contents or None if unable to read
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        logger.warning(f"Could not read license file {file_path}: {e}")
        return None


def detect_license_type(license_text: str) -> Optional[str]:
    """
    Detect license type from license text.
    
    Uses pattern matching against common license texts.
    
    Args:
        license_text: Full text of the license
    
    Returns:
        License type (SPDX identifier) or None if not detected
    """
    if not license_text:
        return None
    
    # Normalize whitespace for matching
    normalized_text = " ".join(license_text.split())
    
    # Try to match against known patterns
    for license_type, patterns in LICENSE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, normalized_text, re.IGNORECASE):
                logger.debug(f"Detected license type: {license_type}")
                return license_type
    
    # Check for SPDX identifier
    spdx_match = re.search(r"SPDX-License-Identifier:\s*([A-Za-z0-9\-\.]+)", license_text)
    if spdx_match:
        spdx_id = spdx_match.group(1)
        logger.debug(f"Found SPDX identifier: {spdx_id}")
        return spdx_id
    
    logger.debug("Could not detect license type from text")
    return None


def extract_copyright_statements(license_text: str) -> List[str]:
    """
    Extract copyright statements from license text.
    
    Args:
        license_text: Full text of the license
    
    Returns:
        List of copyright statements found
    """
    if not license_text:
        return []
    
    statements = []
    seen = set()
    
    for pattern in COPYRIGHT_PATTERNS:
        matches = re.finditer(pattern, license_text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            # Get the full matched text
            statement = match.group(0).strip()
            
            # Normalize and deduplicate
            normalized = " ".join(statement.split())
            if normalized and normalized not in seen:
                statements.append(statement)
                seen.add(normalized)
    
    logger.debug(f"Extracted {len(statements)} copyright statement(s)")
    return statements


def extract_license_info(
    license_file_path: Path,
    repo_root: Path,
    max_text_length: int = 10000
) -> Optional[LicenseInfo]:
    """
    Extract complete license information from a license file.
    
    Args:
        license_file_path: Path to the license file
        repo_root: Repository root path (for relative path calculation)
        max_text_length: Maximum length of license text to store (default: 10000 chars)
    
    Returns:
        LicenseInfo object or None if unable to extract
    """
    license_text = read_license_file(license_file_path)
    if not license_text:
        return None
    
    # Detect license type
    license_type = detect_license_type(license_text)
    
    # Extract copyright statements
    copyright_statements = extract_copyright_statements(license_text)
    
    # Truncate license text if too long
    if len(license_text) > max_text_length:
        license_text = license_text[:max_text_length] + "\n... (truncated)"
    
    # Calculate relative path
    try:
        rel_path = str(license_file_path.relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        rel_path = str(license_file_path)
    
    return LicenseInfo(
        license_type=license_type,
        license_file_path=rel_path,
        license_text=license_text,
        copyright_statements=copyright_statements,
        spdx_id=license_type if license_type and "-" in license_type else None
    )


def find_and_extract_licenses(
    directory: Path,
    repo_root: Path,
    recursive: bool = False
) -> List[LicenseInfo]:
    """
    Find and extract license information from a directory.
    
    Args:
        directory: Directory to search
        repo_root: Repository root path
        recursive: Whether to search recursively
    
    Returns:
        List of LicenseInfo objects found
    """
    license_infos = []
    
    # Common license file names
    license_file_names = {
        "license", "license.txt", "license.md",
        "licence", "licence.txt", "licence.md",
        "copying", "copying.txt",
        "notice", "notice.txt",
        "copyright", "copyright.txt",
    }
    
    try:
        iterator = directory.rglob("*") if recursive else directory.iterdir()
        
        for item in iterator:
            if item.is_file():
                name_lower = item.name.lower()
                if name_lower in license_file_names:
                    logger.debug(f"Found license file: {item.relative_to(repo_root)}")
                    license_info = extract_license_info(item, repo_root)
                    if license_info:
                        license_infos.append(license_info)
    
    except Exception as e:
        logger.warning(f"Error searching for licenses in {directory}: {e}")
    
    return license_infos
