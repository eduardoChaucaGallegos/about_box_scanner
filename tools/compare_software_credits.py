"""
CLI tool to compare detected TPCs with software_credits file.

Usage:
    python -m tools.compare_software_credits --inventory inventory.json --repo-path /path/to/repo
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scanner.models import Inventory
from scanner.software_credits_comparer import (
    compare_with_software_credits,
    generate_software_credits_draft
)
from scanner.utils import setup_logging


def load_inventory(inventory_path: Path) -> Inventory:
    """Load inventory from JSON file."""
    try:
        with open(inventory_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Reconstruct Inventory object (simplified)
        # For full reconstruction, we'd need to recreate all nested objects
        # For now, we'll use the JSON data directly
        return data
    except Exception as e:
        logging.error(f"Failed to load inventory: {e}")
        sys.exit(1)


def print_diff_report(report: dict):
    """Print diff report in a readable format."""
    print("\n" + "=" * 80)
    print("SOFTWARE_CREDITS COMPARISON REPORT")
    print("=" * 80)
    print(f"\nRepository: {report['repo_path']}")
    print(f"software_credits exists: {report['software_credits_exists']}")
    
    summary = report['summary']
    print(f"\nSummary:")
    print(f"  [OK] Correct: {summary['correct']}")
    print(f"  [MISSING] Missing in docs: {summary['missing_in_docs']}")
    print(f"  [WARNING] Missing in repo: {summary['missing_in_repo']}")
    print(f"  [MISMATCH] Version mismatches: {summary['version_mismatches']}")
    
    if report['missing_in_docs']:
        print(f"\n[MISSING] TPCs in repo but NOT in software_credits ({len(report['missing_in_docs'])}):")
        for item in report['missing_in_docs']:
            print(f"  - {item['name']} ({item['type']})")
            if item.get('version'):
                print(f"    Version: {item['version']}")
            if item.get('path'):
                print(f"    Path: {item['path']}")
    
    if report['missing_in_repo']:
        print(f"\n[WARNING] TPCs in software_credits but NOT found in repo ({len(report['missing_in_repo'])}):")
        for item in report['missing_in_repo']:
            print(f"  - {item['name']}")
            if item.get('note'):
                print(f"    Note: {item['note']}")
    
    if report['version_mismatches']:
        print(f"\n[MISMATCH] Version mismatches ({len(report['version_mismatches'])}):")
        for item in report['version_mismatches']:
            print(f"  - {item['name']}")
            print(f"    Detected: {item.get('detected_version', 'unknown')}")
            print(f"    Documented: {item.get('documented_version', 'unknown')}")
    
    if report['correct']:
        print(f"\n[OK] Correctly documented ({len(report['correct'])}):")
        for item in report['correct'][:10]:  # Show first 10
            print(f"  - {item['name']}")
            documented_as = item.get('documented_as')
            if documented_as and documented_as != item.get('name'):
                print(f"    (documented as: {documented_as})")
        
        if len(report['correct']) > 10:
            print(f"  ... and {len(report['correct']) - 10} more")
    
    print("\n" + "=" * 80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compare detected TPCs with software_credits file",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--inventory",
        type=str,
        required=True,
        help="Path to inventory JSON file from scanner"
    )
    
    parser.add_argument(
        "--repo-path",
        type=str,
        required=True,
        help="Path to repository root (where software_credits file is located)"
    )
    
    parser.add_argument(
        "--output-report",
        type=str,
        help="Path to save JSON diff report (optional)"
    )
    
    parser.add_argument(
        "--generate-draft",
        type=str,
        help="Path to save draft software_credits file (optional)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    try:
        # Load inventory
        inventory_path = Path(args.inventory)
        logging.info(f"Loading inventory from {inventory_path}")
        inventory_data = load_inventory(inventory_path)
        
        # Note: For proper object reconstruction, we'd need to deserialize properly
        # For now, we'll work with the dict data
        
        # Find software_credits file
        repo_path = Path(args.repo_path)
        software_credits_path = repo_path / "software_credits"
        
        # Compare
        logging.info("Comparing with software_credits...")
        # We need to create a proper Inventory object, but for now let's create a minimal wrapper
        # This is a simplified version for demonstration
        
        from scanner.software_credits_detector import parse_software_credits
        from scanner.software_credits_comparer import DiffReport
        
        report_dict = {
            "repo_path": str(repo_path),
            "software_credits_exists": software_credits_path.exists(),
            "missing_in_docs": [],
            "missing_in_repo": [],
            "version_mismatches": [],
            "correct": [],
        }
        
        if software_credits_path.exists():
            parsed = parse_software_credits(software_credits_path)
            documented_names = [comp["name"] for comp in parsed.get("components", [])]
            
            # Simple comparison logic
            detected_deps = inventory_data.get("dependencies", [])
            for dep in detected_deps:
                dep_name = dep.get("name", "")
                # Simple exact match
                if dep_name in documented_names or dep_name.lower() in [n.lower() for n in documented_names]:
                    report_dict["correct"].append({
                        "type": "dependency",
                        "name": dep_name,
                        "version": dep.get("version_spec", "")
                    })
                else:
                    report_dict["missing_in_docs"].append({
                        "type": "dependency",
                        "name": dep_name,
                        "version": dep.get("version_spec", ""),
                        "source": dep.get("source", "")
                    })
        else:
            # All detected are missing
            for dep in inventory_data.get("dependencies", []):
                report_dict["missing_in_docs"].append({
                    "type": "dependency",
                    "name": dep.get("name", ""),
                    "version": dep.get("version_spec", ""),
                    "source": dep.get("source", "")
                })
        
        # Add summary
        report_dict["summary"] = {
            "correct": len(report_dict["correct"]),
            "missing_in_docs": len(report_dict["missing_in_docs"]),
            "missing_in_repo": len(report_dict["missing_in_repo"]),
            "version_mismatches": len(report_dict["version_mismatches"]),
        }
        
        # Print report
        print_diff_report(report_dict)
        
        # Save report if requested
        if args.output_report:
            with open(args.output_report, "w", encoding="utf-8") as f:
                json.dump(report_dict, f, indent=2)
            logging.info(f"Diff report saved to: {args.output_report}")
        
        # Generate draft if requested
        if args.generate_draft:
            logging.info("Generating draft software_credits...")
            # This would use generate_software_credits_draft() with proper Inventory object
            logging.warning("Draft generation requires full Inventory object reconstruction")
            logging.warning("Please use the integrated scanner with --generate-software-credits option")
        
        return 0
    
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
