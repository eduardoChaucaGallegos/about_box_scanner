"""
Data models for installation inventory.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime
import json


@dataclass
class BinaryComponent:
    """Represents a binary/software component in the installation."""
    
    name: str
    path: str  # Relative or absolute path
    version: Optional[str] = None
    type: str = "binary"  # "binary", "library", "executable"
    architecture: Optional[str] = None  # "x86_64", "arm64", etc.
    
    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class PythonModule:
    """Represents a Python module/package."""
    
    name: str
    version: Optional[str] = None
    location: Optional[str] = None
    license: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ToolkitComponent:
    """Represents a Toolkit component (tk-core, tk-desktop, etc.)."""
    
    name: str
    path: str
    version: Optional[str] = None
    has_software_credits: bool = False
    
    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class InstallationInventory:
    """Complete inventory of a SGD installation."""
    
    installation_path: str
    platform: str  # "windows", "macos", "linux"
    scanned_at: str
    
    binaries: List[BinaryComponent] = field(default_factory=list)
    python_modules: List[PythonModule] = field(default_factory=list)
    toolkit_components: List[ToolkitComponent] = field(default_factory=list)
    fonts: List[str] = field(default_factory=list)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "installation_path": self.installation_path,
            "platform": self.platform,
            "scanned_at": self.scanned_at,
            "binaries": [b.to_dict() for b in self.binaries],
            "python_modules": [m.to_dict() for m in self.python_modules],
            "toolkit_components": [t.to_dict() for t in self.toolkit_components],
            "fonts": self.fonts,
        }
    
    def to_json(self, indent=2):
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, output_path):
        """Save inventory to JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
    
    @classmethod
    def create(cls, installation_path: str, platform: str):
        """Create a new inventory."""
        return cls(
            installation_path=installation_path,
            platform=platform,
            scanned_at=datetime.utcnow().isoformat() + "Z"
        )


@dataclass
class MergedInventory:
    """Merged inventory from multiple platforms."""
    
    scanned_at: str
    platforms: List[str] = field(default_factory=list)
    
    # Components present in all platforms
    common_binaries: List[dict] = field(default_factory=list)
    common_python_modules: List[dict] = field(default_factory=list)
    common_toolkit_components: List[dict] = field(default_factory=list)
    
    # Platform-specific components
    platform_specific: dict = field(default_factory=dict)
    
    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self, indent=2):
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, output_path):
        """Save merged inventory to JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
