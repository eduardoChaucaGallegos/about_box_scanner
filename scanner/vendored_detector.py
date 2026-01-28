"""
Detector for vendored third-party code.

Uses heuristics to identify directories and files that appear to be
vendored third-party components.
"""

import logging
from pathlib import Path
from typing import List

from .models import VendoredCandidate
from .utils import (
    is_vendor_directory,
    is_license_file,
    should_skip_directory,
    relative_path,
    is_toolkit_vendor_path,
)

logger = logging.getLogger(__name__)


def scan_vendored_code(repo_path: Path, toolkit_mode: bool = True) -> List[VendoredCandidate]:
    """
    Scan repository for vendored third-party code.
    
    Uses multiple heuristics:
    1. Directories with names like "vendor", "third_party", etc.
    2. Directories containing LICENSE files with different names
    3. Toolkit-specific patterns (if toolkit_mode=True)
    4. Root-level .zip files (Toolkit pattern)
    
    Args:
        repo_path: Path to repository root
        toolkit_mode: If True, apply Toolkit-specific detection patterns
    """
    candidates = []
    
    # Heuristic 1: Look for vendor-like directory names
    candidates.extend(_find_vendor_directories(repo_path, toolkit_mode))
    
    # Heuristic 2: Look for directories with LICENSE files that might indicate vendored code
    candidates.extend(_find_directories_with_licenses(repo_path))
    
    # Heuristic 3 (Toolkit): Look for root-level .zip files
    if toolkit_mode:
        candidates.extend(_find_root_zip_files(repo_path))
    
    logger.info(f"Found {len(candidates)} vendored code candidates")
    return candidates


def _find_vendor_directories(repo_path: Path, toolkit_mode: bool = True) -> List[VendoredCandidate]:
    """Find directories with names suggesting vendored code."""
    candidates = []
    seen_paths = set()
    
    def scan_directory(path: Path, depth: int = 0):
        # Don't scan too deep
        if depth > 5:
            return
        
        try:
            for item in path.iterdir():
                if not item.is_dir():
                    continue
                
                if should_skip_directory(item):
                    continue
                
                rel_path = relative_path(item, repo_path)
                
                # Skip if already seen
                if rel_path in seen_paths:
                    continue
                
                # Check Toolkit-specific patterns first
                is_toolkit_match = False
                if toolkit_mode and is_toolkit_vendor_path(rel_path):
                    license_files = _find_license_files_in_directory(item)
                    candidates.append(VendoredCandidate(
                        path=rel_path,
                        reason="toolkit_vendor_pattern",
                        license_files=[relative_path(lf, repo_path) for lf in license_files],
                        is_toolkit_pattern=True
                    ))
                    seen_paths.add(rel_path)
                    is_toolkit_match = True
                    # Don't recurse into toolkit vendor directories
                    continue
                
                # Check if directory name suggests vendored code
                if is_vendor_directory(item):
                    license_files = _find_license_files_in_directory(item)
                    candidates.append(VendoredCandidate(
                        path=rel_path,
                        reason="directory_name_match",
                        license_files=[relative_path(lf, repo_path) for lf in license_files],
                        is_toolkit_pattern=False
                    ))
                    seen_paths.add(rel_path)
                    # Don't recurse into vendor directories
                    continue
                
                # Recurse into other directories
                scan_directory(item, depth + 1)
        
        except PermissionError:
            logger.warning(f"Permission denied: {path}")
        except Exception as e:
            logger.warning(f"Error scanning {path}: {e}")
    
    scan_directory(repo_path)
    return candidates


def _find_directories_with_licenses(repo_path: Path) -> List[VendoredCandidate]:
    """
    Find directories containing LICENSE files that might indicate vendored code.
    
    Ignores the root LICENSE file (that's the repo's own license).
    """
    candidates = []
    seen_paths = set()
    
    try:
        for license_file in repo_path.rglob("LICENSE*"):
            if not license_file.is_file():
                continue
            
            # Skip the root license
            if license_file.parent == repo_path:
                continue
            
            # Skip files in already identified vendor directories
            if any(part in license_file.parts for part in ["vendor", "third_party", "externals"]):
                continue
            
            # Skip test directories
            if any(part in license_file.parts for part in ["test", "tests", "testing"]):
                continue
            
            parent_dir = license_file.parent
            parent_path = relative_path(parent_dir, repo_path)
            
            # Avoid duplicates
            if parent_path in seen_paths:
                continue
            
            seen_paths.add(parent_path)
            
            # Check if this looks like a component directory
            # (has __init__.py or setup.py or looks like a package)
            if _looks_like_third_party_component(parent_dir):
                license_files = _find_license_files_in_directory(parent_dir)
                candidates.append(VendoredCandidate(
                    path=parent_path,
                    reason="license_file_found",
                    license_files=[relative_path(lf, repo_path) for lf in license_files]
                ))
    
    except Exception as e:
        logger.error(f"Error finding license files: {e}")
    
    return candidates


def _find_license_files_in_directory(directory: Path) -> List[Path]:
    """Find all license-related files in a directory (non-recursive)."""
    license_files = []
    
    try:
        for item in directory.iterdir():
            if item.is_file() and is_license_file(item):
                license_files.append(item)
    except Exception as e:
        logger.warning(f"Error scanning {directory}: {e}")
    
    return license_files


def _looks_like_third_party_component(directory: Path) -> bool:
    """
    Check if a directory looks like a third-party component.
    
    Heuristics:
    - Has its own LICENSE file
    - Has setup.py or pyproject.toml
    - Has __init__.py (Python package)
    - Has multiple source files
    """
    # Check for common package files
    has_init = (directory / "__init__.py").exists()
    has_setup = (directory / "setup.py").exists()
    has_pyproject = (directory / "pyproject.toml").exists()
    has_license = any(is_license_file(f) for f in directory.iterdir() if f.is_file())
    
    # Count source files
    try:
        source_files = list(directory.glob("*.py"))
        has_multiple_sources = len(source_files) > 1
    except Exception:
        has_multiple_sources = False
    
    # If it has a license and looks like a package, it's probably third-party
    if has_license and (has_init or has_setup or has_pyproject or has_multiple_sources):
        return True
    
    return False


def _find_root_zip_files(repo_path: Path) -> List[VendoredCandidate]:
    """
    Find .zip files at the root level (Toolkit pattern).
    
    Per the wiki: Some Toolkit repos have third-party components
    packaged as .zip files in the root or specific directories like adobe/.
    """
    candidates = []
    
    try:
        # Check root level
        for item in repo_path.iterdir():
            if item.is_file() and item.suffix.lower() == ".zip":
                candidates.append(VendoredCandidate(
                    path=relative_path(item, repo_path),
                    reason="root_zip_file",
                    license_files=[],
                    is_toolkit_pattern=True
                ))
        
        # Check adobe/ directory if it exists
        adobe_dir = repo_path / "adobe"
        if adobe_dir.exists() and adobe_dir.is_dir():
            for item in adobe_dir.iterdir():
                if item.is_file() and item.suffix.lower() == ".zip":
                    candidates.append(VendoredCandidate(
                        path=relative_path(item, repo_path),
                        reason="adobe_zip_file",
                        license_files=[],
                        is_toolkit_pattern=True
                    ))
    
    except Exception as e:
        logger.warning(f"Error finding zip files: {e}")
    
    return candidates
