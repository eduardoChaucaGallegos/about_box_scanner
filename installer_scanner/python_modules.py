"""
Python modules detector.

Detects Python packages installed in the SGD installation.
"""

import logging
import subprocess
import re
from pathlib import Path
from typing import List

from .models import PythonModule

logger = logging.getLogger(__name__)


def get_python_modules_via_pip(python_exe: Path) -> List[PythonModule]:
    """
    Get Python modules using pip list.
    
    Args:
        python_exe: Path to Python executable
    
    Returns:
        List of PythonModule objects
    """
    modules = []
    
    try:
        # Run pip list --format=json
        result = subprocess.run(
            [str(python_exe), "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            import json
            packages = json.loads(result.stdout)
            
            for pkg in packages:
                modules.append(PythonModule(
                    name=pkg.get("name", ""),
                    version=pkg.get("version", ""),
                    location=None
                ))
            
            logger.info(f"Found {len(modules)} Python modules via pip")
        else:
            logger.warning(f"pip list failed: {result.stderr}")
    
    except Exception as e:
        logger.warning(f"Could not run pip list: {e}")
    
    return modules


def get_python_modules_via_site_packages(installation_path: Path) -> List[PythonModule]:
    """
    Get Python modules by scanning site-packages directory.
    
    Fallback method when pip is not available.
    
    Args:
        installation_path: Path to installation root
    
    Returns:
        List of PythonModule objects
    """
    modules = []
    
    try:
        # Common site-packages locations
        patterns = [
            "**/site-packages",
            "**/dist-packages",
            "**/lib/python*/site-packages",
        ]
        
        site_packages_dirs = []
        for pattern in patterns:
            site_packages_dirs.extend(installation_path.glob(pattern))
        
        if not site_packages_dirs:
            logger.warning("No site-packages directory found")
            return modules
        
        # Use the first one found
        site_packages = site_packages_dirs[0]
        logger.info(f"Scanning site-packages: {site_packages}")
        
        # Look for .dist-info directories (modern packages)
        dist_info_dirs = list(site_packages.glob("*.dist-info"))
        
        for dist_info in dist_info_dirs:
            # Extract package name and version from directory name
            # Format: package_name-version.dist-info
            match = re.match(r"(.+?)-(.+?)\.dist-info", dist_info.name)
            if match:
                name = match.group(1).replace("_", "-")
                version = match.group(2)
                
                modules.append(PythonModule(
                    name=name,
                    version=version,
                    location=str(dist_info.relative_to(installation_path))
                ))
        
        # Look for .egg-info files (older packages)
        egg_info_files = list(site_packages.glob("*.egg-info"))
        
        for egg_info in egg_info_files:
            match = re.match(r"(.+?)-(.+?)\.egg-info", egg_info.name)
            if match:
                name = match.group(1).replace("_", "-")
                version = match.group(2)
                
                # Skip if already added via dist-info
                if not any(m.name == name for m in modules):
                    modules.append(PythonModule(
                        name=name,
                        version=version,
                        location=str(egg_info.relative_to(installation_path))
                    ))
        
        logger.info(f"Found {len(modules)} Python modules in site-packages")
    
    except Exception as e:
        logger.error(f"Error scanning site-packages: {e}")
    
    return modules


def scan_python_modules(installation_path: Path, python_exe: Path = None) -> List[PythonModule]:
    """
    Scan for Python modules in the installation.
    
    Args:
        installation_path: Path to installation root
        python_exe: Optional path to Python executable (will auto-detect if not provided)
    
    Returns:
        List of PythonModule objects
    """
    logger.info("Scanning for Python modules...")
    
    # Auto-detect Python executable if not provided
    if not python_exe:
        python_patterns = [
            "**/python.exe",
            "**/python",
            "**/Python.framework/Versions/*/bin/python3",
        ]
        
        for pattern in python_patterns:
            python_exes = list(installation_path.glob(pattern))
            if python_exes:
                python_exe = python_exes[0]
                logger.info(f"Using Python: {python_exe}")
                break
    
    # Try pip first
    if python_exe and python_exe.exists():
        modules = get_python_modules_via_pip(python_exe)
        if modules:
            return modules
    
    # Fallback to site-packages scan
    logger.info("Falling back to site-packages scan...")
    return get_python_modules_via_site_packages(installation_path)
