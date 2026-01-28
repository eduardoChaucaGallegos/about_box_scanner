"""
Software Credits Comparer and Generator.

Compares detected TPCs with documented TPCs in software_credits file,
generates diff reports, and creates draft updated software_credits files.
"""

import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, field

from .models import Inventory, Dependency, VendoredCandidate
from .software_credits_detector import parse_software_credits

logger = logging.getLogger(__name__)


@dataclass
class ComponentMatch:
    """Represents a match between detected TPC and documented component."""
    
    detected_name: str
    documented_name: str
    match_score: float  # 0.0 to 1.0
    detected_version: str = ""
    documented_version: str = ""
    status: str = "matched"  # matched, version_mismatch, missing_in_docs, missing_in_repo


@dataclass
class DiffReport:
    """Report of differences between detected and documented TPCs."""
    
    repo_path: str
    software_credits_exists: bool
    
    # TPCs in repo but NOT in software_credits
    missing_in_docs: List[Dict] = field(default_factory=list)
    
    # TPCs in software_credits but NOT found in repo
    missing_in_repo: List[Dict] = field(default_factory=list)
    
    # TPCs with version mismatches
    version_mismatches: List[Dict] = field(default_factory=list)
    
    # TPCs that match correctly
    correct: List[Dict] = field(default_factory=list)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "repo_path": self.repo_path,
            "software_credits_exists": self.software_credits_exists,
            "summary": {
                "missing_in_docs": len(self.missing_in_docs),
                "missing_in_repo": len(self.missing_in_repo),
                "version_mismatches": len(self.version_mismatches),
                "correct": len(self.correct),
            },
            "missing_in_docs": self.missing_in_docs,
            "missing_in_repo": self.missing_in_repo,
            "version_mismatches": self.version_mismatches,
            "correct": self.correct,
        }


def normalize_component_name(name: str) -> str:
    """
    Normalize component name for comparison.
    
    Handles variations like:
    - "PyYAML" vs "pyyaml"
    - "ruamel.yaml" vs "ruamel_yaml"
    - "Open Sans" vs "OpenSans"
    """
    normalized = name.lower()
    normalized = normalized.replace("_", "").replace("-", "").replace(".", "").replace(" ", "")
    return normalized


def fuzzy_match_component(detected_name: str, documented_names: List[str]) -> Tuple[str, float]:
    """
    Find best match for a detected component in documented names.
    
    Returns:
        Tuple of (best_match_name, score) or ("", 0.0) if no good match
    """
    detected_norm = normalize_component_name(detected_name)
    
    best_match = ""
    best_score = 0.0
    
    for doc_name in documented_names:
        doc_norm = normalize_component_name(doc_name)
        
        # Exact match after normalization
        if detected_norm == doc_norm:
            return doc_name, 1.0
        
        # Substring match
        if detected_norm in doc_norm or doc_norm in detected_norm:
            score = 0.8
            if score > best_score:
                best_score = score
                best_match = doc_name
        
        # Partial match (for cases like "yaml" matching "pyyaml")
        shorter = min(len(detected_norm), len(doc_norm))
        if shorter > 3:  # Only for reasonable length names
            matching_chars = sum(1 for a, b in zip(detected_norm, doc_norm) if a == b)
            score = matching_chars / max(len(detected_norm), len(doc_norm))
            if score > 0.6 and score > best_score:
                best_score = score
                best_match = doc_name
    
    return best_match, best_score


