# POLY PMNA PDF Files

This public repository is dedicated to PDF study-note distribution for the [POLY PMNA website](https://polypmna.dpdns.org/).

## Archive layout

PDF files are organized by curriculum revision, stable subject code, and version:

```text
notes/2021/<subject-code>/v1/<subject-code>.pdf
notes/2026/<subject-code>/v1/<subject-code>.pdf
```

The `manifests/` directory contains the subject title, revision, canonical Raw URL, byte size, page count, SHA-256 checksum, and publication status for each PDF.

## Source-of-truth policy

The visible `notes/` directory on the default branch is the single source of truth for direct PDF delivery. The website consumes the manifests and downloads the exact `pdfUrl` recorded for a published subject. GitHub Release assets are not required for operation and may be removed after the visible tree has been validated.

Every published file must be validated as a readable PDF and recorded in the checksum manifest. Upload credentials, private keys, local staging files, and backup bundles must never be committed.

## Versions and updates

Published PDFs must not be overwritten silently when a versioned document needs to be retained. Use a new version directory such as `v2`, then update the relevant manifest entry and website resolver policy. The current automated workflow uses `v1` for the generated archive and updates only the subject files affected by lesson HTML changes.

## Download URLs

The public URL for a file in the default branch is:

```text
https://raw.githubusercontent.com/nandurpm/poly-pmna-pdf-files/main/notes/<revision>/<subject-code>/v1/<subject-code>.pdf
```

The POLY PMNA website consumes the manifest rather than constructing filenames from display titles. If an exact published entry is unavailable, the website keeps its existing HTML print-to-PDF fallback.

## Automation

The main `nandurpm/diploma-notes` repository renders changed lesson pages with Chromium, validates the resulting PDFs, commits them to the canonical paths in this repository, and updates the manifests. The cross-repository write requires the `PDF_ARCHIVE_REPO_TOKEN` Actions secret in `diploma-notes`.

The current archive contains Revision 2021 and Revision 2026 lesson PDFs generated from the corresponding HTML lesson pages.
