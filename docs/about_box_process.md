# About Box and software_credits Update Process

Every year, or even twice a year if possible, our team needs to review all Third Party Components (TPC) used in our products.

A Third Party Component can be anything that we did not create, for example, a Font, code (compiled and not compiled), image, and so on. For this reason, this process is very hard to automate.

Third-party components must be approved through the Autodesk legal process first. This includes direct and indirect dependencies (i.e. dependencies of dependencies).

## Legal Approval Routes

There are two main routes to get a TPC approved by the Autodesk legal process:

- **For Pre-Approved Open Source (PAOS) licenses**: listing the component in the project's PAOS spreadsheet document
- **For non-PAOS licenses**: submitting a Lecorpio request and waiting for its approval

Which one to choose will depend on the type of component and how it is licensed. The Leap page should help guide your decision here.

Our Legal Partner can assist you with any questions you might have about the process. At the time of writing, @Tonya Holder is our Legal partner.

> **Important:** We might need to remove some TPC in the case where the license would not be approved.
>
> This is why it is important that developers and reviewers are aware of licensing issues when reviewing Pull Requests.

---

## A - Inspect the ShotGrid Desktop Installation Folder

The first step is to list what is included in ShotGrid Desktop for all 3 Operating Systems (Linux, macOS, Windows). Specifically, we are looking for:

- Third-Party Components (Python, Fonts, QT, Python modules, ...)
- Toolkit components (tk-core, tk-config-basic, python-api, ...)
  - Do not list the TPC from these components just yet. This will be done later.

> **Note:** We use the latest version of ShotGrid Desktop. However, when analyzing repositories, we use the master branch and not the specific version used in the ShotGrid Desktop installer.
>
> The reason for that if that, if any change needs to be done, it will require a new version of the component and ShotGrid Desktop. In other words, we can't fix the past here, only the future.

### Steps

1. **For each of the Linux/macOS/Windows**
   a. Install the latest version of ShotGrid Desktop
   b. Go to the installation folder and list all the components

2. **Combine the 3 lists into a unique one in 2 categories**
   - Binaries/Software
   - Python modules

### Example

Look at this page to see how this was done during FY24: **FY24 - ShotGrid Desktop - installation folder**.

---

## B - Toolkit Components and software_credit Files

Each Toolkit component has its equivalent Git repository. We need to look in each repository for Third Party Components.

In this context, a Third Party Component is any file/folder in the git repository that we add but did not create. In other words, what we copied from somewhere else.

**Repositories that have Third Party Components must have a file named `software_credits` in the root folder.** This file must contain the copyright holder and license of each TPC.

We only consider here the TK components shipped in the ShotGrid Desktop installer. The one we found in the previous section.

### Steps

**For each Toolkit Component:**

1. **Open every single file and identify whether or not it is owned by Autodesk**
   - Fonts, Images, Python modules, Windows binaries,...
   - Create a wiki page and list the TPC by alphabetical orders
   - Name, version, path in the git repo

2. **For each TPC:**
   
   a. Add a link to the upstream website
   
   b. Identify the license and copyright holder of the specific version
   - Helper for fonts: open the font file on macOS (getInfo)
   - Helper for Python modules:
     - Check the LICENSE file from the installed packages
     - Retrieve the information from https://pypi.org/ entry
     - Provide a link from the github.com repository at the tag of the version
   - Using the Leap page to identify whether to use PAOS or Lecorpio
   
   c. Is the TPC listed in the software_credit file?
   - If yes, is it the same copyright and license?
   - Store this information for later
   
   d. Obtain legal approval for this TPC (Leap page)
   - If the license is PAOS, create and fill a PAOS spreadsheet for the Toolkit component and add a line for this TPC
   - Otherwise, create a LeCorpio record and wait until it's approved by our legal partner
   - Checkout the LeCorpio section below for more information

