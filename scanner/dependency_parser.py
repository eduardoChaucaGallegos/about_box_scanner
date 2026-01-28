"""
Parser for Python dependency files.

Supports:
- requirements.txt
- pyproject.toml
- setup.py (basic detection)
"""

import logging
import re
import sys
from pathlib import Path
from typing import List

from .models import Dependency

logger = logging.getLogger(__name__)


def parse_requirements_txt(file_path: Path) -> List[Dependency]:
    """
    Parse a requirements.txt file.
    
    Handles:
    - Simple package names
    - Version specifiers (==, >=, <=, !=, ~=, etc.)
    - Comments and blank lines
    - -e git+https://... style entries (marks as vendored/git)
    """
    dependencies = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                raw_line = line.strip()
                
                # Skip empty lines and comments
                if not raw_line or raw_line.startswith("#"):
                    continue
                
                # Skip options like -r, -c, --index-url, etc.
                if raw_line.startswith("-"):
                    continue
                
                # Handle editable installs or git URLs
                if raw_line.startswith("-e") or "git+" in raw_line:
                    dependencies.append(Dependency(
                        source=f"requirements.txt:{line_num}",
                        name="<editable-or-git-dependency>",
                        version_spec="unknown",
                        raw_line=raw_line
                    ))
                    continue
                
                # Remove inline comments
                if "#" in raw_line:
                    raw_line = raw_line.split("#")[0].strip()
                
                # Parse package name and version spec
                # Pattern: package-name[extras]>=1.0,<2.0
                match = re.match(r"^([a-zA-Z0-9_\-\.]+)(\[[^\]]+\])?(.*)", raw_line)
                if match:
                    name = match.group(1)
                    version_spec = match.group(3).strip() if match.group(3) else "unknown"
                    
                    dependencies.append(Dependency(
                        source=f"requirements.txt:{line_num}",
                        name=name,
                        version_spec=version_spec if version_spec else "unknown",
                        raw_line=line.strip()
                    ))
                else:
                    logger.warning(f"Could not parse line {line_num} in {file_path}: {line.strip()}")
    
    except FileNotFoundError:
        logger.debug(f"File not found: {file_path}")
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
    
    return dependencies


def parse_pyproject_toml(file_path: Path) -> List[Dependency]:
    """
    Parse a pyproject.toml file.
    
    Looks for dependencies in:
    - [project.dependencies]
    - [project.optional-dependencies]
    - [tool.poetry.dependencies]
    """
    dependencies = []
    
    try:
        # Use tomli for Python < 3.11, tomllib for Python >= 3.11
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            try:
                import tomli as tomllib
            except ImportError:
                logger.warning(f"Cannot parse {file_path}: tomli not installed (pip install tomli)")
                return dependencies
        
        with open(file_path, "rb") as f:
            data = tomllib.load(f)
        
        # Parse [project.dependencies]
        project_deps = data.get("project", {}).get("dependencies", [])
        for dep in project_deps:
            name, version_spec = _parse_pep508_requirement(dep)
            dependencies.append(Dependency(
                source="pyproject.toml:project.dependencies",
                name=name,
                version_spec=version_spec,
                raw_line=dep
            ))
        
        # Parse [project.optional-dependencies]
        optional_deps = data.get("project", {}).get("optional-dependencies", {})
        for group_name, deps in optional_deps.items():
            for dep in deps:
                name, version_spec = _parse_pep508_requirement(dep)
                dependencies.append(Dependency(
                    source=f"pyproject.toml:project.optional-dependencies.{group_name}",
                    name=name,
                    version_spec=version_spec,
                    raw_line=dep
                ))
        
        # Parse [tool.poetry.dependencies] if present
        poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        for name, version_spec in poetry_deps.items():
            if name == "python":  # Skip Python version constraint
                continue
            
            # Poetry can have dict or string format
            if isinstance(version_spec, dict):
                version_str = version_spec.get("version", "unknown")
            else:
                version_str = str(version_spec)
            
            dependencies.append(Dependency(
                source="pyproject.toml:tool.poetry.dependencies",
                name=name,
                version_spec=version_str,
                raw_line=f"{name} = {version_spec}"
            ))
    
    except FileNotFoundError:
        logger.debug(f"File not found: {file_path}")
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
    
    return dependencies


