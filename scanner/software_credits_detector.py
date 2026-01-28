"""
Detector for software_credits files.

Per the wiki: "Repositories that have Third Party Components must have
a file named software_credits in the root folder."
"""

import logging
from pathlib import Path

from .models import SoftwareCreditsInfo

logger = logging.getLogger(__name__)


def detect_software_credits(repo_path: Path) -> SoftwareCreditsInfo:
    """
    Detect and analyze the software_credits file in a repository.
    
    Args:
        repo_path: Path to repository root
    
    Returns:
        SoftwareCreditsInfo object with details about the file
    """
    # Look for software_credits file (no extension)
    software_credits_file = repo_path / "software_credits"
    
    if not software_credits_file.exists():
        logger.debug("No software_credits file found")
        return SoftwareCreditsInfo(exists=False)
    
    try:
        # Read file to check if it's empty or minimal
        with open(software_credits_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        lines = content.strip().split("\n")
        line_count = len([line for line in lines if line.strip()])
        
        # Check if it's the "no third parties" placeholder
        is_empty = (
            line_count <= 3 and
            "does not include any third" in content.lower()
        )
        
        logger.info(f"Found software_credits file: {line_count} non-empty lines")
        
        return SoftwareCreditsInfo(
            exists=True,
            path="software_credits",
            is_empty=is_empty,
            line_count=line_count
        )
    
    except Exception as e:
        logger.warning(f"Error reading software_credits file: {e}")
        return SoftwareCreditsInfo(
            exists=True,
            path="software_credits",
            is_empty=False,
            line_count=0
        )


def parse_software_credits(software_credits_path: Path) -> dict:
    """
    Parse a software_credits file and extract component information.
    
    Args:
        software_credits_path: Path to software_credits file
    
    Returns:
        Dictionary with parsed sections:
        {
            "header": "intro text",
            "components": [
                {
                    "name": "Component Name",
                    "url": "https://...",
                    "content": "full license text"
                }
            ]
        }
    """
    try:
        with open(software_credits_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        # Split by section markers (lines starting with ===)
        sections = []
        current_section = None
        header_lines = []
        in_header = True
        
        for line in content.split("\n"):
            # Check if this is a section header
            if line.startswith("===") or line.startswith("=="):
                in_header = False
                # Save previous section if exists
                if current_section:
                    sections.append(current_section)
                
                # Parse new section header
                # Format: === Name (URL) ===
                import re
                match = re.search(r"^=+\s*(.+?)\s*\(([^)]+)\)\s*=+", line)
                if match:
                    name = match.group(1).strip()
                    url = match.group(2).strip()
                    current_section = {
                        "name": name,
                        "url": url,
                        "content": "",
                        "raw_header": line
                    }
                else:
                    # Fallback: just extract what's between === markers
                    cleaned = line.strip("= ")
                    current_section = {
                        "name": cleaned,
                        "url": "",
                        "content": "",
                        "raw_header": line
                    }
            else:
                # Add to current section or header
                if in_header:
                    header_lines.append(line)
                elif current_section is not None:
                    current_section["content"] += line + "\n"
        
        # Don't forget the last section
        if current_section:
            sections.append(current_section)
        
        logger.info(f"Parsed {len(sections)} components from software_credits")
        
        return {
            "header": "\n".join(header_lines).strip(),
            "components": sections
        }
    
    except Exception as e:
        logger.error(f"Error parsing software_credits: {e}")
        return {
            "header": "",
            "components": []
        }
