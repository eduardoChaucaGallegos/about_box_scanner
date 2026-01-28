"""
Data models for the third-party inventory.

These classes represent the structured output of the scanning process.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime
import json


@dataclass
class LicenseInfo:
    """Information about a license."""
    
    license_type: Optional[str] = None  # e.g., "MIT", "Apache-2.0", "BSD-3-Clause"
    license_file_path: Optional[str] = None
    license_text: Optional[str] = None
    copyright_statements: List[str] = field(default_factory=list)
    spdx_id: Optional[str] = None  # SPDX identifier if detected
    
    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class PyPIInfo:
    """Information retrieved from PyPI."""
    
    name: str
    version: Optional[str] = None
    license: Optional[str] = None
    home_page: Optional[str] = None
    project_url: Optional[str] = None
    author: Optional[str] = None
    summary: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Dependency:
    """Represents a Python dependency found in dependency files."""
    
    source: str  # e.g., "requirements.txt", "pyproject.toml", "setup.py"
    name: str
    version_spec: str  # e.g., "==1.2.3", ">=1.0,<2.0", "unknown"
    raw_line: Optional[str] = None
    license_info: Optional[LicenseInfo] = None
    pypi_info: Optional[PyPIInfo] = None
    
    def to_dict(self):
        """Convert to dictionary."""
        result = {
            "source": self.source,
            "name": self.name,
            "version_spec": self.version_spec,
            "raw_line": self.raw_line,
        }
        if self.license_info:
            result["license_info"] = self.license_info.to_dict()
        if self.pypi_info:
            result["pypi_info"] = self.pypi_info.to_dict()
        return result


@dataclass
class VendoredCandidate:
    """Represents a potential vendored third-party component."""
    
    path: str  # Relative path from repo root
    reason: str  # Why we think this is vendored third-party code
    license_files: List[str] = field(default_factory=list)
    is_toolkit_pattern: bool = False  # Matches known Toolkit vendor pattern
    license_info: Optional[LicenseInfo] = None
    
    def to_dict(self):
        """Convert to dictionary."""
        result = {
            "path": self.path,
            "reason": self.reason,
            "license_files": self.license_files,
            "is_toolkit_pattern": self.is_toolkit_pattern,
        }
        if self.license_info:
            result["license_info"] = self.license_info.to_dict()
        return result


@dataclass
class AssetCandidate:
    """Represents a potential third-party asset (font, JS, CSS, etc.)."""
    
    path: str  # Relative path from repo root
    type: str  # "font", "js", "css", "other"
    reason: str  # Why we think this is third-party
    
    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SoftwareCreditsInfo:
    """Information about the software_credits file."""
    
    exists: bool
    path: Optional[str] = None
    is_empty: bool = False
    line_count: int = 0
    
    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Inventory:
    """Complete third-party inventory for a repository."""
    
    repo_path: str
    scanned_at: str
    dependencies: List[Dependency] = field(default_factory=list)
    vendored_candidates: List[VendoredCandidate] = field(default_factory=list)
    asset_candidates: List[AssetCandidate] = field(default_factory=list)
    software_credits: Optional[SoftwareCreditsInfo] = None
    frozen_requirements_files: List[str] = field(default_factory=list)
    
    def to_dict(self):
        """Convert to dictionary."""
        result = {
            "repo_path": self.repo_path,
            "scanned_at": self.scanned_at,
            "dependencies": [d.to_dict() for d in self.dependencies],
            "vendored_candidates": [v.to_dict() for v in self.vendored_candidates],
            "asset_candidates": [a.to_dict() for a in self.asset_candidates],
            "frozen_requirements_files": self.frozen_requirements_files,
        }
        if self.software_credits:
            result["software_credits"] = self.software_credits.to_dict()
        return result
    
    def to_json(self, indent=2):
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, output_path):
        """Save inventory to a JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
    
    @classmethod
    def create(cls, repo_path: str):
        """Create a new inventory for the given repository."""
        return cls(
            repo_path=repo_path,
            scanned_at=datetime.utcnow().isoformat() + "Z"
        )
