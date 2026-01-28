"""
Core scanning orchestration logic.

This module coordinates the various detectors and produces the final inventory.
"""

import logging
from pathlib import Path

from .models import Inventory
from .dependency_parser import scan_dependencies
from .vendored_detector import scan_vendored_code
from .asset_detector import scan_assets
from .software_credits_detector import detect_software_credits
from .license_extractor import extract_license_info, find_and_extract_licenses
from .pypi_client import fetch_pypi_info

logger = logging.getLogger(__name__)


def scan_repository(
    repo_path: Path,
    toolkit_mode: bool = True,
    enrich_licenses: bool = True,
    fetch_pypi: bool = True
) -> Inventory:
    """
    Scan a repository and generate a complete third-party inventory.
    
    Args:
        repo_path: Path to the repository root
        toolkit_mode: If True, apply Toolkit-specific detection patterns
        enrich_licenses: If True, extract license information from detected components
        fetch_pypi: If True, fetch package metadata from PyPI for dependencies
    
    Returns:
        Inventory object containing all detected third-party components
    """
    logger.info(f"Starting scan of repository: {repo_path}")
    if toolkit_mode:
        logger.info("Toolkit mode: ENABLED (using ShotGrid Toolkit patterns)")
    
    # Validate repository path
    if not repo_path.exists():
        raise ValueError(f"Repository path does not exist: {repo_path}")
    
    if not repo_path.is_dir():
        raise ValueError(f"Repository path is not a directory: {repo_path}")
    
    # Create inventory
    inventory = Inventory.create(str(repo_path.absolute()))
    
    # Detect software_credits file
    logger.info("=" * 60)
    logger.info("Checking for software_credits file...")
    logger.info("=" * 60)
    inventory.software_credits = detect_software_credits(repo_path)
    if inventory.software_credits.exists:
        if inventory.software_credits.is_empty:
            logger.info("  software_credits exists (placeholder - no TPCs)")
        else:
            logger.info(f"  software_credits exists ({inventory.software_credits.line_count} lines)")
    else:
        logger.info("  software_credits NOT found")
    
    # Run dependency scanner
    logger.info("=" * 60)
    logger.info("Scanning for dependencies...")
    logger.info("=" * 60)
    dependencies, frozen_files = scan_dependencies(repo_path, toolkit_mode)
    inventory.dependencies = dependencies
    inventory.frozen_requirements_files = frozen_files
    
    # Run vendored code detector
    logger.info("=" * 60)
    logger.info("Scanning for vendored third-party code...")
    logger.info("=" * 60)
    inventory.vendored_candidates = scan_vendored_code(repo_path, toolkit_mode)
    
    # Run asset detector
    logger.info("=" * 60)
    logger.info("Scanning for third-party assets...")
    logger.info("=" * 60)
    inventory.asset_candidates = scan_assets(repo_path)
    
    # Enrich with license information
    if enrich_licenses:
        logger.info("=" * 60)
        logger.info("Extracting license information...")
        logger.info("=" * 60)
        _enrich_with_licenses(inventory, repo_path)
    
    # Fetch PyPI information
    if fetch_pypi:
        logger.info("=" * 60)
        logger.info("Fetching PyPI metadata...")
        logger.info("=" * 60)
        _enrich_with_pypi(inventory)
    
    # Summary
    logger.info("=" * 60)
    logger.info("Scan complete!")
    logger.info(f"  software_credits: {'EXISTS' if inventory.software_credits.exists else 'MISSING'}")
    logger.info(f"  Dependencies found: {len(inventory.dependencies)}")
    logger.info(f"  frozen_requirements.txt files: {len(inventory.frozen_requirements_files)}")
    logger.info(f"  Vendored candidates found: {len(inventory.vendored_candidates)}")
    toolkit_vendors = sum(1 for v in inventory.vendored_candidates if v.is_toolkit_pattern)
    if toolkit_mode and toolkit_vendors > 0:
        logger.info(f"    (including {toolkit_vendors} Toolkit-specific patterns)")
    logger.info(f"  Asset candidates found: {len(inventory.asset_candidates)}")
    logger.info("=" * 60)
    
    return inventory


def _enrich_with_licenses(inventory: Inventory, repo_path: Path):
    """
    Enrich inventory with license information.
    
    Extracts license info from vendored candidates that have LICENSE files.
    """
    enriched_count = 0
    
    for candidate in inventory.vendored_candidates:
        if candidate.license_files:
            # Use the first license file found
            license_file_path = repo_path / candidate.license_files[0]
            if license_file_path.exists():
                license_info = extract_license_info(license_file_path, repo_path)
                if license_info:
                    candidate.license_info = license_info
                    enriched_count += 1
                    logger.debug(f"Extracted license for {candidate.path}: {license_info.license_type}")
    
    logger.info(f"Enriched {enriched_count} vendored candidates with license info")


def _enrich_with_pypi(inventory: Inventory):
    """
    Enrich inventory with PyPI metadata.
    
    Fetches package information from PyPI for Python dependencies.
    """
    enriched_count = 0
    
    for dep in inventory.dependencies:
        # Skip if already has PyPI info
        if dep.pypi_info:
            continue
        
        # Skip non-Python packages or test dependencies
        if dep.name.lower() in ["python", "pip", "setuptools", "wheel"]:
            continue
        
        pypi_info = fetch_pypi_info(dep.name, dep.version_spec)
        if pypi_info:
            dep.pypi_info = pypi_info
            enriched_count += 1
    
    logger.info(f"Fetched PyPI info for {enriched_count}/{len(inventory.dependencies)} dependencies")
