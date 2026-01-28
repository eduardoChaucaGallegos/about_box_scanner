# Installation Scanner

Tool to scan ShotGrid Desktop installations and identify shipped components.

## Purpose

This tool helps with **Section A** of the About Box update process:
- Inspect SGD installation on Linux/macOS/Windows
- List binaries (Python, Qt, OpenSSL, etc.)
- List Python modules with versions
- Identify Toolkit components included
- Merge inventories from multiple platforms

## Installation

The installer_scanner is part of the about_box_scanner package:

```bash
cd about_box_scanner
pip install -r requirements.txt
```

## Usage

### Scan a Single Installation

```bash
python -m installer_scanner \
    --installation-path /path/to/SGD \
    --platform windows \
    --output sgd-windows.json
```

**Parameters:**
- `--installation-path`: Path to ShotGrid Desktop installation (required)
- `--platform`: Platform name (`windows`, `macos`, `linux`) - auto-detected if not specified
- `--output`: Output JSON file path (default: `installation_inventory.json`)
- `-v, --verbose`: Enable verbose logging

### Merge Multiple Platform Inventories

After scanning on each platform, merge the results:

```bash
python -m installer_scanner \
    --merge sgd-windows.json sgd-macos.json sgd-linux.json \
    --output sgd-merged.json
```

## Output Format

### Single Platform Inventory

```json
{
  "installation_path": "/path/to/SGD",
  "platform": "windows",
  "scanned_at": "2026-01-27T...",
  "binaries": [
    {
      "name": "Python",
      "path": "python/python.exe",
      "version": "3.10.11",
      "type": "interpreter"
    },
    {
      "name": "Qt",
      "version": "5.x",
      "type": "library"
    }
  ],
  "python_modules": [
    {
      "name": "requests",
      "version": "2.31.0",
      "location": "..."
    }
  ],
  "toolkit_components": [
    {
      "name": "tk-core",
      "path": "install/core",
      "version": "v0.20.10",
      "has_software_credits": true
    }
  ],
  "fonts": [
    "resources/fonts/OpenSans-Regular.ttf"
  ]
}
```

### Merged Inventory

```json
{
  "scanned_at": "2026-01-27T...",
  "platforms": ["windows", "macos", "linux"],
  "common_binaries": [
    {
      "name": "Python",
      "version": "3.10.11",
      "platforms": ["windows", "macos", "linux"]
    }
  ],
  "common_python_modules": [...],
  "common_toolkit_components": [...],
  "platform_specific": {
    "windows": {
      "binaries": [...],
      "python_modules": [...]
    }
  }
}
```

## Examples

### Windows Installation

```bash
# Typical Windows installation path
python -m installer_scanner \
    --installation-path "C:\Program Files\Shotgun\Shotgun Desktop" \
    --output sgd-windows.json
```

### macOS Installation

```bash
# Typical macOS installation path
python -m installer_scanner \
    --installation-path "/Applications/Shotgun.app/Contents" \
    --output sgd-macos.json
```

### Linux Installation

```bash
# Typical Linux installation path
python -m installer_scanner \
    --installation-path "/opt/Shotgun/Shotgun Desktop" \
    --output sgd-linux.json
```

### Merge All Three

```bash
python -m installer_scanner \
    --merge sgd-windows.json sgd-macos.json sgd-linux.json \
    --output sgd-merged-fy26.json
```

## Components Detected

### Binaries
- **Python**: Version from `python --version`
- **Qt**: Version from QtCore library files
- **OpenSSL**: Version from libssl/libcrypto files

### Python Modules
- Via `pip list --format=json` (preferred)
- Via site-packages scan (fallback)
- Includes name, version, location

### Toolkit Components
- All `tk-*` directories
- Version from `info.yml` or `VERSION` file
- Checks for `software_credits` file

### Fonts
- All `.ttf`, `.otf`, `.woff`, `.woff2` files

## Workflow

```
1. INSTALL SGD on each platform (Linux, macOS, Windows)

2. SCAN each installation
   ├─> Windows: python -m installer_scanner --installation-path "C:\..." --output win.json
   ├─> macOS:   python -m installer_scanner --installation-path "/Applications/..." --output mac.json
   └─> Linux:   python -m installer_scanner --installation-path "/opt/..." --output linux.json

3. MERGE results
   └─> python -m installer_scanner --merge win.json mac.json linux.json --output merged.json

4. REVIEW merged inventory
   └─> Identify components common to all platforms
       └─> Identify platform-specific components
```

## Notes

- Requires access to actual SGD installations
- Python detection requires executable permission
- Some version detection is heuristic
- Platform must be specified if running on different machine than installation

## Integration with Main Scanner

The installation scanner complements the repo scanner:

```bash
# 1. Scan installation
python -m installer_scanner --installation-path /path/to/SGD --output installation.json

# 2. Scan repos for each Toolkit component found
for component in tk-core tk-desktop tk-framework-*; do
    python -m scanner --repo-path /path/to/$component --output $component.json
done

# 3. Compare and generate About Box (future tools)
```

## Troubleshooting

### Python Not Detected
- Check if python.exe/python is in installation
- Try specifying full path to Python executable
- Check execute permissions

### No Python Modules Found
- Pip may not be available
- Site-packages directory may be in non-standard location
- Check verbose output for paths searched

### Toolkit Components Not Found
- tk-* directories may be in non-standard locations
- Check if SGD uses embedded/bundled Toolkit
- Review verbose output for search patterns

## See Also

- [Main Scanner README](../README.md)
- [About Box Process Documentation](../docs/about_box_process.md)
- [Milestone 4 Summary](../docs/milestone_4_summary.md)
