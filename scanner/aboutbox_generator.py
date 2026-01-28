"""
About Box HTML Generator

This module generates the license.html file for the ShotGrid Desktop About Box.
It aggregates information from:
- Installation folder inventory (binaries, Python modules)
- Toolkit component inventories (from repo scans)

The output follows the structure defined in Section C of the About Box process:
1. Autodesk header
2. License blocks for binaries (Python, Qt, Fonts, OpenSSL, etc.)
3. License blocks for Python modules
4. Links to software_credits files for all TK repos with TPCs
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class LicenseBlock:
    """Represents a license block in the About Box HTML"""
    component_name: str
    version: Optional[str] = None
    copyright_text: Optional[str] = None
    license_type: Optional[str] = None
    license_text: Optional[str] = None
    url: Optional[str] = None
    is_lgpl: bool = False
    category: str = "other"  # binary, python_module, toolkit, other


@dataclass
class AboutBoxData:
    """Container for all data needed to generate the About Box"""
    binaries: List[LicenseBlock] = field(default_factory=list)
    python_modules: List[LicenseBlock] = field(default_factory=list)
    toolkit_components: List[Dict[str, Any]] = field(default_factory=list)
    lgpl_warnings: List[str] = field(default_factory=list)


def load_installation_inventory(json_path: Path) -> Dict[str, Any]:
    """
    Load the installation inventory JSON from Milestone 4.
    
    Args:
        json_path: Path to the installation inventory JSON file
        
    Returns:
        Dictionary containing the installation inventory
    """
    if not json_path.exists():
        raise FileNotFoundError(f"Installation inventory not found: {json_path}")
    
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_repo_inventory(json_path: Path) -> Dict[str, Any]:
    """
    Load a repo inventory JSON from Milestones 1-3.
    
    Args:
        json_path: Path to the repo inventory JSON file
        
    Returns:
        Dictionary containing the repo inventory
    """
    if not json_path.exists():
        raise FileNotFoundError(f"Repo inventory not found: {json_path}")
    
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_binary_licenses(installation_inv: Dict[str, Any]) -> List[LicenseBlock]:
    """
    Extract license blocks for binaries from the installation inventory.
    
    Args:
        installation_inv: Installation inventory dictionary
        
    Returns:
        List of LicenseBlock objects for binaries
    """
    blocks = []
    
    for binary in installation_inv.get("binaries", []):
        license_info = binary.get("license_info", {})
        
        block = LicenseBlock(
            component_name=binary.get("name", "Unknown"),
            version=binary.get("version"),
            copyright_text="\n".join(license_info.get("copyright_statements", [])) if license_info else None,
            license_type=license_info.get("license_type") if license_info else None,
            license_text=license_info.get("license_text") if license_info else None,
            url=binary.get("url"),
            category="binary"
        )
        
        # Check for LGPL
        if block.license_type and "lgpl" in block.license_type.lower():
            block.is_lgpl = True
        
        blocks.append(block)
    
    return blocks


def extract_python_module_licenses(installation_inv: Dict[str, Any]) -> List[LicenseBlock]:
    """
    Extract license blocks for Python modules from the installation inventory.
    
    Args:
        installation_inv: Installation inventory dictionary
        
    Returns:
        List of LicenseBlock objects for Python modules
    """
    blocks = []
    
    for module in installation_inv.get("python_modules", []):
        license_info = module.get("license_info", {})
        
        block = LicenseBlock(
            component_name=module.get("name", "Unknown"),
            version=module.get("version"),
            copyright_text="\n".join(license_info.get("copyright_statements", [])) if license_info else None,
            license_type=license_info.get("license_type") if license_info else None,
            license_text=license_info.get("license_text") if license_info else None,
            url=module.get("url"),
            category="python_module"
        )
        
        # Check for LGPL
        if block.license_type and "lgpl" in block.license_type.lower():
            block.is_lgpl = True
        
        blocks.append(block)
    
    return blocks


def extract_toolkit_components(repo_inventories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract Toolkit component information from repo inventories.
    
    For each repo with TPCs, we need to include a link to its software_credits file.
    
    Args:
        repo_inventories: List of repo inventory dictionaries
        
    Returns:
        List of dicts with repo name and software_credits info
    """
    components = []
    
    for inv in repo_inventories:
        sc_info = inv.get("software_credits", {})
        
        # Only include repos that have TPCs (i.e., non-empty software_credits)
        if sc_info.get("exists") and not sc_info.get("is_empty", True):
            repo_name = Path(inv.get("repo_path", "unknown")).name
            
            components.append({
                "repo_name": repo_name,
                "software_credits_path": sc_info.get("path"),
                "line_count": sc_info.get("line_count", 0)
            })
    
    return components


