# POLY PMNA PDF Files

This public repository is dedicated to PDF study-note distribution for the [POLY PMNA website](https://polypmna.dpdns.org/).

It has two distinct archives: generated POLY PMNA lesson PDFs under `notes/` and
officially sourced SITTTR documents under `sitttr/`. Revision manifests provide
the machine-readable metadata used to verify and consume both collections.

## Technology stack

- Static PDF and JSON assets served from GitHub's raw-content endpoint
- Python 3 maintenance, discovery, download, and manifest-validation scripts
- GitHub Actions for the repository's current SLSA provenance experiment

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

Published PDFs must not be overwritten silently when a versioned document needs to be retained. Use a new version directory such as `v2`, then update the relevant manifest entry and website resolver policy. The publisher must allocate a new version directory whenever a published document changes; it must never replace an existing version in place.

## Download URLs

The public URL for a file in the default branch is:

```text
https://raw.githubusercontent.com/nandurpm/poly-pmna-pdf-files/main/notes/<revision>/<subject-code>/v1/<subject-code>.pdf
```

The POLY PMNA website consumes the manifest rather than constructing filenames from display titles. If an exact published entry is unavailable, the website keeps its existing HTML print-to-PDF fallback.

## Official Sources

### SITTTR (State Institute of Technical Teachers' Training & Research, Kalamassery)

**Primary official source** for diploma syllabus and model question papers.

| Resource | URL |
| --- | --- |
| SITTTR Official Website | https://sitttrkerala.ac.in/ |
| SITTTR Academic / Courses | https://sitttrkerala.ac.in/index.php?r=site/home |
| Diploma Syllabus – Revision 2015 | https://www.sitttrkerala.ac.in/index.php?r=site%2Fdiploma-syllabus&scheme=REV2015 |
| Diploma Syllabus – Revision 2021 | https://www.sitttrkerala.ac.in/index.php?r=site%2Fdiploma-syllabus&scheme=REV2021 |
| Model Question Papers – Revision 2015 | https://sitttrkerala.ac.in/index.php?r=site%2Fdiploma-modelqp&scheme=REV2015 |
| Model Question Papers – Revision 2021 | https://sitttrkerala.ac.in/index.php?r=site%2Fdiploma-modelqp&scheme=REV2021 |
| Revision 2021 Handbook | https://sitttrkerala.ac.in/syllabus/rev2021/handbook-rev2021.pdf |
| Revision 2021 Rules | https://sitttrkerala.ac.in/syllabus/rev2021/rules-rev2021.pdf |

**Revision 2026:** Navigate through the current official SITTTR site to locate dedicated Revision 2026 syllabus/programme pages. Do not assume Revision 2026 has the same structure as Revision 2021.

### Source-of-Truth Policy

For every missing document, follow this order:

1. POLY PMNA existing repository
2. Official SITTTR
3. Official Government / DTE Kerala source
4. Other authoritative educational source
5. Mark as MISSING if no trustworthy source exists

**Never skip the SITTTR check** for diploma syllabus and model question papers.

## Automation

The main `nandurpm/diploma-notes` repository renders changed lesson pages with Chromium, validates the resulting PDFs, commits them to the canonical paths in this repository, and updates the manifests. The cross-repository write requires the `PDF_ARCHIVE_REPO_TOKEN` Actions secret in `diploma-notes`.

The current archive contains Revision 2021 and Revision 2026 lesson PDFs generated from the corresponding HTML lesson pages.

## Project structure

| Path | Responsibility |
| --- | --- |
| `notes/` | Versioned POLY PMNA lesson PDFs grouped by curriculum revision and subject code. |
| `sitttr/` | Mirrored official SITTTR syllabus, handbook, rule, and model-question-paper documents. |
| `manifests/` | JSON inventories containing canonical URLs, checksums, sizes, page counts, and publication state. |
| Root Python scripts | One-off and repeatable archive discovery, scraping, gap analysis, reorganization, retry, and validation tools. |
| `.github/workflows/` | Release-triggered supply-chain provenance experiment. |

## Installation

There is no application dependency installation step. A complete checkout needs
Git LFS only if the repository later adopts LFS; the current archive consists of
ordinary Git objects. Python 3.10 or newer is recommended for running the
maintenance scripts. Individual network-facing scripts may require `requests` or
`beautifulsoup4`; read their module documentation before use.

## Common commands

Run the local manifest consistency checks:

```bash
python3 test_manifests.py
```

List SITTTR records whose files are not present locally:

```bash
python3 list_missing_sitttr.py
```

The scraping and download utilities contact external sites and can create many
files. Review each script's options and use a disposable branch before running it.

## Testing

`test_manifests.py` validates manifest structure, checksums, byte counts, page
counts, revision fields, canonical URLs, and the expected archive paths. It must
be run from a complete checkout because sparse clones that omit PDFs cannot
perform file-level verification.

## Documentation map

- [`notes/README.md`](notes/README.md) — generated lesson archive layout and publication rules
- [`sitttr/README.md`](sitttr/README.md) — official-source archive, verification, and attribution rules
- [`manifests/README.md`](manifests/README.md) — manifest schemas and status conventions
- [`.github/README.md`](.github/README.md) — repository automation configuration

## Contributing

Keep PDFs at their canonical versioned paths, update the corresponding manifest
in the same change, and run the manifest validator before proposing a merge.
Never commit credentials, local staging directories, or unverified third-party
documents. Archive additions should retain their authoritative source URL and
checksum so future maintainers can reproduce the verification.
