"""
Binary and software component detector.

Detects and extracts version information from binaries like:
- Python interpreter
- Qt/PySide libraries
- OpenSSL
- Other system libraries
"""

import logging
import re
import subprocess
from pathlib import Path
from typing import List, Optional

from .models import BinaryComponent

logger = logging.getLogger(__name__)


def detect_python_version(python_exe: Path) -> Optional[str]:
    """
    Detect Python version by running python --version.
    
    Args:
        python_exe: Path to Python executable
    
    Returns:
        Version string or None
    """
    try:
        result = subprocess.run(
            [str(python_exe), "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # Output format: "Python 3.10.11"
        match = re.search(r"Python\s+([\d\.]+)", result.stdout + result.stderr)
        if match:
            version = match.group(1)
            logger.info(f"Detected Python version: {version}")
            return version
    except Exception as e:
        logger.warning(f"Could not detect Python version: {e}")
    
    return None


def detect_qt_version(installation_path: Path) -> Optional[str]:
    """
    Detect Qt version from installation.
    
    Common locations:
    - Windows: QtCore5.dll, QtCore6.dll
    - macOS: QtCore.framework
    - Linux: libQt5Core.so, libQt6Core.so
    
    Args:
        installation_path: Path to installation root
    
    Returns:
        Version string or None
    """
    try:
        # Look for Qt DLLs/SOs/Frameworks
        patterns = [
            "**/QtCore*.dll",
            "**/QtCore*.so*",
            "**/QtCore.framework",
            "**/Qt5Core*.dll",
            "**/Qt6Core*.dll",
        ]
        
        for pattern in patterns:
            qt_files = list(installation_path.glob(pattern))
            if qt_files:
                qt_file = qt_files[0]
                # Try to extract version from filename
                match = re.search(r"Qt([56])Core", qt_file.name)
                if match:
                    major_version = match.group(1)
                    logger.info(f"Detected Qt {major_version}.x")
                    return f"{major_version}.x"
    
    except Exception as e:
        logger.warning(f"Could not detect Qt version: {e}")
    
    return None


def detect_openssl_version(installation_path: Path) -> Optional[str]:
    """
    Detect OpenSSL version.
    
    Args:
        installation_path: Path to installation root
    
    Returns:
        Version string or None
    """
    try:
        # Look for OpenSSL DLLs/SOs
        patterns = [
            "**/libssl*.dll",
            "**/libssl*.so*",
            "**/libcrypto*.dll",
            "**/libcrypto*.so*",
        ]
        
        for pattern in patterns:
            ssl_files = list(installation_path.glob(pattern))
            if ssl_files:
                ssl_file = ssl_files[0]
                # Try to extract version from filename
                # Example: libssl-1_1.dll, libssl.so.1.1
                match = re.search(r"[\-\.](\d+)[_\.](\d+)", ssl_file.name)
                if match:
                    version = f"{match.group(1)}.{match.group(2)}"
                    logger.info(f"Detected OpenSSL {version}")
                    return version
    
    except Exception as e:
        logger.warning(f"Could not detect OpenSSL version: {e}")
    
    return None


def scan_binaries(installation_path: Path) -> List[BinaryComponent]:
    """
    Scan installation for binary components.
    
    Args:
        installation_path: Path to installation root
    
    Returns:
        List of BinaryComponent objects
    """
    binaries = []
    
    logger.info("Scanning for binary components...")
    
    # Detect Python
    python_patterns = [
        "**/python.exe",
        "**/python",
        "**/Python.framework/Versions/*/bin/python*",
    ]
    
    for pattern in python_patterns:
        python_exes = list(installation_path.glob(pattern))
        for python_exe in python_exes:
            if python_exe.is_file():
                version = detect_python_version(python_exe)
                binaries.append(BinaryComponent(
                    name="Python",
                    path=str(python_exe.relative_to(installation_path)),
                    version=version,
                    type="interpreter"
                ))
                break  # Only add one Python
        if binaries:  # Found Python
            break
    
    # Detect Qt
    qt_version = detect_qt_version(installation_path)
    if qt_version:
        binaries.append(BinaryComponent(
            name="Qt",
            path="",
            version=qt_version,
            type="library"
        ))
    
    # Detect OpenSSL
    ssl_version = detect_openssl_version(installation_path)
    if ssl_version:
        binaries.append(BinaryComponent(
            name="OpenSSL",
            path="",
            version=ssl_version,
            type="library"
        ))
    
    logger.info(f"Found {len(binaries)} binary components")
    return binaries
