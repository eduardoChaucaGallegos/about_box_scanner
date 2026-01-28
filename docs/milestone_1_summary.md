# Milestone 1: Enhanced Repo Scanner - Completed ✅

**Date:** January 27, 2026  
**Status:** Implemented and working

---

## Summary

We enhanced the repository scanner to specifically align with ShotGrid Toolkit patterns documented in `docs/about_box_process.md`. The scanner now applies Toolkit-specific heuristics by default.

---

## New Features Implemented

### 1. ✅ Toolkit Mode (Enabled by default)

The scanner now recognizes Toolkit-specific patterns:

**Detected Toolkit vendored paths:**
- `shotgun_api3/lib`
- `python/vendors/`
- `desktopclient/python/vendors`
- `desktopserver/resources/python/`
- `tests/python/third_party/`
- `adobe/` (for .zip files)

**Root-level .zip files:**
- Detects `.zip` files in repo root
- Detects `.zip` files in `adobe/` directory

### 2. ✅ `frozen_requirements.txt` Detection

The scanner now:
- Searches for `frozen_requirements.txt` files throughout the repo
- Lists them separately in the inventory
- Parses them to extract dependencies
- Documents their location for Snyk audits

### 3. ✅ `software_credits` Detection

New functionality to check the `software_credits` file:
- Detects if it exists in repo root
- Counts content lines
- Identifies if it's a placeholder ("no third parties")
- Reports status in inventory

### 4. ✅ Enhanced `requirements.txt` Search

The scanner now searches at multiple levels:
- `requirements.txt` (root)
- `*/requirements.txt` (level 1)
- `*/*/requirements.txt` (level 2)
- `*/*/*/requirements.txt` (level 3)

This captures Toolkit patterns like:
- `desktopserver/resources/python/bin/requirements.txt`
- `desktopserver/resources/python/source/requirements.txt`

### 5. ✅ Enhanced Data Models

**New class: `SoftwareCreditsInfo`**
```python
@dataclass
class SoftwareCreditsInfo:
    exists: bool
    path: Optional[str] = None
    is_empty: bool = False
    line_count: int = 0
```

**Enhanced class: `VendoredCandidate`**
- New field: `is_toolkit_pattern: bool`
- Identifies candidates matching Toolkit-specific patterns

**Enhanced class: `Inventory`**
- New field: `software_credits: Optional[SoftwareCreditsInfo]`
- New field: `frozen_requirements_files: List[str]`

### 6. ✅ Enhanced CLI

New command-line option:
```bash
--no-toolkit-mode    # Disables Toolkit-specific patterns
```

By default, Toolkit mode is **ENABLED**.

---

## Usage

### Standard Scan (Toolkit mode enabled)

```bash
python -m scanner --repo-path /path/to/tk-core --output tk-core-inventory.json
```

### Generic Scan (Toolkit mode disabled)

```bash
python -m scanner --repo-path /path/to/generic-repo --no-toolkit-mode --output generic-inventory.json
```

---

## Testing Results

### Test 1: tk-core

```bash
python -m scanner --repo-path ../tk-core --output tk-core-inventory.json
```

**Results:**
- ✅ Detected `shotgun_api3/lib` as vendored code (Toolkit pattern)
- ✅ Found `software_credits` file (35 lines)
- ✅ Detected 15 dependencies from `requirements.txt`
- ✅ Found 2 vendored candidates
- ✅ No `frozen_requirements.txt` (as expected for tk-core)

### Test 2: tk-framework-adobe

```bash
python -m scanner --repo-path ../tk-framework-adobe --output tk-framework-adobe-inventory.json
```

**Results:**
- ✅ Detected nested `frozen_requirements.txt` in `requirements/base/` and `requirements/cep/`
- ✅ Found `software_credits` file (245 lines)
- ✅ Detected zip files in `adobe/` directory
- ✅ Found multiple vendored paths including `cep/js/adobe`

### Test 3: tk-framework-desktopclient

```bash
python -m scanner --repo-path ../tk-framework-desktopclient --output tk-framework-desktopclient-inventory.json
```

**Results:**
- ✅ Found `software_credits` file
- ✅ No vendored code detected (expected)
- ✅ No `frozen_requirements.txt` (expected)

---

## Value Added to Process

This milestone automates the following manual tasks from the wiki:

### Wiki Section B - Part 1: "Open every single file and identify whether or not it is owned by Autodesk"

**Before:** Manual inspection of every file/folder
**Now:** Automated detection with Toolkit-specific heuristics

**Time Savings:** ~2-3 hours per repo → ~15 minutes

### Wiki Section B: Python Packages

**Before:** Manually search for `frozen_requirements.txt` files
**Now:** Automatic detection and parsing

**Time Savings:** ~30 minutes per repo → instant

### Wiki Section B - Step 2c: "Is the TPC listed in the software_credit file?"

**Before:** Manual check if file exists
**Now:** Automatic detection with line count and empty status

**Time Savings:** ~10 minutes per repo → instant

---

## Files Modified/Created

### Modified Files
- `scanner/utils.py` - Added `TOOLKIT_THIRD_PARTY_PATHS` and `TOOLKIT_ZIP_PATTERNS` constants
- `scanner/models.py` - Added `SoftwareCreditsInfo` dataclass, enhanced `VendoredCandidate` and `Inventory`
- `scanner/vendored_detector.py` - Added Toolkit pattern detection
- `scanner/dependency_parser.py` - Enhanced to find nested `requirements.txt` and `frozen_requirements.txt`
- `scanner/core.py` - Integrated `software_credits` detection
- `scanner/cli.py` - Added `--no-toolkit-mode` argument

### New Files
- `scanner/software_credits_detector.py` - New module for `software_credits` file detection

---

## Known Limitations

1. **Toolkit patterns are hardcoded:**
   - If new patterns emerge, `utils.py` needs to be updated
   - Consider making patterns configurable via YAML/JSON in future

2. **`frozen_requirements.txt` parsing is basic:**
   - Only extracts package names and versions
   - Doesn't validate against installed packages

3. **`software_credits` detection is shallow:**
   - Only checks if file exists and counts lines
   - Doesn't parse content structure (reserved for Milestone 3)

---

## Next Steps

**Milestone 2: License & Copyright Extractor**
- Extract license information from detected vendored code
- Parse license files (LICENSE, COPYING, NOTICE)
- Extract copyright statements
- Integrate with PyPI for package metadata

---

*Completed: January 27, 2026*
