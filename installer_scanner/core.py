"""
Core installation scanner orchestration.
"""

import logging
from pathlib import Path
import platform as platform_module

from .models import InstallationInventory
from .binary_detector import scan_binaries
from .python_modules import scan_python_modules
from .toolkit_detector import scan_toolkit_components

logger = logging.getLogger(__name__)


def detect_platform() -> str:
    """
    Detect current platform.
    
    Returns:
        "windows", "macos", or "linux"
    """
    system = platform_module.system().lower()
    
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    else:
        return system


def scan_fonts(installation_path: Path) -> list:
    """
    Scan for font files in the installation.
    
    Args:
        installation_path: Path to installation root
    
    Returns:
        List of font file paths (relative)
    """
    fonts = []
    
    try:
        # Look for common font extensions
        font_extensions = {".ttf", ".otf", ".woff", ".woff2"}
        
        for font_file in installation_path.rglob("*"):
            if font_file.is_file() and font_file.suffix.lower() in font_extensions:
                fonts.append(str(font_file.relative_to(installation_path)).replace("\\", "/"))
        
        logger.info(f"Found {len(fonts)} font files")
    
    except Exception as e:
        logger.error(f"Error scanning for fonts: {e}")
    
    return fonts


def scan_installation(
    installation_path: Path,
    platform: str = None
) -> InstallationInventory:
    """
    Scan a ShotGrid Desktop installation.
    
    Args:
        installation_path: Path to installation root
        platform: Platform name ("windows", "macos", "linux"), auto-detected if not provided
    
    Returns:
        InstallationInventory object
    """
    if not platform:
        platform = detect_platform()
    
    logger.info(f"Starting scan of installation: {installation_path}")
    logger.info(f"Platform: {platform}")
    
    # Validate path
    if not installation_path.exists():
        raise ValueError(f"Installation path does not exist: {installation_path}")
    
    if not installation_path.is_dir():
        raise ValueError(f"Installation path is not a directory: {installation_path}")
    
    # Create inventory
    inventory = InstallationInventory.create(
        str(installation_path.absolute()),
        platform
    )
    
    # Scan binaries
    logger.info("=" * 60)
    logger.info("Scanning for binary components...")
    logger.info("=" * 60)
    inventory.binaries = scan_binaries(installation_path)
    
    # Scan Python modules
    logger.info("=" * 60)
    logger.info("Scanning for Python modules...")
    logger.info("=" * 60)
    inventory.python_modules = scan_python_modules(installation_path)
    
    # Scan Toolkit components
    logger.info("=" * 60)
    logger.info("Scanning for Toolkit components...")
    logger.info("=" * 60)
    inventory.toolkit_components = scan_toolkit_components(installation_path)
    
    # Scan fonts
    logger.info("=" * 60)
    logger.info("Scanning for fonts...")
    logger.info("=" * 60)
    inventory.fonts = scan_fonts(installation_path)
    
    # Summary
    logger.info("=" * 60)
    logger.info("Scan complete!")
    logger.info(f"  Binaries: {len(inventory.binaries)}")
    logger.info(f"  Python modules: {len(inventory.python_modules)}")
    logger.info(f"  Toolkit components: {len(inventory.toolkit_components)}")
    logger.info(f"  Fonts: {len(inventory.fonts)}")
    logger.info("=" * 60)
    
    return inventory
