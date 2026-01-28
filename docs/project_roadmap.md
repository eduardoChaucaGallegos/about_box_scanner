# Project Roadmap - About Box Scanner

**Objective:** Automate and assist with the About Box and software_credits update process for ShotGrid Desktop

**Reference Document:** `docs/about_box_process.md`

---

## Current Status

- ✅ **Milestone 1: Enhanced Repo Scanner** - **COMPLETED**
- ✅ **Milestone 2: License & Copyright Extractor** - **COMPLETED**
- ✅ **Milestone 3: software_credits Parser & Generator** - **COMPLETED**
- ✅ **Milestone 4: Installation Folder Scanner** - **COMPLETED**
- ⏳ **Milestone 5: FY Comparison Tool** - Pending
- ✅ **Milestone 6: About Box Aggregator** - **COMPLETED**
- ⏳ **Milestone 7: PAOS/LeCorpio Assistant** - Optional

---

## Milestone 1: Enhanced Repo Scanner ✅ COMPLETED

### Process Mapping: Section B - Part 1

**Objective:** Improve git repo scanning to align with Toolkit-specific patterns

**Implemented:**
- ✅ Toolkit-specific vendored patterns
- ✅ `frozen_requirements.txt` detection
- ✅ `software_credits` detection
- ✅ Enhanced nested `requirements.txt` search
- ✅ Root-level `.zip` file detection
- ✅ Toolkit mode in CLI

**See:** `docs/milestone_1_summary.md` for complete details

---

## Milestone 2: License & Copyright Extractor ✅ COMPLETED

### Process Mapping: Section B - Step 2b

**Objective:** Extract license and copyright information from detected TPCs

**See:** `docs/milestone_2_summary.md` for complete details

### Inputs
- Inventory JSON from Milestone 1
- Paths to detected TPC directories/files

### Outputs
- Enriched JSON with:
  - LICENSE/COPYING/NOTICE file contents
  - Extracted copyright statements (regex)
  - Detected license type (MIT, Apache-2.0, BSD-3-Clause, GPL-2.0, LGPL-2.1, etc.)
  - PyPI links for Python packages (with version info)
  - GitHub/upstream links when possible
  - Extracted version information

### Helps With
- **Wiki Section B, Step 2b:** "Identify the license and copyright holder of the specific version"
- **Wiki - Font helper:** "open the font file on macOS (getInfo)"
- **Wiki - Python module helper:** 
  - "Check the LICENSE file from installed packages"
  - "Retrieve information from https://pypi.org/ entry"
  - "Provide link from github.com repository at the tag of the version"

### Key Functionalities
1. **License file reader**
   - Search for LICENSE, COPYING, NOTICE in vendored candidates
   - Extract full text
   - Identify multiple license files

2. **License type detector**
   - Text analysis with regex/patterns
   - Detect SPDX identifiers
   - Identify common licenses by content
   - Handle multiple license cases

3. **Copyright extractor**
   - Search for `Copyright (c) YYYY Name` lines
   - Extract years, holders
   - Handle various formats

4. **PyPI integration**
   - Query PyPI API for Python packages
   - Get metadata: license, homepage, version
   - Source repository links
   - Maintainer info

5. **Font metadata extractor**
   - Read TTF/OTF metadata (copyright, license)
   - Use library like `fontTools` if needed

### Limitations
- ⚠️ License detection is heuristic (humans must verify)
- ⚠️ Cannot determine PAOS vs. LeCorpio automatically (requires Leap page)
- ⚠️ Some licenses may be ambiguous or need legal interpretation

### Files to Create/Modify
- **New:** `scanner/license_extractor.py`
- **New:** `scanner/pypi_client.py`
- **New:** `scanner/font_metadata.py` (optional)
- **Modify:** `scanner/models.py` (add license fields)
- **Modify:** `scanner/core.py` (integrate extractor)

---

## Milestone 3: software_credits Parser & Generator ✅ COMPLETED

### Process Mapping: Section B - Step 2c and Step 3

**Objective:** Parse existing `software_credits` files and generate draft updates

**See:** `docs/milestone_3_summary.md` for complete details

### Inputs
- Enriched JSON from Milestone 2 (with license info)
- Existing `software_credits` file (if present)

### Outputs
- Parsed `software_credits` structure (JSON)
- **Diff report:**
  - TPCs in repo but NOT in `software_credits` ❌
  - TPCs in `software_credits` but NOT in repo ⚠️
  - TPCs with outdated copyright/license 🔄
  - Correct TPCs ✅
- **Draft updated `software_credits`:**
  - Plain text format
  - Grouped by component
  - Copyright + license for each TPC
  - Ready for human review

### Helps With
- **Wiki Section B, Step 2c:** "Is the TPC listed in the software_credit file?"
- **Wiki Section B, Step 3:** "Apply necessary changes to software_credits"
  - 3a: File exists but repo has no TPCs → placeholder
  - 3b: File doesn't exist and repo has TPCs → create file
  - 3c: Remove info unrelated to found TPCs
  - 3d: Update with correct info for each TPC