3. **Apply the necessary changes to the software_credits**
   
   a. If the file exists but the repository does include any TPC, make sure the file only contains a small paragraph "This Toolkit component does not include any third_parties" (we want to avoid 404 dead links on older versions of SGD)
   
   b. If the file does not exist and the repository has TPCs, create the file
   
   c. Remove any information that is not related to TPC found earlier
   
   d. Update the file to make sure it contains up-to-date information about each TPC
   
   e. Create a PR with the changes and ask for a review

### Example

Create a wiki page (example: **FY24 - software-credits update**) to list all repositories and have a quick overview of:

- Repo name
- Has TPCs?
- Has software_credit file?
- Status: up-to-date/todo/done

### Python Packages

When the component bundles Python packages, the repositories must contain a `frozen_requirements.txt` file next to them detailing the versions of the bundled packages.

This allows security audit tools like Snyk to prompt us via the Security Dashboard when finding issues.

The purpose of the `frozen_requirements.txt` is to list all components, whereas a `requirements.txt` would just list the directly required components which then may install other dependencies.

To create/update a `frozen_requirements.txt` file, you can use `pip freeze`:

```bash
pip freeze --path third_party > third_party/frozen_requirements.txt
```

---

## C - ShotGrid Desktop About Box

The ShotGrid Desktop About box is an HTML file that is stored in tk-desktop.

Similarly to the software_credit, it must contain copyright holder information and license for each TPC. Not only about tk-desktop, but about the ShotGrid Desktop installer (combining all we have done so far). The file is structured of 4 sections:

- Autodesk header
- License blocks for binaries (Python, QT, Fonts, OpenSSL, ...)
- License blocks for Python modules (pywin32, PySide, ...)
- Links to software_credit file of all TK repositories that have TPCs

### About Box Guidelines

Here's what Jackie Cheng had to say about our about box:

> About box includes the language you had previously + a list of third party components' required attribution/notice. You can find the About box template for desktop on the leap page (https://engineering.autodesk.com/leap/). You can have an in-product notice/page that links to an ADSK webpage that has the full about box, as opposed to including the full text of the about box in-product. In terms of the 3rd party components to include, for this launch it is fine to just include the direct or top level 3rd party components. I checked internally and it seems like best practices is to include up to the second level, if possible. If possible, have as close as complete of an about box before launch of this app. And at the very least, please do have an about box in place.

### Steps

1. **For each binary and Python module:**

   a. Identify the license and copyright holder of the specific version
   - Helper for fonts: open the font file on macOS (getInfo)
   - Helper for Python modules:
     - Check the LICENSE file from the installed packages
     - Retrieve the information from https://pypi.org/ entry
     - Provide a link from the github.com repository at the tag of the version
   - Using the Leap page to identify whether to use PAOS or Lecorpio

   b. Obtain legal approval for this TPC (Leap page)
   - If the license is PAOS, create and fill a PAOS spreadsheet for the Toolkit component and add a line for this TPC
   - Otherwise, create a LeCorpio record and wait until it's approved by our legal partner
   - Checkout the LeCorpio section below for more information

   c. If the license is LGPL (e.g., PySide), you must make sure the TPC source code is submitted to the source code posting
   - If you have more than one component sharing the same 3rd party resource it is OK to list multiple components in the components field and have one record

   d. Update the license.html file accordingly

2. **Create a PR and ask for a review on the changes to license.html**
   - When the PR is merged a new tk-desktop version released, users will start receiving the update

### Example

Look at this page to see how this was done during FY24: **FY24 - licenses.html update**.

---

## Knowledge Base

Don't hesitate to look at this similar page from the ShotGrid team: **About Box**.

More information can also be found on the archived Slack channel of the FY24 update project: https://autodesk.enterprise.slack.com/archives/C05NB6GUSJV

---

## Filling in a PAOS Record

- Create and maintain a PAOS record at https://share.autodesk.com:/f:/r/sites/LegalTopicsToolkits/Component%20Records%20%20About%20Boxes/2021/Shotgun/Shotgun%20Desktop?csf=1&web=1&e=pBo4St

- If you need to submit a PAOS record you will need to upload a filled-in version of the template PAOS record that can also be found in the Leap page, to our designated OneDrive folder. At the time of writing, this was here, but it might be best to confirm with our legal partner first in case things have changed.

