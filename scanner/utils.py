"""
Utility functions for the scanner.
"""

import logging
from pathlib import Path
from typing import List, Set

# Common directory names that often contain vendored third-party code
VENDOR_DIR_NAMES = {
    "vendor",
    "vendored",
    "third_party",
    "thirdparty",
    "3rdparty",
    "externals",
    "external",
    "libs",
    "lib",
    "dependencies",
    "packages",
}

# Toolkit-specific vendored code patterns (from wiki)
TOOLKIT_VENDOR_PATTERNS = {
    # Specific known patterns from About Box process documentation
    "lib",  # e.g., shotgun_api3/lib
    "vendors",  # e.g., python/vendors, desktopclient/python/vendors
}

# Toolkit-specific paths that often contain third-party code
TOOLKIT_THIRD_PARTY_PATHS = [
    "shotgun_api3/lib",
    "python/vendors",
    "desktopclient/python/vendors",
    "desktopserver/resources/python",
    "tests/python/third_party",
    "adobe",  # May contain .zip files
]

# Common license file names
LICENSE_FILE_NAMES = {
    "license",
    "license.txt",
    "license.md",
    "licence",
    "licence.txt",
    "licence.md",
    "copying",
    "copying.txt",
    "notice",
    "notice.txt",
    "copyright",
    "copyright.txt",
}

# Directories to always skip
SKIP_DIRECTORIES = {
    ".git",
    ".svn",
    ".hg",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".eggs",
    "*.egg-info",
    "node_modules",
    ".venv",
    "venv",
    "env",
}


def setup_logging(verbose: bool = False):
    """Configure logging for the scanner."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def should_skip_directory(dir_path: Path) -> bool:
    """Check if a directory should be skipped during scanning."""
    dir_name = dir_path.name
    
    # Skip hidden directories
    if dir_name.startswith("."):
        return True
    
    # Skip known directories
    if dir_name in SKIP_DIRECTORIES:
        return True
    
    # Skip egg-info directories
    if dir_name.endswith(".egg-info"):
        return True
    
    return False


def is_license_file(file_path: Path) -> bool:
    """Check if a file appears to be a license file."""
    name_lower = file_path.name.lower()
    return name_lower in LICENSE_FILE_NAMES


def is_vendor_directory(dir_path: Path) -> bool:
    """Check if a directory name suggests it contains vendored code."""
    name_lower = dir_path.name.lower()
    return name_lower in VENDOR_DIR_NAMES


def is_toolkit_vendor_path(rel_path: str) -> bool:
    """
    Check if a relative path matches known Toolkit third-party patterns.
    
    Args:
        rel_path: Relative path from repo root (with forward slashes)
    
    Returns:
        True if path matches Toolkit vendor patterns
    """
    rel_path_lower = rel_path.lower()
    
    # Check exact matches
    for pattern in TOOLKIT_THIRD_PARTY_PATHS:
        if pattern.lower() in rel_path_lower:
            return True
    
    return False


def find_files_by_extension(
    root_path: Path,
    extensions: Set[str],
    max_depth: int = None
) -> List[Path]:
    """
    Find all files with given extensions in a directory tree.
    
    Args:
        root_path: Root directory to search
        extensions: Set of file extensions to match (e.g., {'.py', '.txt'})
        max_depth: Maximum depth to search (None for unlimited)
    
    Returns:
        List of Path objects matching the extensions
    """
    results = []
    
    def scan_directory(path: Path, current_depth: int = 0):
        if max_depth is not None and current_depth > max_depth:
            return
        
        try:
            for item in path.iterdir():
                if item.is_dir():
                    if not should_skip_directory(item):
                        scan_directory(item, current_depth + 1)
                elif item.is_file():
                    if item.suffix.lower() in extensions:
                        results.append(item)
        except PermissionError:
            logging.warning(f"Permission denied: {path}")
        except Exception as e:
            logging.warning(f"Error scanning {path}: {e}")
    
    scan_directory(root_path)
    return results


def relative_path(file_path: Path, repo_root: Path) -> str:
    """
    Get the relative path of a file from the repository root.
    
    Returns the path as a string with forward slashes.
    """
    try:
        rel_path = file_path.relative_to(repo_root)
        return str(rel_path).replace("\\", "/")
    except ValueError:
        # If file_path is not relative to repo_root, return absolute path
        return str(file_path)
