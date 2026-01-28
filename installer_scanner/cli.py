"""
CLI for installation scanner.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from .core import scan_installation
from .merger import merge_inventories
from .models import InstallationInventory


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Scan ShotGrid Desktop installation for components",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan a single installation
  python -m installer_scanner.cli --installation-path /path/to/SGD --output sgd-windows.json
  
  # Scan and specify platform
  python -m installer_scanner.cli --installation-path /path/to/SGD --platform windows --output sgd-win.json
  
  # Merge multiple platform inventories
  python -m installer_scanner.cli --merge sgd-windows.json sgd-macos.json sgd-linux.json --output merged.json
        """
    )
    
    parser.add_argument(
        "--installation-path",
        type=str,
        help="Path to ShotGrid Desktop installation"
    )
    
    parser.add_argument(
        "--platform",
        type=str,
        choices=["windows", "macos", "linux"],
        help="Platform name (auto-detected if not specified)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="installation_inventory.json",
        help="Path to output JSON file"
    )
    
    parser.add_argument(
        "--merge",
        nargs="+",
        type=str,
        help="Merge multiple inventory JSON files (instead of scanning)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.verbose)
    
    try:
        if args.merge:
            # Merge mode
            logging.info(f"Merging {len(args.merge)} inventories...")
            
            inventories = []
            for inv_path in args.merge:
                logging.info(f"Loading {inv_path}...")
                with open(inv_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Reconstruct InstallationInventory
                # Note: This is simplified; full reconstruction would need all nested objects
                inv = InstallationInventory(
                    installation_path=data["installation_path"],
                    platform=data["platform"],
                    scanned_at=data["scanned_at"]
                )
                # Add components from data
                inv.binaries = [type('obj', (object,), b)() for b in data.get("binaries", [])]
                inv.python_modules = [type('obj', (object,), m)() for m in data.get("python_modules", [])]
                inv.toolkit_components = [type('obj', (object,), t)() for t in data.get("toolkit_components", [])]
                inv.fonts = data.get("fonts", [])
                
                inventories.append(inv)
            
            # Merge
            merged = merge_inventories(inventories)
            
            # Save
            output_path = Path(args.output)
            merged.save(output_path)
            logging.info(f"\nMerged inventory saved to: {output_path}")
        
        else:
            # Scan mode
            if not args.installation_path:
                logging.error("--installation-path is required for scanning")
                return 1
            
            installation_path = Path(args.installation_path).resolve()
            output_path = Path(args.output).resolve()
            
            logging.info(f"Installation: {installation_path}")
            logging.info(f"Output file: {output_path}")
            
            # Run scan
            inventory = scan_installation(
                installation_path,
                platform=args.platform
            )
            
            # Save
            inventory.save(output_path)
            logging.info(f"\nInventory saved to: {output_path}")
        
        return 0
    
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
