"""
Multi-platform inventory merger.

Merges inventories from Linux, macOS, and Windows installations.
"""

import logging
from pathlib import Path
from typing import List
from datetime import datetime

from .models import InstallationInventory, MergedInventory

logger = logging.getLogger(__name__)


def normalize_component_name(name: str) -> str:
    """Normalize component name for comparison."""
    return name.lower().strip().replace("-", "").replace("_", "")


def merge_inventories(inventories: List[InstallationInventory]) -> MergedInventory:
    """
    Merge multiple platform inventories into one.
    
    Args:
        inventories: List of InstallationInventory objects
    
    Returns:
        MergedInventory with common and platform-specific components
    """
    if not inventories:
        logger.warning("No inventories to merge")
        return MergedInventory(
            scanned_at=datetime.utcnow().isoformat() + "Z"
        )
    
    logger.info(f"Merging {len(inventories)} platform inventories...")
    
    merged = MergedInventory(
        scanned_at=datetime.utcnow().isoformat() + "Z",
        platforms=[inv.platform for inv in inventories]
    )
    
    # Group components by platform
    binaries_by_platform = {}
    modules_by_platform = {}
    toolkit_by_platform = {}
    
    for inv in inventories:
        platform = inv.platform
        
        # Binaries
        binaries_by_platform[platform] = {
            normalize_component_name(b.name): b.to_dict()
            for b in inv.binaries
        }
        
        # Python modules
        modules_by_platform[platform] = {
            normalize_component_name(m.name): m.to_dict()
            for m in inv.python_modules
        }
        
        # Toolkit components
        toolkit_by_platform[platform] = {
            normalize_component_name(t.name): t.to_dict()
            for t in inv.toolkit_components
        }
    
    # Find common components (present in all platforms)
    all_platforms = set(merged.platforms)
    
    # Common binaries
    all_binary_names = set()
    for platform_bins in binaries_by_platform.values():
        all_binary_names.update(platform_bins.keys())
    
    for bin_name in all_binary_names:
        platforms_with_bin = [
            p for p in all_platforms
            if bin_name in binaries_by_platform.get(p, {})
        ]
        
        if len(platforms_with_bin) == len(all_platforms):
            # Common to all platforms
            # Use first platform's data as representative
            first_platform = list(platforms_with_bin)[0]
            bin_data = binaries_by_platform[first_platform][bin_name].copy()
            bin_data["platforms"] = platforms_with_bin
            merged.common_binaries.append(bin_data)
        else:
            # Platform-specific
            for platform in platforms_with_bin:
                if platform not in merged.platform_specific:
                    merged.platform_specific[platform] = {
                        "binaries": [],
                        "python_modules": [],
                        "toolkit_components": []
                    }
                
                merged.platform_specific[platform]["binaries"].append(
                    binaries_by_platform[platform][bin_name]
                )
    
    # Common Python modules
    all_module_names = set()
    for platform_mods in modules_by_platform.values():
        all_module_names.update(platform_mods.keys())
    
    for mod_name in all_module_names:
        platforms_with_mod = [
            p for p in all_platforms
            if mod_name in modules_by_platform.get(p, {})
        ]
        
        if len(platforms_with_mod) == len(all_platforms):
            # Common to all platforms
            first_platform = list(platforms_with_mod)[0]
            mod_data = modules_by_platform[first_platform][mod_name].copy()
            mod_data["platforms"] = platforms_with_mod
            
            # Collect versions from all platforms
            versions = set()
            for platform in platforms_with_mod:
                version = modules_by_platform[platform][mod_name].get("version")
                if version:
                    versions.add(version)
            
            if len(versions) > 1:
                mod_data["version_note"] = f"Multiple versions: {', '.join(sorted(versions))}"
            
            merged.common_python_modules.append(mod_data)
        else:
            # Platform-specific
            for platform in platforms_with_mod:
                if platform not in merged.platform_specific:
                    merged.platform_specific[platform] = {
                        "binaries": [],
                        "python_modules": [],
                        "toolkit_components": []
                    }
                
                merged.platform_specific[platform]["python_modules"].append(
                    modules_by_platform[platform][mod_name]
                )
    
    # Common Toolkit components
    all_toolkit_names = set()
    for platform_tk in toolkit_by_platform.values():
        all_toolkit_names.update(platform_tk.keys())
    
    for tk_name in all_toolkit_names:
        platforms_with_tk = [
            p for p in all_platforms
            if tk_name in toolkit_by_platform.get(p, {})
        ]
        
        if len(platforms_with_tk) == len(all_platforms):
            # Common to all platforms
            first_platform = list(platforms_with_tk)[0]
            tk_data = toolkit_by_platform[first_platform][tk_name].copy()
            tk_data["platforms"] = platforms_with_tk
            merged.common_toolkit_components.append(tk_data)
        else:
            # Platform-specific
            for platform in platforms_with_tk:
                if platform not in merged.platform_specific:
                    merged.platform_specific[platform] = {
                        "binaries": [],
                        "python_modules": [],
                        "toolkit_components": []
                    }
                
                merged.platform_specific[platform]["toolkit_components"].append(
                    toolkit_by_platform[platform][tk_name]
                )
    
    # Log summary
    logger.info(f"Merge complete:")
    logger.info(f"  Common binaries: {len(merged.common_binaries)}")
    logger.info(f"  Common Python modules: {len(merged.common_python_modules)}")
    logger.info(f"  Common Toolkit components: {len(merged.common_toolkit_components)}")
    logger.info(f"  Platform-specific entries: {len(merged.platform_specific)}")
    
    return merged