def compare_with_software_credits(
    inventory: Inventory,
    software_credits_path: Path
) -> DiffReport:
    """
    Compare detected TPCs with software_credits file.
    
    Args:
        inventory: Inventory from scanning
        software_credits_path: Path to software_credits file
    
    Returns:
        DiffReport with differences
    """
    repo_path = Path(inventory.repo_path)
    report = DiffReport(
        repo_path=str(repo_path),
        software_credits_exists=software_credits_path.exists()
    )
    
    if not software_credits_path.exists():
        # All detected TPCs are missing in docs
        for dep in inventory.dependencies:
            report.missing_in_docs.append({
                "type": "dependency",
                "name": dep.name,
                "version": dep.version_spec,
                "source": dep.source
            })
        
        for vendor in inventory.vendored_candidates:
            report.missing_in_docs.append({
                "type": "vendored",
                "name": Path(vendor.path).name,
                "path": vendor.path,
                "license_files": vendor.license_files
            })
        
        for asset in inventory.asset_candidates:
            report.missing_in_docs.append({
                "type": "asset",
                "name": Path(asset.path).name,
                "path": asset.path,
                "asset_type": asset.type
            })
        
        logger.info(f"software_credits not found: {len(report.missing_in_docs)} TPCs undocumented")
        return report
    
    # Parse software_credits
    parsed = parse_software_credits(software_credits_path)
    documented_components = parsed.get("components", [])
    documented_names = [comp["name"] for comp in documented_components]
    
    logger.info(f"Found {len(documented_components)} documented components")
    
    # Track which documented components we've matched
    matched_documented = set()
    
    # Check dependencies
    for dep in inventory.dependencies:
        match_name, score = fuzzy_match_component(dep.name, documented_names)
        
        if score >= 0.7:  # Good match
            matched_documented.add(match_name)
            # Check version
            if dep.version_spec and dep.version_spec != "unknown":
                report.correct.append({
                    "type": "dependency",
                    "name": dep.name,
                    "documented_as": match_name,
                    "version": dep.version_spec,
                    "match_score": score
                })
            else:
                report.correct.append({
                    "type": "dependency",
                    "name": dep.name,
                    "documented_as": match_name,
                    "version": dep.version_spec,
                    "match_score": score
                })
        else:
            report.missing_in_docs.append({
                "type": "dependency",
                "name": dep.name,
                "version": dep.version_spec,
                "source": dep.source
            })
    
    # Check vendored candidates
    for vendor in inventory.vendored_candidates:
        vendor_name = Path(vendor.path).name
        match_name, score = fuzzy_match_component(vendor_name, documented_names)
        
        if score >= 0.6:  # Slightly lower threshold for vendored
            matched_documented.add(match_name)
            report.correct.append({
                "type": "vendored",
                "name": vendor_name,
                "documented_as": match_name,
                "path": vendor.path,
                "match_score": score
            })
        else:
            report.missing_in_docs.append({
                "type": "vendored",
                "name": vendor_name,
                "path": vendor.path,
                "license_files": vendor.license_files
            })
    
    # Check for documented components not found in repo
    for doc_comp in documented_components:
        if doc_comp["name"] not in matched_documented:
            # Double-check with fuzzy matching against all detected names
            all_detected_names = (
                [dep.name for dep in inventory.dependencies] +
                [Path(v.path).name for v in inventory.vendored_candidates]
            )
            match_name, score = fuzzy_match_component(doc_comp["name"], all_detected_names)
            
            if score < 0.6:  # No good match found
                report.missing_in_repo.append({
                    "name": doc_comp["name"],
                    "url": doc_comp.get("url", ""),
                    "note": "May have been removed or renamed"
                })
    
    # Log summary
    logger.info(f"Comparison complete:")
    logger.info(f"  ✅ Correct: {len(report.correct)}")
    logger.info(f"  ❌ Missing in docs: {len(report.missing_in_docs)}")
    logger.info(f"  ⚠️  Missing in repo: {len(report.missing_in_repo)}")
    logger.info(f"  🔄 Version mismatches: {len(report.version_mismatches)}")
    
    return report


def generate_software_credits_draft(
    inventory: Inventory,
    existing_credits_path: Path = None
) -> str:
    """
    Generate a draft software_credits file content.
    
    Args:
        inventory: Inventory from scanning
        existing_credits_path: Optional path to existing software_credits to preserve formatting
    
    Returns:
        Draft content as string
    """
    lines = []
    
    # Header
    lines.append("The following licenses and copyright notices apply to various components")
    lines.append(f"of {Path(inventory.repo_path).name} as outlined below.")
    lines.append("")
    lines.append("")
    
    # Collect all components
    components = []
    
    # Add dependencies with PyPI info
    for dep in inventory.dependencies:
        comp_name = dep.name
        comp_url = ""
        license_text = ""
        
        if dep.pypi_info:
            comp_name = dep.pypi_info.name or dep.name
            comp_url = dep.pypi_info.project_url or dep.pypi_info.home_page or ""
        
        if dep.license_info and dep.license_info.license_text:
            license_text = dep.license_info.license_text
        elif dep.pypi_info and dep.pypi_info.license:
            license_text = f"License: {dep.pypi_info.license}\n\n(Full license text should be obtained from {comp_url})"
        
        if license_text or comp_url:
            components.append({
                "name": comp_name,
                "url": comp_url,
                "content": license_text
            })
    
    # Add vendored with license info
    for vendor in inventory.vendored_candidates:
        comp_name = Path(vendor.path).name
        comp_url = vendor.path
        license_text = ""
        
        if vendor.license_info:
            license_text = vendor.license_info.license_text or ""
            if vendor.license_info.copyright_statements:
                copyright_text = "\n".join(vendor.license_info.copyright_statements[:3])  # First 3
                license_text = copyright_text + "\n\n" + license_text
        
        if license_text:
            components.append({
                "name": comp_name,
                "url": comp_url,
                "content": license_text
            })
    
    # Sort alphabetically
    components.sort(key=lambda c: c["name"].lower())
    
    # Generate sections
    for comp in components:
        # Section header
        header = f"=== {comp['name']}"
        if comp['url']:
            header += f" ({comp['url']})"
        header += " " + "=" * (80 - len(header))
        lines.append(header)
        lines.append("")
        
        # Content
        lines.append(comp['content'].strip())
        lines.append("")
        lines.append("")
    
    return "\n".join(lines)
