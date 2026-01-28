"""
Detector for third-party assets.

Identifies fonts, JavaScript libraries, CSS libraries, and other static
assets that might be third-party components.
"""

import logging
from pathlib import Path
from typing import List, Set

from .models import AssetCandidate
from .utils import find_files_by_extension, relative_path, should_skip_directory

logger = logging.getLogger(__name__)

# File extensions for different asset types
FONT_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2", ".eot"}
JS_EXTENSIONS = {".js"}
CSS_EXTENSIONS = {".css"}

# Known third-party library names (partial matches)
KNOWN_THIRD_PARTY_NAMES = {
    "jquery", "bootstrap", "fontawesome", "font-awesome",
    "lodash", "underscore", "backbone", "react", "vue", "angular",
    "d3", "chart", "moment", "axios", "csinterface",
    "ace", "codemirror", "highlight.js", "prism",
}

# Directory names that often contain third-party assets
ASSET_DIR_NAMES = {
    "fonts", "font", "js", "javascript", "css", "styles",
    "lib", "libs", "vendor", "third_party", "assets",
    "static", "public", "resources",
}


def scan_assets(repo_path: Path) -> List[AssetCandidate]:
    """
    Scan repository for third-party assets.
    
    Detects:
    - Font files (TTF, OTF, WOFF, etc.)
    - JavaScript files that look like libraries
    - CSS files that look like libraries
    """
    candidates = []
    
    # Scan for fonts
    logger.info("Scanning for font files...")
    candidates.extend(_scan_fonts(repo_path))
    
    # Scan for JavaScript libraries
    logger.info("Scanning for JavaScript files...")
    candidates.extend(_scan_javascript(repo_path))
    
    # Scan for CSS libraries
    logger.info("Scanning for CSS files...")
    candidates.extend(_scan_css(repo_path))
    
    logger.info(f"Found {len(candidates)} asset candidates")
    return candidates


def _scan_fonts(repo_path: Path) -> List[AssetCandidate]:
    """Scan for font files."""
    candidates = []
    font_files = find_files_by_extension(repo_path, FONT_EXTENSIONS)
    
    for font_file in font_files:
        reason = _determine_font_reason(font_file, repo_path)
        candidates.append(AssetCandidate(
            path=relative_path(font_file, repo_path),
            type="font",
            reason=reason
        ))
    
    return candidates


def _scan_javascript(repo_path: Path) -> List[AssetCandidate]:
    """Scan for JavaScript library files."""
    candidates = []
    js_files = find_files_by_extension(repo_path, JS_EXTENSIONS)
    
    for js_file in js_files:
        # Only include if it looks like a third-party library
        if _looks_like_third_party_js(js_file, repo_path):
            reason = _determine_js_reason(js_file, repo_path)
            candidates.append(AssetCandidate(
                path=relative_path(js_file, repo_path),
                type="js",
                reason=reason
            ))
    
    return candidates


def _scan_css(repo_path: Path) -> List[AssetCandidate]:
    """Scan for CSS library files."""
    candidates = []
    css_files = find_files_by_extension(repo_path, CSS_EXTENSIONS)
    
    for css_file in css_files:
        # Only include if it looks like a third-party library
        if _looks_like_third_party_css(css_file, repo_path):
            reason = _determine_css_reason(css_file, repo_path)
            candidates.append(AssetCandidate(
                path=relative_path(css_file, repo_path),
                type="css",
                reason=reason
            ))
    
    return candidates


def _determine_font_reason(font_file: Path, repo_path: Path) -> str:
    """Determine why a font file is considered third-party."""
    reasons = []
    
    # Check file name for known fonts
    name_lower = font_file.stem.lower()
    if any(known in name_lower for known in KNOWN_THIRD_PARTY_NAMES):
        reasons.append("known_font_name")
    
    # Check if in a font directory
    if any(part.lower() in ASSET_DIR_NAMES for part in font_file.parts):
        reasons.append("in_font_directory")
    
    # All fonts are likely third-party unless custom
    if not reasons:
        reasons.append("font_file_extension")
    
    return " | ".join(reasons)


def _looks_like_third_party_js(js_file: Path, repo_path: Path) -> bool:
    """Check if a JavaScript file looks like a third-party library."""
    name_lower = js_file.stem.lower()
    
    # Check for known library names
    if any(known in name_lower for known in KNOWN_THIRD_PARTY_NAMES):
        return True
    
    # Check if file has .min.js (minified)
    if js_file.name.endswith(".min.js"):
        return True
    
    # Check if in a vendor/lib directory
    if any(part.lower() in {"lib", "libs", "vendor", "third_party"} for part in js_file.parts):
        return True
    
    # Check file size (large JS files are often libraries)
    try:
        size_kb = js_file.stat().st_size / 1024
        if size_kb > 50:  # Larger than 50KB is often a library
            return True
    except Exception:
        pass
    
    return False


def _looks_like_third_party_css(css_file: Path, repo_path: Path) -> bool:
    """Check if a CSS file looks like a third-party library."""
    name_lower = css_file.stem.lower()
    
    # Check for known library names
    if any(known in name_lower for known in KNOWN_THIRD_PARTY_NAMES):
        return True
    
    # Check if file has .min.css (minified)
    if css_file.name.endswith(".min.css"):
        return True
    
    # Check if in a vendor/lib directory
    if any(part.lower() in {"lib", "libs", "vendor", "third_party"} for part in css_file.parts):
        return True
    
    # Check file size (large CSS files are often libraries)
    try:
        size_kb = css_file.stat().st_size / 1024
        if size_kb > 30:  # Larger than 30KB is often a library
            return True
    except Exception:
        pass
    
    return False


def _determine_js_reason(js_file: Path, repo_path: Path) -> str:
    """Determine why a JS file is considered third-party."""
    reasons = []
    
    name_lower = js_file.stem.lower()
    
    if any(known in name_lower for known in KNOWN_THIRD_PARTY_NAMES):
        reasons.append("known_library_name")
    
    if js_file.name.endswith(".min.js"):
        reasons.append("minified")
    
    if any(part.lower() in {"lib", "libs", "vendor", "third_party"} for part in js_file.parts):
        reasons.append("in_vendor_directory")
    
    try:
        size_kb = js_file.stat().st_size / 1024
        if size_kb > 50:
            reasons.append("large_file_size")
    except Exception:
        pass
    
    if not reasons:
        reasons.append("heuristic_match")
    
    return " | ".join(reasons)


def _determine_css_reason(css_file: Path, repo_path: Path) -> str:
    """Determine why a CSS file is considered third-party."""
    reasons = []
    
    name_lower = css_file.stem.lower()
    
    if any(known in name_lower for known in KNOWN_THIRD_PARTY_NAMES):
        reasons.append("known_library_name")
    
    if css_file.name.endswith(".min.css"):
        reasons.append("minified")
    
    if any(part.lower() in {"lib", "libs", "vendor", "third_party"} for part in css_file.parts):
        reasons.append("in_vendor_directory")
    
    try:
        size_kb = css_file.stat().st_size / 1024
        if size_kb > 30:
            reasons.append("large_file_size")
    except Exception:
        pass
    
    if not reasons:
        reasons.append("heuristic_match")
    
    return " | ".join(reasons)