- **It's not always possible to find all of the required information for a PAOS record.**
  - If you can't find the copyright line or identify the author/year, try to provide a link to the website where the code is found. If you don't have any links, you could add that the copyright author is unknown. But please do make sure we have the information regarding the license governing that component.
  - If you are retroactively adding a record for a component that was added in the past, then you will need to look back through the Git history to find when the component was added and when it was released. In the rare case of that not being possible, add "unknown" for the component added and add the current release for the release date.

- **You must update a PAOS record if you update the 3rd party component or remove it.**

---

## Filling in a Lecorpio Request

Step-by-step instructions about LeCorpio process can be found on this page: [About Box and software_credits update process](About Box and software_credits update process).

- **You must create a new Lecorpio request each time you update the 3rd party component.**
- For Toolkit, we are submitting all the requests under the "Shotgun Toolkit" name and are not specifying a version.

- If a 3rd party component is used in multiple Toolkit components then as long as they are used in the same way and are exactly the same version, then we are treating this as one request. (At the time of writing we need to still check this is OK)

- PySide2 is marked down in the Lecorpio request as being a "Dynamically linked" component.
  - This is because we are compiling PySide2 (without change at the time of writing) and shipping it with the installer but it is not built into the executable and the Toolkit code dynamically imports this library at run time.

- You may want to check if a component is already covered or use an existing one as starting point.
  - To do this search "Shotgun" and that should show up all the requests relating to Shotgun. You can then clone an existing request if you want to use it as a starting point for a new request.

> **Before creating new records, please check passed record for the component.**
> The search functionality provides a way to search by product ("Shotgun - Toolkit").

---

## Other Useful Information

- Finding the license for a 3rd party component can sometimes be tricky. It can sometimes be included with the code itself or sometimes you can find it in the GitHub/public repository. If it is a Python repo you may be able to find it on PyPi though it is usually best to get it from the source if you can.

- Sometimes 3rd party components have multiple licenses. Mostly they do this to allow the consumer to pick the license that is most convenient to them. In this situation, you should aim to pick a license that is on our PAOS Licenses list. However sometimes the authors require you to accept all the licenses, you must check.

- We are only crediting the 3rd party components that we bundle with the Toolkit component or that we have derived our code from. If we are using a component via our code but are not actually bundling it, and are requiring it to be present on the user's system then we are not crediting it.

- For LGPL components (e.g., PySide), you can just cite the website that has the LGPL (ver) license terms. Here is an example: **LGPL Attribution Language.docx**

- For MIT licenses you can group all the copyrights for each component using MIT just above the MIT license: **MIT attribution sample.docx**

- There are no standards for how 3rd parties are packaged inside repos. You may have to look for:
  - `shotgun_api3/lib`
  - `desktopserver/resources/python/bin/requirements.txt`
  - `desktopserver/resources/python/source/requirements.txt`
  - `desktopclient/python/vendors`
  - `{tk-core,tk-framework-desktopserver,...}/tests/python/third_party`
  - `adobe/someZipFileAtTheRoot.zip`

---

## Common Third-Party Locations in Toolkit Repos

Based on the information above, here are common patterns for where third-party components are located:

| Location Pattern | Description |
|------------------|-------------|
| `vendor/`, `third_party/`, `externals/` | Explicit vendor directories |
| `*/lib/` | Library directories (e.g., `shotgun_api3/lib`) |
| `*/requirements.txt` | Python dependency files |
| `*/frozen_requirements.txt` | Frozen Python dependencies |
| `python/vendors/` | Python-specific vendor directories |
| `resources/python/*/requirements.txt` | Resource-embedded Python dependencies |
| `tests/python/third_party/` | Test-specific third-party code |
| Root-level `.zip` files | Compressed third-party packages |
| Font files (`.ttf`, `.otf`) | Custom fonts |
| `LICENSE*`, `COPYING`, `NOTICE` | License files in subdirectories |

---

*Last Updated: FY26 (January 2026)*
