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

## Automation

The main `nandurpm/diploma-notes` repository renders changed lesson pages with Chromium, validates the resulting PDFs, commits them to the canonical paths in this repository, and updates the manifests. The cross-repository write requires the `PDF_ARCHIVE_REPO_TOKEN` Actions secret in `diploma-notes`.

Archive changes flow in the other direction through [the consumer notification workflow](.github/workflows/notify-consumers.yml). A push to `notes/`, `manifests/`, or `sitttr/` on `main` sends a `pdf-archive-updated` repository-dispatch event to both `nandurpm/diploma-notes` and `nandurpm/polypmna`. The payload identifies the exact archive commit and manifest base URL, so consumers can invalidate caches, refresh derived indexes, or run their own integrity checks without copying these generated PDFs into another repository.

Configure an Actions secret named `CROSS_REPO_SYNC_TOKEN` in this repository. It must be a fine-grained token with access only to the two consumer repositories and permission to dispatch repository events (fine-grained **Contents: write**). Do not store the token in this repository. Each consumer must handle the following event in its own workflow:

```yaml
on:
  repository_dispatch:
    types: [pdf-archive-updated]
```

The contract is deliberately one-way for archive updates: `diploma-notes` publishes validated PDFs here, and this repository notifies both consumers after the canonical files change. `polypmna` and `diploma-notes` should continue resolving published files from the supplied manifests rather than maintaining divergent PDF copies. A notification failure makes the workflow fail visibly instead of silently claiming that consumers were updated.

The current archive contains Revision 2021 and Revision 2026 lesson PDFs generated from the corresponding HTML lesson pages.


## Consumer synchronization

`poly-pmna-pdf-files` is the canonical binary and manifest repository for the POLY PMNA ecosystem. The `notify-pdf-consumers.yml` workflow watches `notes/` and `manifests/` and dispatches a `pdf-archive-updated` event to `diploma-notes` and `polypmna` after each relevant change.

Add a fine-grained GitHub token as the `PDF_CONSUMERS_TOKEN` Actions secret in this repository. The token must be allowed to dispatch workflows or repository events in both consumer repositories. The token is used only by the workflow and must never be committed.

The consumer workflows refresh `docs/pdf-archive-sync.json`. They do not duplicate PDF binaries: both sites continue to use the canonical raw URLs, so a published file or manifest update is reflected from the archive repository without creating competing copies.
