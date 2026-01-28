"""
Toolkit components detector.

Detects tk-* components in the SGD installation.
"""

import logging
import re
from pathlib import Path
from typing import List

from .models import ToolkitComponent

logger = logging.getLogger(__name__)


def read_version_from_info_yml(component_path: Path) -> str:
    """
    Read version from info.yml file.
    
    Args:
        component_path: Path to component directory
    
    Returns:
        Version string or "unknown"
    """
    info_yml = component_path / "info.yml"
    
    if not info_yml.exists():
        return "unknown"
    
    try:
        with open(info_yml, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Look for version: line
        match = re.search(r"version:\s*['\"]?([^'\"]+)['\"]?", content)
        if match:
            return match.group(1).strip()
    
    except Exception as e:
        logger.debug(f"Could not read version from {info_yml}: {e}")
    
    return "unknown"


def read_version_from_version_file(component_path: Path) -> str:
    """
    Read version from VERSION file.
    
    Args:
        component_path: Path to component directory
    
    Returns:
        Version string or "unknown"
    """
    version_file = component_path / "VERSION"
    
    if not version_file.exists():
        return "unknown"
    
    try:
        with open(version_file, "r", encoding="utf-8") as f:
            version = f.read().strip()
            return version
    
    except Exception as e:
        logger.debug(f"Could not read version from {version_file}: {e}")
    
    return "unknown"


def has_software_credits(component_path: Path) -> bool:
    """
    Check if component has a software_credits file.
    
    Args:
        component_path: Path to component directory
    
    Returns:
        True if software_credits exists
    """
    return (component_path / "software_credits").exists()


def scan_toolkit_components(installation_path: Path) -> List[ToolkitComponent]:
    """
    Scan for Toolkit components (tk-*) in the installation.
    
    Common locations:
    - install/core/
    - install/engines/
    - install/apps/
    - install/frameworks/
    
    Args:
        installation_path: Path to installation root
    
    Returns:
        List of ToolkitComponent objects
    """
    components = []
    
    logger.info("Scanning for Toolkit components...")
    
    try:
        # Look for directories starting with "tk-"
        tk_dirs = []
        
        # Search recursively but not too deep (max 4 levels)
        for depth in range(4):
            pattern = "/".join(["*"] * depth) + "/tk-*"
            tk_dirs.extend([d for d in installation_path.glob(pattern) if d.is_dir()])
        
        # Deduplicate
        tk_dirs = list(set(tk_dirs))
        
        for tk_dir in tk_dirs:
            name = tk_dir.name
            
            # Try to read version
            version = read_version_from_info_yml(tk_dir)
            if version == "unknown":
                version = read_version_from_version_file(tk_dir)
            
            # Check for software_credits
            has_credits = has_software_credits(tk_dir)
            
            components.append(ToolkitComponent(
                name=name,
                path=str(tk_dir.relative_to(installation_path)),
                version=version,
                has_software_credits=has_credits
            ))
        
        logger.info(f"Found {len(components)} Toolkit components")
    
    except Exception as e:
        logger.error(f"Error scanning for Toolkit components: {e}")
    
    return components
