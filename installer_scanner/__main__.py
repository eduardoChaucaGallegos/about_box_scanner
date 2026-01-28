"""
Main entry point for running the installer scanner as a module.

Allows running: python -m installer_scanner
"""

from .cli import main

if __name__ == "__main__":
    main()
