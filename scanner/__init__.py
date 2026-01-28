"""
About Box Scanner - Third-party component inventory tool.

This package provides tools to scan repositories and identify third-party
components, dependencies, and assets for license review processes.
"""

__version__ = "0.1.0"

from .models import (
    Inventory,
    Dependency,
    VendoredCandidate,
    AssetCandidate,
    SoftwareCreditsInfo,
    LicenseInfo,
    PyPIInfo,
)
from .aboutbox_generator import (
    aggregate_aboutbox_data,
    generate_aboutbox_html,
    validate_aboutbox_data,
    AboutBoxData,
    LicenseBlock,
)

__all__ = [
    "Inventory",
    "Dependency",
    "VendoredCandidate",
    "AssetCandidate",
    "SoftwareCreditsInfo",
    "LicenseInfo",
    "PyPIInfo",
    "aggregate_aboutbox_data",
    "generate_aboutbox_html",
    "validate_aboutbox_data",
    "AboutBoxData",
    "LicenseBlock",
]
