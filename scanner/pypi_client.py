"""
PyPI API client for fetching package metadata.

Uses the PyPI JSON API to retrieve package information.
"""

import logging
import json
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from .models import PyPIInfo

logger = logging.getLogger(__name__)

PYPI_API_URL = "https://pypi.org/pypi/{package}/json"
PYPI_VERSION_API_URL = "https://pypi.org/pypi/{package}/{version}/json"


def fetch_pypi_info(package_name: str, version: Optional[str] = None) -> Optional[PyPIInfo]:
    """
    Fetch package information from PyPI.
    
    Args:
        package_name: Name of the package
        version: Specific version to fetch (optional, fetches latest if not specified)
    
    Returns:
        PyPIInfo object or None if unable to fetch
    """
    try:
        # Construct URL
        if version and version not in ["unknown", ""]:
            # Clean version spec (remove ==, >=, etc.)
            clean_version = version.strip("=<>!~")
            # If it still contains operators or commas, fetch latest
            if any(op in clean_version for op in ["<", ">", "!", "~", ","]):
                url = PYPI_API_URL.format(package=package_name)
            else:
                url = PYPI_VERSION_API_URL.format(package=package_name, version=clean_version)
        else:
            url = PYPI_API_URL.format(package=package_name)
        
        logger.debug(f"Fetching PyPI info for {package_name} from {url}")
        
        # Make request with User-Agent header
        request = Request(url, headers={"User-Agent": "about-box-scanner/0.1.0"})
        
        with urlopen(request, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        # Extract info from response
        info = data.get("info", {})
        
        pypi_info = PyPIInfo(
            name=info.get("name", package_name),
            version=info.get("version"),
            license=info.get("license"),
            home_page=info.get("home_page"),
            project_url=info.get("project_url") or info.get("package_url"),
            author=info.get("author"),
            summary=info.get("summary"),
        )
        
        logger.info(f"Retrieved PyPI info for {package_name} v{pypi_info.version}")
        return pypi_info
    
    except HTTPError as e:
        if e.code == 404:
            logger.debug(f"Package {package_name} not found on PyPI")
        else:
            logger.warning(f"HTTP error fetching PyPI info for {package_name}: {e.code}")
        return None
    
    except URLError as e:
        logger.warning(f"Network error fetching PyPI info for {package_name}: {e}")
        return None
    
    except Exception as e:
        logger.warning(f"Error fetching PyPI info for {package_name}: {e}")
        return None


def get_pypi_project_urls(package_name: str) -> dict:
    """
    Get project URLs for a package from PyPI.
    
    Args:
        package_name: Name of the package
    
    Returns:
        Dictionary of project URLs (homepage, repository, documentation, etc.)
    """
    try:
        url = PYPI_API_URL.format(package=package_name)
        request = Request(url, headers={"User-Agent": "about-box-scanner/0.1.0"})
        
        with urlopen(request, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        info = data.get("info", {})
        project_urls = info.get("project_urls", {})
        
        # Add home_page if available
        if info.get("home_page"):
            project_urls["Homepage"] = info["home_page"]
        
        return project_urls
    
    except Exception as e:
        logger.debug(f"Could not fetch project URLs for {package_name}: {e}")
        return {}
