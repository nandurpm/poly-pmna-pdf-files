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

## Automation and uploads

See [Upload once, use on both websites](docs/upload-and-sync.md) for the upload layout, automatic indexing, consumer synchronization, legacy preservation and verification steps.

A single [Index PDFs and notify consumers](.github/workflows/notify-pdf-consumers.yml) workflow publishes the catalog and sends both consumers the resulting archive commit. Both sites expose the shared catalog through their All PDFs page and resolve published lesson URLs from the versioned manifests.

