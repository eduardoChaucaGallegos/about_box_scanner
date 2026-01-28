"""
Command-line interface for the About Box Scanner.
"""

import argparse
import logging
import sys
from pathlib import Path

from .core import scan_repository
from .utils import setup_logging

logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Scan repositories for third-party components and generate inventories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan a repository
  python -m scanner --repo-path /path/to/tk-core --output inventory.json
  
  # Scan with verbose output
  python -m scanner --repo-path /path/to/tk-desktop --output output.json -v
        """
    )
    
    parser.add_argument(
        "--repo-path",
        type=str,
        required=True,
        help="Path to the repository to scan"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="third_party_inventory.json",
        help="Path to output JSON file (default: third_party_inventory.json)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--no-toolkit-mode",
        action="store_true",
        help="Disable Toolkit-specific detection patterns (use generic scanning only)"
    )
    
    parser.add_argument(
        "--no-license-extraction",
        action="store_true",
        help="Skip license information extraction"
    )
    
    parser.add_argument(
        "--no-pypi",
        action="store_true",
        help="Skip fetching package metadata from PyPI"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the CLI."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.verbose)
    
    try:
        # Convert paths to Path objects
        repo_path = Path(args.repo_path).resolve()
        output_path = Path(args.output).resolve()
        
        logger.info(f"Repository: {repo_path}")
        logger.info(f"Output file: {output_path}")
        
        # Determine scan options
        toolkit_mode = not args.no_toolkit_mode
        enrich_licenses = not args.no_license_extraction
        fetch_pypi = not args.no_pypi
        
        # Run the scan
        inventory = scan_repository(
            repo_path,
            toolkit_mode=toolkit_mode,
            enrich_licenses=enrich_licenses,
            fetch_pypi=fetch_pypi
        )
        
        # Save the inventory
        inventory.save(output_path)
        logger.info(f"\nInventory saved to: {output_path}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