def detect_lgpl_components(data: AboutBoxData) -> List[str]:
    """
    Detect all LGPL components and generate warnings.
    
    LGPL components require source code posting to Autodesk's source code posting location.
    
    Args:
        data: AboutBoxData container
        
    Returns:
        List of warning messages
    """
    warnings = []
    
    # Check binaries
    for block in data.binaries:
        if block.is_lgpl:
            warnings.append(
                f"LGPL component detected: {block.component_name} {block.version or ''}. "
                "Source code must be posted to Autodesk source code posting location."
            )
    
    # Check Python modules
    for block in data.python_modules:
        if block.is_lgpl:
            warnings.append(
                f"LGPL component detected: {block.component_name} {block.version or ''}. "
                "Source code must be posted to Autodesk source code posting location."
            )
    
    return warnings


def aggregate_aboutbox_data(
    installation_inv_path: Path,
    repo_inv_paths: List[Path]
) -> AboutBoxData:
    """
    Aggregate all data needed for the About Box HTML.
    
    Args:
        installation_inv_path: Path to installation inventory JSON
        repo_inv_paths: List of paths to repo inventory JSONs
        
    Returns:
        AboutBoxData container with all aggregated information
    """
    logger.info("Loading installation inventory...")
    installation_inv = load_installation_inventory(installation_inv_path)
    
    logger.info("Extracting binary licenses...")
    binaries = extract_binary_licenses(installation_inv)
    
    logger.info("Extracting Python module licenses...")
    python_modules = extract_python_module_licenses(installation_inv)
    
    logger.info(f"Loading {len(repo_inv_paths)} repo inventories...")
    repo_inventories = []
    for path in repo_inv_paths:
        try:
            repo_inventories.append(load_repo_inventory(path))
        except Exception as e:
            logger.warning(f"Failed to load repo inventory {path}: {e}")
    
    logger.info("Extracting Toolkit components...")
    toolkit_components = extract_toolkit_components(repo_inventories)
    
    # Create data container
    data = AboutBoxData(
        binaries=binaries,
        python_modules=python_modules,
        toolkit_components=toolkit_components
    )
    
    # Detect LGPL components
    logger.info("Detecting LGPL components...")
    data.lgpl_warnings = detect_lgpl_components(data)
    
    return data


def format_license_block_html(block: LicenseBlock) -> str:
    """
    Format a single license block as HTML.
    
    Args:
        block: LicenseBlock to format
        
    Returns:
        HTML string for the license block
    """
    html = f'<div class="license-block">\n'
    
    # Component name and version
    name = block.component_name
    if block.version:
        name += f" {block.version}"
    html += f'  <h3>{name}</h3>\n'
    
    # URL (if available)
    if block.url:
        html += f'  <p><a href="{block.url}">{block.url}</a></p>\n'
    
    # Copyright
    if block.copyright_text:
        html += f'  <p class="copyright">{block.copyright_text}</p>\n'
    
    # License type
    if block.license_type:
        html += f'  <p class="license-type"><strong>License:</strong> {block.license_type}</p>\n'
    
    # License text (if available)
    if block.license_text:
        # Truncate very long license texts
        license_preview = block.license_text[:500] + "..." if len(block.license_text) > 500 else block.license_text
        html += f'  <pre class="license-text">{license_preview}</pre>\n'
    
    # LGPL warning
    if block.is_lgpl:
        html += '  <p class="lgpl-warning"><strong>Note:</strong> This is an LGPL component. ' \
                'Source code is available at [AUTODESK SOURCE CODE POSTING URL]</p>\n'
    
    html += '</div>\n'
    
    return html