def parse_setup_py(file_path: Path) -> List[Dependency]:
    """
    Parse a setup.py file (basic heuristic approach).
    
    This is a naive approach that looks for install_requires patterns.
    Does NOT execute the setup.py file for security reasons.
    """
    dependencies = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Look for install_requires=[...] pattern
        # This is a simple regex and won't catch all cases
        match = re.search(
            r"install_requires\s*=\s*\[(.*?)\]",
            content,
            re.DOTALL
        )
        
        if match:
            requires_content = match.group(1)
            # Extract quoted strings
            for line in requires_content.split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                # Match quoted strings
                quoted_match = re.search(r'["\']([^"\']+)["\']', line)
                if quoted_match:
                    req_string = quoted_match.group(1)
                    name, version_spec = _parse_pep508_requirement(req_string)
                    dependencies.append(Dependency(
                        source="setup.py:install_requires",
                        name=name,
                        version_spec=version_spec,
                        raw_line=req_string
                    ))
        else:
            logger.debug(f"No install_requires found in {file_path}")
    
    except FileNotFoundError:
        logger.debug(f"File not found: {file_path}")
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
    
    return dependencies


def _parse_pep508_requirement(requirement_string: str) -> tuple:
    """
    Parse a PEP 508 requirement string into (name, version_spec).
    
    Example: "requests>=2.0,<3.0" -> ("requests", ">=2.0,<3.0")
    """
    # Remove extras: package[extra1,extra2]
    requirement_string = re.sub(r"\[.*?\]", "", requirement_string)
    
    # Split on operators
    match = re.match(r"^([a-zA-Z0-9_\-\.]+)(.*)", requirement_string.strip())
    if match:
        name = match.group(1)
        version_spec = match.group(2).strip()
        return name, version_spec if version_spec else "unknown"
    
    return requirement_string, "unknown"


def scan_dependencies(repo_path: Path, toolkit_mode: bool = True) -> tuple:
    """
    Scan all dependency files in a repository.
    
    Args:
        repo_path: Path to repository root
        toolkit_mode: If True, apply Toolkit-specific patterns
    
    Returns:
        Tuple of (all_dependencies: List[Dependency], frozen_req_files: List[str])
    """
    all_dependencies = []
    frozen_req_files = []
    
    # Look for requirements.txt files (may be multiple)
    # In toolkit_mode, also search deeper paths
    if toolkit_mode:
        # Toolkit-specific patterns from wiki
        toolkit_req_patterns = [
            "requirements*.txt",
            "*/requirements*.txt",
            "*/*/requirements*.txt",
            "*/*/*/requirements*.txt",
            # Also search for frozen_requirements.txt specifically
            "frozen_requirements.txt",
            "*/frozen_requirements.txt",
            "*/*/frozen_requirements.txt",
            "*/*/*/frozen_requirements.txt",
        ]
        req_files = set()
        for pattern in toolkit_req_patterns:
            req_files.update(repo_path.glob(pattern))
    else:
        req_files = repo_path.rglob("requirements*.txt")
        # Also look for frozen_requirements.txt in generic mode
        req_files = set(req_files)
        req_files.update(repo_path.rglob("frozen_requirements.txt"))
    
    for req_file in req_files:
        # Skip files in .git directories
        if ".git" in req_file.parts:
            continue
        
        rel_path = str(req_file.relative_to(repo_path)).replace("\\", "/")
        
        # Track frozen_requirements.txt files separately
        if "frozen_requirements" in req_file.name.lower():
            frozen_req_files.append(rel_path)
            logger.info(f"Found frozen requirements: {rel_path}")
            # Still parse them for dependencies
        
        logger.info(f"Parsing {rel_path}")
        deps = parse_requirements_txt(req_file)
        all_dependencies.extend(deps)
    
    # Look for pyproject.toml
    pyproject_file = repo_path / "pyproject.toml"
    if pyproject_file.exists():
        logger.info(f"Parsing {pyproject_file.relative_to(repo_path)}")
        deps = parse_pyproject_toml(pyproject_file)
        all_dependencies.extend(deps)
    
    # Look for setup.py
    setup_file = repo_path / "setup.py"
    if setup_file.exists():
        logger.info(f"Parsing {setup_file.relative_to(repo_path)}")
        deps = parse_setup_py(setup_file)
        all_dependencies.extend(deps)
    
    logger.info(f"Found {len(all_dependencies)} dependencies")
    logger.info(f"Found {len(frozen_req_files)} frozen_requirements.txt files")
    
    return all_dependencies, frozen_req_files
