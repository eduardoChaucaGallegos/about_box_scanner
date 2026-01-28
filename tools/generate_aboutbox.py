"""
About Box Generator CLI

This tool generates the license.html file for the ShotGrid Desktop About Box.

It takes:
- An installation folder inventory (from Milestone 4)
- One or more repo inventories (from Milestones 1-3)

And outputs:
- A draft license.html file ready for human/legal review

Usage:
    python -m tools.generate_aboutbox \
        --installation installer_inventory.json \
        --repos tk-core_inventory.json tk-desktop_inventory.json ... \
        --output license.html
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scanner.aboutbox_generator import (
    aggregate_aboutbox_data,
    generate_aboutbox_html,
    validate_aboutbox_data,
    AboutBoxData
)


def setup_logging(verbose: bool = False):
    """Configure logging for the CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s"
    )


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate the license.html file for ShotGrid Desktop About Box",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate About Box from one installation and multiple repo inventories
  python -m tools.generate_aboutbox \\
      --installation installer_inventory.json \\
      --repos tk-core_inventory.json tk-desktop_inventory.json \\
      --output license.html

  # Use a directory of repo inventories
  python -m tools.generate_aboutbox \\
      --installation installer_inventory.json \\
      --repo-dir inventories/ \\
      --output license.html

  # Validate only (don't generate HTML)
  python -m tools.generate_aboutbox \\
      --installation installer_inventory.json \\
      --repos *.json \\
      --validate-only
        """
    )
    
    parser.add_argument(
        "--installation",
        type=Path,
        required=True,
        help="Path to the installation inventory JSON (from Milestone 4)"
    )
    
    parser.add_argument(
        "--repos",
        type=Path,
        nargs="+",
        help="Paths to one or more repo inventory JSON files (from Milestones 1-3)"
    )
    
    parser.add_argument(
        "--repo-dir",
        type=Path,
        help="Directory containing repo inventory JSON files (alternative to --repos)"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default="license.html",
        help="Output HTML file path (default: license.html)"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the data, don't generate HTML"
    )
    
    parser.add_argument(
        "--template",
        type=Path,
        help="Optional path to custom HTML template"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def collect_repo_inventories(args) -> List[Path]:
    """
    Collect all repo inventory paths from command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        List of Path objects to repo inventory JSON files
    """
    repo_paths = []
    
    # From --repos argument
    if args.repos:
        repo_paths.extend(args.repos)
    
    # From --repo-dir argument
    if args.repo_dir:
        if not args.repo_dir.is_dir():
            logging.error(f"Repo directory not found: {args.repo_dir}")
            sys.exit(1)
        
        # Find all JSON files in the directory
        json_files = list(args.repo_dir.glob("*.json"))
        logging.info(f"Found {len(json_files)} JSON files in {args.repo_dir}")
        repo_paths.extend(json_files)
    
    # Validate that we have at least one repo inventory
    if not repo_paths:
        logging.error("No repo inventories specified. Use --repos or --repo-dir")
        sys.exit(1)
    
    # Validate that all paths exist
    for path in repo_paths:
        if not path.exists():
            logging.error(f"Repo inventory not found: {path}")
            sys.exit(1)
    
    return repo_paths


def print_validation_report(warnings: List[str], lgpl_warnings: List[str]):
    """
    Print a validation report with warnings and issues.
    
    Args:
        warnings: List of validation warning messages
        lgpl_warnings: List of LGPL component warnings
    """
    print("\n" + "="*80)
    print("VALIDATION REPORT")
    print("="*80)
    
    if lgpl_warnings:
        print("\nLGPL COMPONENTS (Require Source Code Posting):")
        print("-" * 80)
        for i, warning in enumerate(lgpl_warnings, 1):
            print(f"{i}. {warning}")
    
    if warnings:
        print("\nWARNINGS:")
        print("-" * 80)
        for i, warning in enumerate(warnings, 1):
            print(f"{i}. {warning}")
    
    if not warnings and not lgpl_warnings:
        print("\nNo issues found.")
    
    print("="*80 + "\n")


def print_summary(data: AboutBoxData, output_path: Path):
    """
    Print a summary of the generated About Box.
    
    Args:
        data: AboutBoxData container
        output_path: Path where the HTML was written
    """
    print("\n" + "="*80)
    print("ABOUT BOX SUMMARY")
    print("="*80)
    print(f"\nGenerated: {output_path}")
    print(f"  - Binaries: {len(data.binaries)}")
    print(f"  - Python modules: {len(data.python_modules)}")
    print(f"  - Toolkit components: {len(data.toolkit_components)}")
    
    if data.lgpl_warnings:
        print(f"\n  WARNING: {len(data.lgpl_warnings)} LGPL component(s) detected")
        print("  These require source code posting to Autodesk source code posting location.")
    
    print("\n" + "="*80)
    print("\nNEXT STEPS:")
    print("  1. Review the generated license.html file")
    print("  2. Verify all license information is correct")
    print("  3. Check with Legal partner for approval")
    print("  4. Handle any LGPL source code posting requirements")
    print("  5. Create a PR to tk-desktop with the updated license.html")
    print("="*80 + "\n")


def main():
    """Main entry point for the About Box generator CLI."""
    args = parse_args()
    setup_logging(args.verbose)
    
    # Collect repo inventories
    logging.info("Collecting repo inventories...")
    repo_paths = collect_repo_inventories(args)
    logging.info(f"Found {len(repo_paths)} repo inventories")
    
    # Aggregate data
    try:
        logging.info("Aggregating About Box data...")
        data = aggregate_aboutbox_data(args.installation, repo_paths)
    except Exception as e:
        logging.error(f"Failed to aggregate data: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    # Validate data
    logging.info("Validating data...")
    validation_warnings = validate_aboutbox_data(data)
    
    # Print validation report
    print_validation_report(validation_warnings, data.lgpl_warnings)
    
    # If validate-only mode, stop here
    if args.validate_only:
        logging.info("Validation complete. Skipping HTML generation (--validate-only).")
        sys.exit(0)
    
    # Generate HTML
    try:
        logging.info("Generating license.html...")
        html_content = generate_aboutbox_html(data, args.template)
        
        # Write to output file
        args.output.write_text(html_content, encoding="utf-8")
        logging.info(f"Successfully wrote {len(html_content)} characters to {args.output}")
        
    except Exception as e:
        logging.error(f"Failed to generate HTML: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    # Print summary
    print_summary(data, args.output)


if __name__ == "__main__":
    main()