### Key Functionalities
1. **`software_credits` parser**
   - Read plain text file
   - Identify sections by component
   - Extract copyright, license, URLs

2. **Comparison engine**
   - Match detected TPCs with `software_credits` entries
   - Identify discrepancies
   - Detect outdated info

3. **Text generator**
   - Template for `software_credits` entries
   - Consistent formatting
   - Alphabetical order

4. **Visual diff report**
   - Git diff-like format
   - Highlight necessary changes
   - Suggest actions

### Limitations
- ⚠️ Only generates drafts; humans must review and approve
- ⚠️ Cannot verify legal approval status
- ⚠️ Parser may fail with non-standard `software_credits` formats

### Files to Create/Modify
- **Modify:** `scanner/software_credits_detector.py` (add full parser)
- **New:** `scanner/software_credits_generator.py`
- **New:** `scanner/diff_reporter.py`

---

## Milestone 4: Installation Folder Scanner ✅ COMPLETED

### Process Mapping: Section A

**Objective:** Scan SGD installation folder and list included components

**See:** `docs/milestone_4_summary.md` and `installer_scanner/README.md` for complete details

### Inputs
- Path to SGD installation folder (per OS)
- Optional: paths for Linux/macOS/Windows

### Outputs
- Inventory JSON with:
  - **Binaries/Software:**
    - Python (version)
    - Qt/PySide (version)
    - OpenSSL (version)
    - Included fonts
    - Other binaries
  - **Python Modules:**
    - Complete list with versions (`pip list`)
    - Installation locations
  - **Toolkit Components:**
    - tk-core, tk-desktop, tk-config-basic, etc.
    - Detected versions
  - **Merged cross-platform inventory**

### Helps With
- **Wiki Section A:** "Inspect the ShotGrid Desktop installation folder"
  - Step 1: "For each Linux/macOS/Windows... list all components"
  - Step 2: "Combine the 3 lists into a unique one in 2 categories"

### Key Functionalities
1. **Binary detector**
   - Search for executables (python, qt, openssl)
   - Extract versions from files or metadata

2. **Python module reader**
   - Execute `pip list` in SGD Python
   - Parse output for package + version

3. **Toolkit component detector**
   - Search for tk-* directories
   - Read info.yml or VERSION files

4. **Cross-platform merger**
   - Combine inventories from 3 OS
   - Mark OS-specific components
   - Create unified view

### Limitations
- ⚠️ Requires access to real SGD installations on all 3 OS
- ⚠️ Version detection may be heuristic for some binaries
- ⚠️ Requires permissions to execute commands in SGD environment

### Files to Create
- **New:** `installer_scanner/` (separate package)
  - `installer_scanner/cli.py`
  - `installer_scanner/binary_detector.py`
  - `installer_scanner/python_modules.py`
  - `installer_scanner/toolkit_detector.py`
  - `installer_scanner/merger.py`

---

## Milestone 5: FY Comparison Tool

### Process Mapping: Year-over-year comparison

**Objective:** Compare current FY inventory with previous FY

### Inputs
- Current FY inventory JSON (from Milestones 1-4)
- Previous FY inventory JSON

### Outputs
- **Diff report:**
  - ➕ Added TPCs (new this FY)
  - ➖ Removed TPCs
  - 🔄 Updated TPCs (version changes)
  - ✅ Unchanged TPCs
- **Confluence export:**
  - CSV/Excel format
  - Wiki markdown tables
  - Ready to copy/paste

### Helps With
- Identify what changed year-over-year
- Prioritize what needs new legal review
- Generate content for Confluence wiki pages

### Key Functionalities
1. **Diff engine**
   - Match components by name
   - Detect version changes
   - Identify additions/removals

2. **CSV/Excel exporter**
   - Columns: Component, Previous Version, New Version, Status, License
   - Excel-compatible for PAOS

3. **Wiki table generator**
   - Confluence markdown format
   - Colors/symbols for changes
   - Links to `software_credits`

### Limitations
- ⚠️ Matching logic may need adjustments for renamed components
- ⚠️ Doesn't auto-detect license changes (requires Milestone 2)

### Files to Create
- **New:** `tools/compare_fy.py` (CLI script)
- **New:** `scanner/differ.py`
- **New:** `scanner/exporters.py`

---

## Milestone 6: About Box Aggregator ✅ COMPLETED

### Process Mapping: Section C

**Objective:** Generate draft `license.html` for tk-desktop About Box

### Inputs
- Installation folder inventory (Milestone 4)
- All Toolkit component inventories (Milestones 1-3)
- Existing `license.html` template

