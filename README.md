# About Box Scanner

A Python tool to scan repositories and generate inventories of third-party components for ShotGrid Desktop license review processes.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Scan a repository and generate a third-party inventory:

```bash
python -m scanner --repo-path /path/to/repo --output inventory.json
```

### Options

- `--repo-path`: Path to the repository to scan (required)
- `--output`: Path to output JSON file (default: `third_party_inventory.json`)
- `--verbose`, `-v`: Enable verbose logging
- `--no-toolkit-mode`: Disable Toolkit-specific patterns (uses generic scanning only)
- `--no-license-extraction`: Skip extracting license information from detected components
- `--no-pypi`: Skip fetching package metadata from PyPI

## Output Format

The tool generates a JSON file with these main sections:

- **software_credits**: Info about the `software_credits` file (exists, line count, etc.)
- **dependencies**: Python packages from requirements.txt, pyproject.toml, setup.py
  - **NEW**: Includes `license_info` with detected license type and copyright
  - **NEW**: Includes `pypi_info` with package metadata from PyPI
- **frozen_requirements_files**: List of `frozen_requirements.txt` files found
- **vendored_candidates**: Directories and files that appear to be vendored third-party code
  - Includes `is_toolkit_pattern` flag for Toolkit-specific patterns
  - **NEW**: Includes `license_info` extracted from LICENSE files
- **asset_candidates**: Static assets (fonts, JS, CSS) that may be third-party

## Examples

```bash
# Scan tk-core repository
python -m scanner --repo-path ~/repos/tk-core --output tk-core-inventory.json

# Scan with verbose output
python -m scanner --repo-path ~/repos/tk-desktop --output tk-desktop-inventory.json -v
```

## Toolkit Mode (Default)

By default, the scanner runs in **Toolkit mode**, which applies ShotGrid Toolkit-specific patterns from the wiki:

- Detects common Toolkit vendored paths: `shotgun_api3/lib`, `python/vendors/`, `tests/python/third_party/`
- Finds `frozen_requirements.txt` files (used for Snyk security audits)
- Detects root-level `.zip` files (e.g., in `adobe/` directory)
- Searches for nested `requirements.txt` files in Toolkit resource patterns
- Checks for `software_credits` file in the repo root

To disable Toolkit mode and use generic scanning only:

```bash
python -m scanner --repo-path /path/to/repo --no-toolkit-mode
```

## Additional Tools

### Compare with software_credits

Compare detected TPCs with existing `software_credits` file:

```bash
python -m tools.compare_software_credits \
    --inventory inventory.json \
    --repo-path /path/to/repo \
    --output-report diff-report.json
```

This generates a diff report showing:
- TPCs in repo but not documented
- TPCs documented but not in repo
- Version mismatches
- Correctly documented TPCs

## Extending

The scanner is modular and can be extended with additional detectors:

- Add new dependency file parsers in `dependency_parser.py`
- Add new heuristics for vendored code in `vendored_detector.py`
- Add new asset types in `asset_detector.py`
- Extend Toolkit patterns in `utils.py` (TOOLKIT_THIRD_PARTY_PATHS)
- Improve fuzzy matching in `software_credits_comparer.py`