def generate_aboutbox_html(data: AboutBoxData, template_path: Optional[Path] = None) -> str:
    """
    Generate the complete license.html content for the About Box.
    
    Args:
        data: AboutBoxData container with all information
        template_path: Optional path to HTML template
        
    Returns:
        Complete HTML string
    """
    html = []
    
    # HTML header
    html.append('<!DOCTYPE html>')
    html.append('<html lang="en">')
    html.append('<head>')
    html.append('  <meta charset="UTF-8">')
    html.append('  <title>ShotGrid Desktop - Third Party Licenses</title>')
    html.append('  <style>')
    html.append('    body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }')
    html.append('    h1 { color: #333; }')
    html.append('    h2 { color: #555; margin-top: 30px; border-bottom: 2px solid #ddd; padding-bottom: 5px; }')
    html.append('    h3 { color: #666; }')
    html.append('    .license-block { margin: 20px 0; padding: 15px; background: #f9f9f9; border-left: 3px solid #007acc; }')
    html.append('    .copyright { font-style: italic; }')
    html.append('    .license-type { font-weight: bold; }')
    html.append('    .license-text { background: #fff; padding: 10px; border: 1px solid #ddd; overflow-x: auto; }')
    html.append('    .lgpl-warning { color: #d9534f; font-weight: bold; }')
    html.append('    .software-credits-link { margin: 10px 0; }')
    html.append('  </style>')
    html.append('</head>')
    html.append('<body>')
    
    # Autodesk header
    html.append('<h1>ShotGrid Desktop - Third Party Licenses</h1>')
    html.append('<p>Copyright &copy; 2024 Autodesk, Inc. All rights reserved.</p>')
    html.append('<p>This product includes third-party software components. ')
    html.append('The following is a list of these components and their respective licenses.</p>')
    
    # LGPL warnings (if any)
    if data.lgpl_warnings:
        html.append('<div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 20px 0;">')
        html.append('<h2>Important: LGPL Components</h2>')
        for warning in data.lgpl_warnings:
            html.append(f'<p>{warning}</p>')
        html.append('</div>')
    
    # Section 1: Binaries/Software
    if data.binaries:
        html.append('<h2>Binaries and Software Components</h2>')
        for block in sorted(data.binaries, key=lambda b: b.component_name.lower()):
            html.append(format_license_block_html(block))
    
    # Section 2: Python Modules
    if data.python_modules:
        html.append('<h2>Python Modules</h2>')
        for block in sorted(data.python_modules, key=lambda b: b.component_name.lower()):
            html.append(format_license_block_html(block))
    
    # Section 3: Toolkit Component software_credits Links
    if data.toolkit_components:
        html.append('<h2>Toolkit Components</h2>')
        html.append('<p>The following Toolkit components include third-party code. ')
        html.append('Please refer to their individual <code>software_credits</code> files for details:</p>')
        html.append('<ul>')
        for component in sorted(data.toolkit_components, key=lambda c: c["repo_name"].lower()):
            repo = component["repo_name"]
            sc_path = component.get("software_credits_path", "software_credits")
            github_link = f"https://github.com/shotgunsoftware/{repo}/blob/master/{sc_path}"
            html.append(f'  <li class="software-credits-link">')
            html.append(f'    <strong>{repo}</strong>: ')
            html.append(f'    <a href="{github_link}">software_credits</a>')
            html.append(f'  </li>')
        html.append('</ul>')
    
    # Footer
    html.append('<hr>')
    html.append('<p style="font-size: 0.9em; color: #888;">This document was generated automatically. ')
    html.append('Please review and verify all information before publishing.</p>')
    
    html.append('</body>')
    html.append('</html>')
    
    return '\n'.join(html)


def validate_aboutbox_data(data: AboutBoxData) -> List[str]:
    """
    Validate the About Box data and return a list of warnings/issues.
    
    Args:
        data: AboutBoxData to validate
        
    Returns:
        List of validation warning messages
    """
    warnings = []
    
    # Check for binaries without license info
    for block in data.binaries:
        if not block.license_type and not block.license_text:
            warnings.append(f"Binary '{block.component_name}' is missing license information")
        if not block.copyright_text:
            warnings.append(f"Binary '{block.component_name}' is missing copyright information")
    
    # Check for Python modules without license info
    for block in data.python_modules:
        if not block.license_type and not block.license_text:
            warnings.append(f"Python module '{block.component_name}' is missing license information")
        if not block.copyright_text:
            warnings.append(f"Python module '{block.component_name}' is missing copyright information")
    
    # Check for Toolkit components
    if not data.toolkit_components:
        warnings.append("No Toolkit components with TPCs found. This may indicate missing repo inventories.")
    
    return warnings