### Outputs
- Draft `license.html` with:
  - Autodesk header
  - License blocks for binaries (Python, Qt, fonts, OpenSSL, etc.)
  - License blocks for Python modules (pywin32, PySide, etc.)
  - Links to `software_credits` files for all TK repos with TPCs
  - Structured HTML following template

### Helps With
- **Wiki Section C:** "ShotGrid Desktop About Box"
- Step 1d: "Update the license.html file accordingly"
- Step 2: "Create a PR and ask for review"

### Key Functionalities
1. **License aggregator**
   - Combine info from all inventories
   - Deduplicate components
   - Group by type (binaries, Python, etc.)

2. **HTML generator**
   - Use base template
   - Insert license blocks
   - Format copyright statements
   - Generate links to `software_credits`

3. **Validator**
   - Verify all TPCs are included
   - Verify valid HTML format
   - Warn about LGPL components (require source posting)

### Limitations
- ⚠️ Legal text must be verified by Legal partner
- ⚠️ LGPL source code posting requirements must be handled manually
- ⚠️ HTML template may need manual adjustments

### Files to Create
- **New:** `tools/generate_aboutbox.py` (CLI script)
- **New:** `scanner/aboutbox_generator.py`
- **New:** `templates/license.html.template`

---

## Milestone 7: PAOS/LeCorpio Assistant (Optional)

### Process Mapping: Legal Approval Sections

**Objective:** Generate CSV templates for PAOS records and draft LeCorpio request text

### Inputs
- Enriched inventories with license info (Milestone 2)

### Outputs
- **PAOS sheet template (Excel/CSV):**
  - Pre-filled with TPC data
  - Columns: Component, Version, License, Copyright, URL, etc.
- **LeCorpio request draft (text):**
  - Request format
  - Component information
  - Usage/integration
- **Approval checklist:**
  - What needs PAOS
  - What needs LeCorpio
  - Status of each component

### Helps With
- **Wiki:** "Fill in a PAOS record"
- **Wiki:** "Fill in a LeCorpio request"
- Accelerate legal approval process

### Key Functionalities
1. **PAOS vs. LeCorpio classifier**
   - List of known PAOS licenses
   - Suggest approval route

2. **PAOS template generator**
   - Excel/CSV with required fields
   - Pre-fill with inventory data

3. **LeCorpio text generator**
   - Request template
   - Fields replaced with component info

### Limitations
- ⚠️ Cannot automatically submit to OneDrive/LeCorpio (manual process)
- ⚠️ Cannot determine approval status
- ⚠️ Requires human review of PAOS vs. LeCorpio classification

### Files to Create
- **New:** `tools/generate_paos.py`
- **New:** `tools/generate_lecorpio.py`
- **New:** `templates/paos_template.csv`
- **New:** `templates/lecorpio_template.txt`

---

## Complete Workflow (When All Milestones Are Complete)

```
┌─────────────────────────────────────────────────────────────┐
│  FISCAL YEAR: About Box Update Process                      │
└─────────────────────────────────────────────────────────────┘

1. INSTALLATION SCAN (Section A)
   └─> python -m installer_scanner --sgd-path /path/to/SGD/
       → installation_inventory.json

2. TOOLKIT REPOS SCAN (Section B)
   ├─> python -m scanner --repo-path /path/to/tk-core
   ├─> python -m scanner --repo-path /path/to/tk-desktop
   ├─> python -m scanner --repo-path /path/to/tk-framework-X
   └─> ... (for each Toolkit component)
       → tk-core_inventory.json, tk-desktop_inventory.json, etc.

3. COMPARE WITH PREVIOUS FY
   └─> python -m tools.compare_fy --current inventories/ --previous fy25/
       → fy26_changes_report.csv (for Confluence)

4. UPDATE software_credits (Section B - Step 3)
   ├─> Review diff reports
   ├─> python -m tools.update_software_credits --repo tk-core --inventory tk-core_inventory.json
   │   → software_credits (draft)
   ├─> Human review ✍️
   └─> Create PR for each repo

5. LEGAL APPROVAL
   ├─> python -m tools.generate_paos --inventory all_inventories.json
   │   → paos_fy26.xlsx (upload to OneDrive)
   ├─> python -m tools.generate_lecorpio --component PySide2
   │   → lecorpio_draft.txt
   └─> Wait for Legal approval ⏳

6. GENERATE ABOUT BOX (Section C)
   └─> python -m tools.generate_aboutbox --installation installation_inventory.json --repos inventories/
       → license.html (draft for tk-desktop)
       → Legal review ✍️
       → Create PR for tk-desktop

7. RELEASE
   └─> New versions of Toolkit components
       └─> New version of ShotGrid Desktop
```

---

## Recommended Next Step

**👉 Implement Milestone 5: FY Comparison Tool**

This is the next logical step because:
1. Completes the core automation workflow
2. Enables automatic year-over-year change detection
3. Generates content for Confluence directly
4. Helps prioritize legal review work

---

*Last updated: January 27, 2026*
